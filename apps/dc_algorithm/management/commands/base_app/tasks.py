from django.db.models import F

from celery.task import task
from celery import chain, group, chord
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
import shutil
import xarray as xr
import numpy as np
import os
import imageio
from collections import OrderedDict

from utils.data_cube_utilities.data_access_api import DataAccessApi
from utils.data_cube_utilities.dc_utilities import (create_cfmask_clean_mask, create_bit_mask, write_geotiff_from_xr,
                                                    write_png_from_xr, add_timestamp_data_to_xr, clear_attrs)
from utils.data_cube_utilities.dc_chunker import (create_geographic_chunks, create_time_chunks,
                                                  combine_geographic_chunks)
from apps.dc_algorithm.utils import create_2d_plot

from .models import AppNameTask
from apps.dc_algorithm.models import Satellite
from apps.dc_algorithm.tasks import DCAlgorithmBase

logger = get_task_logger(__name__)


class BaseTask(DCAlgorithmBase):
    # TODO: replace the __app__name var with app_name - avoids the auto rename.
    __app__name = 'app_name'


# TODO: If pixel drilling is enabled, uncomment this block and fill in the remaining TODOs
"""@task(name="app_name.pixel_drill", base=BaseTask)
def pixel_drill(task_id=None):
    parameters = parse_parameters_from_task(task_id=task_id)
    validate_parameters(parameters, task_id=task_id)
    task = AppNameTask.objects.get(pk=task_id)

    if task.status == "ERROR":
        return None

    dc = DataAccessApi(config=task.config_path)
    single_pixel = dc.get_stacked_datasets_by_extent(**parameters)
    clear_mask = task.satellite.get_clean_mask_func()(single_pixel.isel(latitude=0, longitude=0))
    single_pixel = single_pixel.where(single_pixel != task.satellite.no_data_value)

    dates = single_pixel.time.values
    if len(dates) < 2:
        task.update_status("ERROR", "There is only a single acquisition for your parameter set.")
        return None
    # TODO: This is an example of how this is normally done. Change it to do what this app does, just on a time
    # series of single pixels.
    wofs_data = task.get_processing_method()(single_pixel,
                                             clean_mask=clear_mask,
                                             enforce_float64=True,
                                             no_data=task.satellite.no_data_value)
    wofs_data = wofs_data.where(wofs_data != task.satellite.no_data_value).isel(latitude=0, longitude=0)

    # transpose flattens it into a 1xn array - TODO: add any bands in the first array that you want to.
    # data_labels, titles, style should all be the same length as datasets. Style refers to matplotlib styling.
    datasets = [wofs_data.wofs.values.transpose()] + [clear_mask]
    data_labels = ["Water/Non Water"] + ["Clear"]
    titles = ["Water/Non Water"] + ["Clear Mask"]
    style = ['.', '.']

    task.plot_path = os.path.join(task.get_result_path(), "plot_path.png")
    create_2d_plot(task.plot_path, dates=dates, datasets=datasets, data_labels=data_labels, titles=titles, style=style)

    task.complete = True
    task.update_status("OK", "Done processing pixel drill.")"""


@task(name="app_name.run", base=BaseTask)
def run(task_id=None):
    """Responsible for launching task processing using celery asynchronous processes

    Chains the parsing of parameters, validation, chunking, and the start to data processing.
    """
    chain(
        parse_parameters_from_task.s(task_id=task_id),
        validate_parameters.s(task_id=task_id),
        perform_task_chunking.s(task_id=task_id),
        start_chunk_processing.s(task_id=task_id))()
    return True


@task(name="app_name.parse_parameters_from_task", base=BaseTask)
def parse_parameters_from_task(task_id=None):
    """Parse out required DC parameters from the task model.

    See the DataAccessApi docstrings for more information.
    Parses out platforms, products, etc. to be used with DataAccessApi calls.

    If this is a multisensor app, platform and product should be pluralized and used
    with the get_stacked_datasets_by_extent call rather than the normal get.

    Returns:
        parameter dict with all keyword args required to load data.

    """
    task = AppNameTask.objects.get(pk=task_id)

    parameters = {
        # TODO: If this is not a multisensory app, uncomment 'platform' and remove 'platforms'
        # 'platform': task.satellite.datacube_platform,
        'platforms': task.satellite.get_platforms(),
        # TODO: If this is not a multisensory app, remove 'products' and uncomment the line below.
        # 'product': task.satellite.get_product(task.area_id),
        'products': task.satellite.get_products(task.area_id),
        'time': (task.time_start, task.time_end),
        'longitude': (task.longitude_min, task.longitude_max),
        'latitude': (task.latitude_min, task.latitude_max),
        'measurements': task.satellite.get_measurements()
    }

    task.execution_start = datetime.now()
    task.update_status("WAIT", "Parsed out parameters.")

    return parameters


@task(name="app_name.validate_parameters", base=BaseTask)
def validate_parameters(parameters, task_id=None):
    """Validate parameters generated by the parameter parsing task

    All validation should be done here - are there data restrictions?
    Combinations that aren't allowed? etc.

    Returns:
        parameter dict with all keyword args required to load data.
        -or-
        updates the task with ERROR and a message, returning None

    """
    task = AppNameTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)

    #validate for any number of criteria here - num acquisitions, etc.
    # TODO: if this is not a multisensory app, replace list_combined_acquisition_dates with list_acquisition_dates
    acquisitions = dc.list_combined_acquisition_dates(**parameters)

    # TODO: are there any additional validations that need to be done here?
    if len(acquisitions) < 1:
        task.complete = True
        task.update_status("ERROR", "There are no acquistions for this parameter set.")
        return None

    if task.animated_product.animation_id != "none" and not task.compositor.is_iterative():
        task.complete = True
        task.update_status("ERROR", "Animations cannot be generated for median pixel operations.")
        return None

    task.update_status("WAIT", "Validated parameters.")

    # TODO: Check that the measurements exist - replace ['products'][0] with ['products'] if this is not a multisensory app.
    if not dc.validate_measurements(parameters['products'][0], parameters['measurements']):
        task.complete = True
        task.update_status(
            "ERROR",
            "The provided Satellite model measurements aren't valid for the product. Please check the measurements listed in the {} model.".
            format(task.satellite.name))
        return None

    dc.close()
    return parameters


@task(name="app_name.perform_task_chunking", base=BaseTask)
def perform_task_chunking(parameters, task_id=None):
    """Chunk parameter sets into more manageable sizes

    Uses functions provided by the task model to create a group of
    parameter sets that make up the arg.

    Args:
        parameters: parameter stream containing all kwargs to load data

    Returns:
        parameters with a list of geographic and time ranges

    """

    if parameters is None:
        return None

    task = AppNameTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)
    # TODO: If this is not a multisensory app, replace list_combined_acquisition_dates with list_acquisition_dates
    dates = dc.list_combined_acquisition_dates(**parameters)
    task_chunk_sizing = task.get_chunk_size()

    geographic_chunks = create_geographic_chunks(
        longitude=parameters['longitude'],
        latitude=parameters['latitude'],
        geographic_chunk_size=task_chunk_sizing['geographic'])

    time_chunks = create_time_chunks(
        dates, _reversed=task.get_reverse_time(), time_chunk_size=task_chunk_sizing['time'])
    logger.info("Time chunks: {}, Geo chunks: {}".format(len(time_chunks), len(geographic_chunks)))

    dc.close()
    task.update_status("WAIT", "Chunked parameter set.")
    return {'parameters': parameters, 'geographic_chunks': geographic_chunks, 'time_chunks': time_chunks}


@task(name="app_name.start_chunk_processing", base=BaseTask)
def start_chunk_processing(chunk_details, task_id=None):
    """Create a fully asyncrhonous processing pipeline from paramters and a list of chunks.

    The most efficient way to do this is to create a group of time chunks for each geographic chunk,
    recombine over the time index, then combine geographic last.
    If we create an animation, this needs to be reversed - e.g. group of geographic for each time,
    recombine over geographic, then recombine time last.

    The full processing pipeline is completed, then the create_output_products task is triggered, completing the task.

    """

    if chunk_details is None:
        return None

    parameters = chunk_details.get('parameters')
    geographic_chunks = chunk_details.get('geographic_chunks')
    time_chunks = chunk_details.get('time_chunks')

    task = AppNameTask.objects.get(pk=task_id)
    task.total_scenes = len(geographic_chunks) * len(time_chunks) * (task.get_chunk_size()['time']
                                                                     if task.get_chunk_size()['time'] is not None else
                                                                     len(time_chunks[0]))
    task.scenes_processed = 0
    task.update_status("WAIT", "Starting processing.")

    logger.info("START_CHUNK_PROCESSING")

    processing_pipeline = group([
        group([
            processing_task.s(
                task_id=task_id,
                geo_chunk_id=geo_index,
                time_chunk_id=time_index,
                geographic_chunk=geographic_chunk,
                time_chunk=time_chunk,
                **parameters) for geo_index, geographic_chunk in enumerate(geographic_chunks)
        ]) | recombine_geographic_chunks.s(task_id=task_id) for time_index, time_chunk in enumerate(time_chunks)
    ]) | recombine_time_chunks.s(task_id=task_id)

    processing_pipeline = (processing_pipeline | create_output_products.s(task_id=task_id)).apply_async()
    return True


@task(name="app_name.processing_task", acks_late=True, base=BaseTask)
def processing_task(task_id=None,
                    geo_chunk_id=None,
                    time_chunk_id=None,
                    geographic_chunk=None,
                    time_chunk=None,
                    **parameters):
    """Process a parameter set and save the results to disk.

    Uses the geographic and time chunk id to identify output products.
    **params is updated with time and geographic ranges then used to load data.
    the task model holds the iterative property that signifies whether the algorithm
    is iterative or if all data needs to be loaded at once.

    Args:
        task_id, geo_chunk_id, time_chunk_id: identification for the main task and what chunk this is processing
        geographic_chunk: range of latitude and longitude to load - dict with keys latitude, longitude
        time_chunk: list of acquisition dates
        parameters: all required kwargs to load data.

    Returns:
        path to the output product, metadata dict, and a dict containing the geo/time ids
    """

    chunk_id = "_".join([str(geo_chunk_id), str(time_chunk_id)])
    task = AppNameTask.objects.get(pk=task_id)

    logger.info("Starting chunk: " + chunk_id)
    if not os.path.exists(task.get_temp_path()):
        return None

    iteration_data = None
    metadata = {}

    def _get_datetime_range_containing(*time_ranges):
        return (min(time_ranges) - timedelta(microseconds=1), max(time_ranges) + timedelta(microseconds=1))

    times = list(
        map(_get_datetime_range_containing, time_chunk)
        if task.get_iterative() else [_get_datetime_range_containing(time_chunk[0], time_chunk[-1])])
    dc = DataAccessApi(config=task.config_path)
    updated_params = parameters
    updated_params.update(geographic_chunk)
    #updated_params.update({'products': parameters['']})
    iteration_data = None
    base_index = (task.get_chunk_size()['time'] if task.get_chunk_size()['time'] is not None else 1) * time_chunk_id
    for time_index, time in enumerate(times):
        updated_params.update({'time': time})
        # TODO: If this is not a multisensory app replace get_stacked_datasets_by_extent with get_dataset_by_extent
        data = dc.get_stacked_datasets_by_extent(**updated_params)
        if data is None or 'time' not in data:
            logger.info("Invalid chunk.")
            continue

        # TODO: Replace anything here with your processing - do you need to create additional masks? Apply bandmaths? etc.
        clear_mask = task.satellite.get_clean_mask_func()(data)
        add_timestamp_data_to_xr(data)

        metadata = task.metadata_from_dataset(metadata, data, clear_mask, updated_params)

        # TODO: Make sure you're producing everything required for your algorithm.
        iteration_data = task.get_processing_method()(data,
                                                      clean_mask=clear_mask,
                                                      intermediate_product=iteration_data,
                                                      no_data=task.satellite.no_data_value,
                                                      reverse_time=task.get_reverse_time())

        # TODO: If there is no animation you can remove this block. Otherwise, save off the data that you need.
        if task.animated_product.animation_id != "none":
            path = os.path.join(task.get_temp_path(),
                                "animation_{}_{}.nc".format(str(geo_chunk_id), str(base_index + time_index)))
            if task.animated_product.animation_id == "scene":
                #need to clear out all the metadata..
                clear_attrs(data)
                #can't reindex on time - weird?
                data.isel(time=0).drop('time').to_netcdf(path)
            elif task.animated_product.animation_id == "cumulative":
                iteration_data.to_netcdf(path)

        task.scenes_processed = F('scenes_processed') + 1
        task.save()

    if iteration_data is None:
        return None

    path = os.path.join(task.get_temp_path(), chunk_id + ".nc")
    iteration_data.to_netcdf(path)
    dc.close()
    logger.info("Done with chunk: " + chunk_id)
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="app_name.recombine_geographic_chunks", base=BaseTask)
def recombine_geographic_chunks(chunks, task_id=None):
    """Recombine processed data over the geographic indices

    For each geographic chunk process spawned by the main task, open the resulting dataset
    and combine it into a single dataset. Combine metadata as well, writing to disk.

    Args:
        chunks: list of the return from the processing_task function - path, metadata, and {chunk ids}

    Returns:
        path to the output product, metadata dict, and a dict containing the geo/time ids
    """
    logger.info("RECOMBINE_GEO")
    total_chunks = [chunks] if not isinstance(chunks, list) else chunks
    total_chunks = [chunk for chunk in total_chunks if chunk is not None]
    geo_chunk_id = total_chunks[0][2]['geo_chunk_id']
    time_chunk_id = total_chunks[0][2]['time_chunk_id']

    metadata = {}
    task = AppNameTask.objects.get(pk=task_id)

    chunk_data = []

    for index, chunk in enumerate(total_chunks):
        metadata = task.combine_metadata(metadata, chunk[1])
        chunk_data.append(xr.open_dataset(chunk[0], autoclose=True))

    combined_data = combine_geographic_chunks(chunk_data)

    # if we're animating, combine it all and save to disk.
    # TODO: If there is no animation, delete this block. Otherwise, recombine all the geo chunks for each time chunk
    #       and save the result to disk.
    if task.animated_product.animation_id != "none":
        base_index = (task.get_chunk_size()['time'] if task.get_chunk_size()['time'] is not None else 1) * time_chunk_id
        for index in range((task.get_chunk_size()['time'] if task.get_chunk_size()['time'] is not None else 1)):
            animated_data = []
            for chunk in total_chunks:
                geo_chunk_index = chunk[2]['geo_chunk_id']
                # if we're animating, combine it all and save to disk.
                path = os.path.join(task.get_temp_path(),
                                    "animation_{}_{}.nc".format(str(geo_chunk_index), str(base_index + index)))
                if os.path.exists(path):
                    animated_data.append(xr.open_dataset(path, autoclose=True))
            path = os.path.join(task.get_temp_path(), "animation_{}.nc".format(base_index + index))
            if len(animated_data) > 0:
                combine_geographic_chunks(animated_data).to_netcdf(path)

    path = os.path.join(task.get_temp_path(), "recombined_geo_{}.nc".format(time_chunk_id))
    combined_data.to_netcdf(path)
    logger.info("Done combining geographic chunks for time: " + str(time_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="app_name.recombine_time_chunks", base=BaseTask)
def recombine_time_chunks(chunks, task_id=None):
    """Recombine processed chunks over the time index.

    Open time chunked processed datasets and recombine them using the same function
    that was used to process them. This assumes an iterative algorithm - if it is not, then it will
    simply return the data again.

    Args:
        chunks: list of the return from the processing_task function - path, metadata, and {chunk ids}

    Returns:
        path to the output product, metadata dict, and a dict containing the geo/time ids

    """
    logger.info("RECOMBINE_TIME")
    #sorting based on time id - earlier processed first as they're incremented e.g. 0, 1, 2..
    chunks = chunks if isinstance(chunks, list) else [chunks]
    chunks = [chunk for chunk in chunks if chunk is not None]
    total_chunks = sorted(chunks, key=lambda x: x[0]) if isinstance(chunks, list) else [chunks]
    task = AppNameTask.objects.get(pk=task_id)
    geo_chunk_id = total_chunks[0][2]['geo_chunk_id']
    time_chunk_id = total_chunks[0][2]['time_chunk_id']
    metadata = {}

    #TODO: If there is no animation, remove this block. Otherwise, compute the data needed to create each frame.
    def generate_animation(index, combined_data):
        base_index = (task.get_chunk_size()['time'] if task.get_chunk_size()['time'] is not None else 1) * index
        for index in range((task.get_chunk_size()['time'] if task.get_chunk_size()['time'] is not None else 1)):
            path = os.path.join(task.get_temp_path(), "animation_{}.nc".format(base_index + index))
            if os.path.exists(path):
                animated_data = xr.open_dataset(path, autoclose=True)
                if task.animated_product.animation_id == "cumulative":
                    animated_data = xr.concat([animated_data], 'time')
                    animated_data['time'] = [0]
                    clear_mask = task.satellite.get_clean_mask_func()(animated_data)
                    animated_data = task.get_processing_method()(animated_data,
                                                                 clean_mask=clear_mask,
                                                                 intermediate_product=combined_data,
                                                                 no_data=task.satellite.no_data_value,
                                                                 reverse_time=task.get_reverse_time())
                path = os.path.join(task.get_temp_path(), "animation_{}.png".format(base_index + index))
                write_png_from_xr(
                    path,
                    animated_data,
                    bands=[task.query_type.red, task.query_type.green, task.query_type.blue],
                    scale=task.satellite.get_scale(),
                    no_data=task.satellite.no_data_value)

    combined_data = None
    for index, chunk in enumerate(total_chunks):
        metadata.update(chunk[1])
        data = xr.open_dataset(chunk[0], autoclose=True)
        if combined_data is None:
            # TODO: If there is no animation, remove this.
            if task.animated_product.animation_id != "none":
                generate_animation(index, combined_data)
            combined_data = data
            continue
        #give time an indice to keep mosaicking from breaking.
        data = xr.concat([data], 'time')
        data['time'] = [0]
        clear_mask = task.satellite.get_clean_mask_func()(data)
        combined_data = task.get_processing_method()(data,
                                                     clean_mask=clear_mask,
                                                     intermediate_product=combined_data,
                                                     no_data=task.satellite.no_data_value,
                                                     reverse_time=task.get_reverse_time())
        # if we're animating, combine it all and save to disk.
        # TODO: If there is no animation, remove this.
        if task.animated_product.animation_id != "none":
            generate_animation(index, combined_data)

    path = os.path.join(task.get_temp_path(), "recombined_time_{}.nc".format(geo_chunk_id))
    combined_data.to_netcdf(path)
    logger.info("Done combining time chunks for geo: " + str(geo_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="app_name.create_output_products", base=BaseTask)
def create_output_products(data, task_id=None):
    """Create the final output products for this algorithm.

    Open the final dataset and metadata and generate all remaining metadata.
    Convert and write the dataset to variuos formats and register all values in the task model
    Update status and exit.

    Args:
        data: tuple in the format of processing_task function - path, metadata, and {chunk ids}

    """
    logger.info("CREATE_OUTPUT")
    full_metadata = data[1]
    dataset = xr.open_dataset(data[0], autoclose=True)
    task = AppNameTask.objects.get(pk=task_id)

    # TODO: Add any paths that you've added in your models.py Result model and remove the ones that aren't there.
    task.result_path = os.path.join(task.get_result_path(), "png_mosaic.png")
    task.result_filled_path = os.path.join(task.get_result_path(), "filled_png_mosaic.png")
    task.data_path = os.path.join(task.get_result_path(), "data_tif.tif")
    task.data_netcdf_path = os.path.join(task.get_result_path(), "data_netcdf.nc")
    task.animation_path = os.path.join(task.get_result_path(),
                                       "animation.gif") if task.animated_product.animation_id != 'none' else ""
    task.final_metadata_from_dataset(dataset)
    task.metadata_from_dict(full_metadata)

    # TODO: Set the bands that should be written to the final products
    bands = task.satellite.get_measurements() + []

    # TODO: If you're creating pngs, specify the RGB bands
    png_bands = [task.query_type.red, task.query_type.green, task.query_type.blue]

    dataset.to_netcdf(task.data_netcdf_path)
    write_geotiff_from_xr(task.data_path, dataset.astype('int32'), bands=bands, no_data=task.satellite.no_data_value)
    write_png_from_xr(
        task.result_path,
        dataset,
        bands=png_bands,
        png_filled_path=task.result_filled_path,
        fill_color=task.query_type.fill,
        scale=task.satellite.get_scale(),
        no_data=task.satellite.no_data_value)

    # TODO: if there is no animation, remove this. Otherwise, open each time iteration slice and write to disk.
    if task.animated_product.animation_id != "none":
        with imageio.get_writer(task.animation_path, mode='I', duration=1.0) as writer:
            valid_range = reversed(
                range(len(full_metadata))) if task.animated_product.animation_id == "scene" and task.get_reverse_time(
                ) else range(len(full_metadata))
            for index in valid_range:
                path = os.path.join(task.get_temp_path(), "animation_{}.png".format(index))
                if os.path.exists(path):
                    image = imageio.imread(path)
                    writer.append_data(image)

    # TODO: if you're capturing more tabular metadata, plot it here by converting these to lists.
    # an example of this is the current water detection app.
    dates = list(map(lambda x: datetime.strptime(x, "%m/%d/%Y"), task._get_field_as_list('acquisition_list')))
    if len(dates) > 1:
        task.plot_path = os.path.join(task.get_result_path(), "plot_path.png")
        create_2d_plot(
            task.plot_path,
            dates=dates,
            datasets=task._get_field_as_list('clean_pixel_percentages_per_acquisition'),
            data_labels="Clean Pixel Percentage (%)",
            titles="Clean Pixel Percentage Per Acquisition")

    logger.info("All products created.")
    # task.update_bounds_from_dataset(dataset)
    task.complete = True
    task.execution_end = datetime.now()
    task.update_status("OK", "All products have been generated. Your result will be loaded on the map.")
    shutil.rmtree(task.get_temp_path())
    return True
