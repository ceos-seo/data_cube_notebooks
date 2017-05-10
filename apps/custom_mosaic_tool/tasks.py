from django.db.models import F

import celery
from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_utilities import create_cfmask_clean_mask, write_geotiff_from_xr, write_png_from_xr, add_timestamp_data_to_xr
from utils.dc_chunker import create_geographic_chunks, create_time_chunks, combine_geographic_chunks
from datetime import datetime, timedelta
import shutil
from itertools import groupby
import xarray as xr
import numpy as np
import os
import imageio
from collections import OrderedDict

from .models import CustomMosaicTask
from apps.dc_algorithm.models import Satellite


@task(name="custom_mosaic_tool.run")
def run(task_id):
    """
    """
    chain(
        parse_parameters_from_task.s(task_id),
        validate_parameters.s(task_id), perform_task_chunking.s(task_id), start_chunk_processing.s(task_id))()
    return True


@task(name="custom_mosaic_tool.parse_parameters_from_task")
def parse_parameters_from_task(task_id):
    """
    """
    task = CustomMosaicTask.objects.get(pk=task_id)

    parameters = {
        'platforms': sorted(task.platform.split(",")),
        'time': (task.time_start, task.time_end),
        'longitude': (task.longitude_min, task.longitude_max),
        'latitude': (task.latitude_min, task.latitude_max),
        'measurements': task.measurements
    }

    parameters['products'] = [
        Satellite.objects.get(datacube_platform=platform).product_prefix + task.area_id
        for platform in parameters['platforms']
    ]

    task.execution_start = datetime.now()
    task.update_status("WAIT", "Parsed out parameters.")

    # Get other parameters here - compositor, result type, everything else.

    return parameters


@task(name="custom_mosaic_tool.validate_parameters")
def validate_parameters(parameters, task_id):
    """
    """
    task = CustomMosaicTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)

    #validate for any number of criteria here - num acquisitions, etc.
    acquisitions = dc.list_combined_acquisition_dates(**parameters)

    if len(acquisitions) < 1:
        task.update_status("ERROR", "There are no acquistions for this parameter set.")
        return None

    if task.animated_product != "none" and task.compositor.id == "median_pixel":
        task.update_status("ERROR", "Animations cannot be generated for median pixel operations.")
        return None

    task.update_status("WAIT", "Validated parameters.")

    try:
        dc.get_stacked_datasets_by_extent(dask_chunks={}, **parameters)
    except KeyError:
        parameters['measurements'] = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'pixel_qa']

    dc.close()
    return parameters


@task(name="custom_mosaic_tool.perform_task_chunking")
def perform_task_chunking(parameters, task_id):
    """

    """

    task = CustomMosaicTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)
    dates = dc.list_combined_acquisition_dates(**parameters)
    task_chunk_sizing = task.get_chunk_size()

    geographic_chunks = create_geographic_chunks(
        longitude=parameters['longitude'],
        latitude=parameters['latitude'],
        geographic_chunk_size=task_chunk_sizing['geographic'])

    time_chunks = create_time_chunks(
        dates, _reversed=task.get_reverse_time(), time_chunk_size=task_chunk_sizing['time'])
    print("Time chunks: {}, Geo chunks: {}".format(len(time_chunks), len(geographic_chunks)))

    dc.close()
    task.update_status("WAIT", "Chunked parameter set.")
    return {'parameters': parameters, 'geographic_chunks': geographic_chunks, 'time_chunks': time_chunks}


@task(name="custom_mosaic_tool.start_chunk_processing")
def start_chunk_processing(chunk_details, task_id):
    parameters = chunk_details.get('parameters')
    geographic_chunks = chunk_details.get('geographic_chunks')
    time_chunks = chunk_details.get('time_chunks')

    task = CustomMosaicTask.objects.get(pk=task_id)
    task.total_scenes = len(geographic_chunks) * len(time_chunks) * task.get_chunk_size()['time']
    task.scenes_processed = 0
    task.update_status("WAIT", "Starting processing.")

    print("START_CHUNK_PROCESSING")

    # create a group of groups that represent the processing pipeline
    # EITHER:
    # Create a group of groups of time chunks for each geographic chunk,
    # chained to combine time chunks (composites all time chunks over a single geo space) ->
    # -> combine over geo (combined over geo and time)
    # -> create output
    # OR
    # Create a group of groups of geographic chunks for each time chunk,
    # chained to combine geo chunks (composites all geo chunks over a single time space) ->
    # -> combine over time (combined over geo and time)
    # -> create output
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
    """from celery.contrib import rdb
    rdb.set_trace()
    full_pipeline = chord(processing_pipeline)(create_output_products.s(task_id=task_id))"""
    """processing_pipeline = (processing_task.s(
        task_id=task_id,
        geo_chunk_id=0,
        time_chunk_id=0,
        geographic_chunk=geographic_chunks[0],
        time_chunk=time_chunks[0],
        **parameters) | recombine_geographic_chunks.s(task_id=task_id) | recombine_time_chunks.s(task_id=task_id) |
                           create_output_products.s(task_id=task_id))
    print(processing_pipeline)
    print(processing_pipeline == processing_pipeline_base)
    processing_pipeline.apply_async()"""
    return True


@task(name="custom_mosaic_tool.processing_task")
def processing_task(task_id=None,
                    geo_chunk_id=None,
                    time_chunk_id=None,
                    geographic_chunk=None,
                    time_chunk=None,
                    **parameters):
    """
    """

    chunk_id = "_".join([str(geo_chunk_id), str(time_chunk_id)])
    task = CustomMosaicTask.objects.get(pk=task_id)

    print("Starting chunk: " + chunk_id)
    if not os.path.exists(task.get_temp_path()):
        return None

    iteration_data = None
    metadata = {}

    def _get_datetime_range_containing(*time_ranges):
        return (min(time_ranges), max(time_ranges))

    times = list(
        map(_get_datetime_range_containing, time_chunk)
        if task.get_iterative() else (_get_datetime_range_containing(time_chunk[0], time_chunk[-1])))
    dc = DataAccessApi(config=task.config_path)
    updated_params = parameters
    updated_params.update(geographic_chunk)
    #updated_params.update({'products': parameters['']})
    iteration_data = None
    base_index = task.get_chunk_size()['time'] * time_chunk_id
    for index, time in enumerate(times):
        updated_params.update({'time': time})
        data = dc.get_stacked_datasets_by_extent(**updated_params)
        if 'time' not in data:
            print("Invalid chunk.")
            continue

        clear_mask = create_cfmask_clean_mask(data.cf_mask) if 'cf_mask' in data else create_bit_mask(data.pixel_qa,
                                                                                                      [1, 2])
        add_timestamp_data_to_xr(data)

        for index, time in enumerate(data.time.values.astype('M8[ms]').tolist()):
            clean_pixels = np.sum(clear_mask[index, :, :] == True)
            if time not in metadata:
                metadata[time] = {}
                metadata[time]['clean_pixels'] = 0
                metadata[time]['satellite'] = parameters['platforms'][np.unique(data.satellite.isel(time=index).values)[
                    0]] if np.unique(data.satellite.isel(time=index).values)[0] > -1 else "NODATA"
            metadata[time]['clean_pixels'] += clean_pixels

        iteration_data = task.get_processing_method()(data, clean_mask=clear_mask, intermediate_product=iteration_data)

        if task.animated_product.id != "none":
            path = os.path.join(task.get_temp_path(),
                                "animation_{}_{}.nc".format(str(geo_chunk_id), str(base_index + index)))
            if task.animated_product.id == "scene":
                #need to clear out all the metadata..
                data.attrs = OrderedDict()
                for band in data:
                    data[band].attrs = OrderedDict()
                data.to_netcdf(path)
            elif task.animated_product.id == "cumulative":
                iteration_data.to_netcdf(path)

        task.scenes_processed = F('scenes_processed') + 1
        task.save()
    path = os.path.join(task.get_temp_path(), chunk_id + ".nc")
    iteration_data.to_netcdf(path)
    print("Done with chunk: " + chunk_id)
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_geographic_chunks")
def recombine_geographic_chunks(chunks, task_id=None):
    """
    """
    print("RECOMBINE_GEO")
    total_chunks = [chunks] if not isinstance(chunks, list) else chunks
    geo_chunk_id = total_chunks[0][2]['geo_chunk_id']
    time_chunk_id = total_chunks[0][2]['time_chunk_id']

    metadata = {}
    task = CustomMosaicTask.objects.get(pk=task_id)

    def combine_metadata(old, new):
        """
        """
        for key in new:
            if key in old:
                old[key]['clean_pixels'] += new[key]['clean_pixels']
                continue
            old[key] = new[key]
        return old

    chunk_data = []

    for index, chunk in enumerate(total_chunks):
        metadata = combine_metadata(metadata, chunk[1])
        chunk_data.append(xr.open_dataset(chunk[0]).load())
        #delete intermediate after loading.
        os.remove(chunk[0])

    combined_data = combine_geographic_chunks(chunk_data)

    # if we're animating, combine it all and save to disk.
    if task.animated_product.id != "none":
        base_index = task.get_chunk_size()['time'] * time_chunk_id
        for index in range(task.get_chunk_size()['time']):
            animated_data = []
            for chunk in total_chunks:
                geo_chunk_index = chunk[2]['geo_chunk_id']
                # if we're animating, combine it all and save to disk.
                path = os.path.join(task.get_temp_path(),
                                    "animation_{}_{}.nc".format(str(geo_chunk_index), str(base_index + index)))
                if os.path.exists(path):
                    animated_data.append(xr.open_dataset(path).load())
                    os.remove(path)
            path = os.path.join(task.get_temp_path(), "animation_{}.nc".format(base_index + index))
            if len(animated_data) > 0:
                combine_geographic_chunks(animated_data).to_netcdf(path)

    path = os.path.join(task.get_temp_path(), "recombined_geo_{}.nc".format(time_chunk_id))
    combined_data.to_netcdf(path)
    print("Done combining geographic chunks for time: " + str(time_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_time_chunks")
def recombine_time_chunks(chunks, task_id=None):
    """
    Geo indexes are the same, only the time index is different - sorting?
    """
    print("RECOMBINE_TIME")
    #sorting based on time id - earlier processed first as they're incremented e.g. 0, 1, 2..
    total_chunks = sorted(chunks, key=lambda x: x[0]) if isinstance(chunks, list) else [chunks]
    task = CustomMosaicTask.objects.get(pk=task_id)
    geo_chunk_id = total_chunks[0][2]['geo_chunk_id']
    time_chunk_id = total_chunks[0][2]['time_chunk_id']
    metadata = {}
    combined_data = None
    for index, chunk in enumerate(total_chunks):
        metadata.update(chunk[1])
        data = xr.open_dataset(chunk[0]).load()
        os.remove(chunk[0])
        if combined_data is None:
            combined_data = data
            continue
        #give time an indice to keep mosaicking from breaking.
        data['time'] = [0]
        clear_mask = create_cfmask_clean_mask(data.cf_mask) if 'cf_mask' in data else create_bit_mask(data.pixel_qa,
                                                                                                      [1, 2])
        combined_data = task.get_processing_method()(data, clean_mask=clear_mask, intermediate_product=combined_data)

        # if we're animating, combine it all and save to disk.
        if task.animated_product.id != "none":
            base_index = task.get_chunk_size()['time'] * index
            for index in range(task.get_chunk_size()['time']):
                path = os.path.join(task.get_temp_path(), "animation_{}.nc".format(base_index + index))
                if os.path.exists(path):
                    animated_data = xr.open_dataset(path).load()
                    if task.animated_product.id == "cumulative":
                        animated_data['time'] = [0]
                        clear_mask = create_cfmask_clean_mask(
                            animated_data.cf_mask) if 'cf_mask' in data else create_bit_mask(animated_data.pixel_qa,
                                                                                             [1, 2])
                        animated_data = task.get_processing_method()(animated_data,
                                                                     clean_mask=clear_mask,
                                                                     intermediate_product=combined_data)
                    path = os.path.join(task.get_temp_path(), "animation_{}.png".format(base_index + index))
                    write_png_from_xr(
                        path,
                        data,
                        bands=[task.query_type.red, task.query_type.green, task.query_type.blue],
                        png_filled_path=task.result_filled_path,
                        fill_color=task.query_type.fill,
                        scale=(0, 4096))

    path = os.path.join(task.get_temp_path(), "recombined_time_{}.nc".format(geo_chunk_id))
    combined_data.to_netcdf(path)
    print("Done combining time chunks for geo: " + str(geo_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.create_output_products")
def create_output_products(data, task_id=None):
    """
    """
    print("CREATE_OUTPUT")
    full_metadata = data[1]
    data = xr.open_dataset(data[0])
    task = CustomMosaicTask.objects.get(pk=task_id)

    task.result_path = os.path.join(task.get_result_path(), "png_mosaic.png")
    task.result_filled_path = os.path.join(task.get_result_path(), "filled_png_mosaic.png")
    task.data_path = os.path.join(task.get_result_path(), "data_tif.tif")
    task.data_netcdf_path = os.path.join(task.get_result_path(), "data_netcdf.nc")
    task.animation_path = os.path.join(task.get_result_path(), "animation.gif") if task.animated_product else ""
    task.metadata_from_dataset(data)
    task.metadata_from_dict(full_metadata)

    png_bands = [task.query_type.red, task.query_type.green, task.query_type.blue]

    write_geotiff_from_xr(
        task.data_path, data.astype('int32'), bands=['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask'])
    write_png_from_xr(
        task.result_path,
        data,
        bands=png_bands,
        png_filled_path=task.result_filled_path,
        fill_color=task.query_type.fill,
        scale=(0, 4096))

    if task.animated_product.id != "none":
        with imageio.get_writer(task.animation_path, mode='I', duration=1.0) as writer:
            valid_range = reversed(range(len(
                full_metadata))) if task.animated_product.id == "scene" and task.get_reverse_time() else range(
                    len(full_metadata))
            for index in valid_range:
                path = os.path.join(task.get_temp_path(), "animation_{}.nc".format(base_index + index))
                if os.path.exists(path):
                    image = imageio.imread(path=path)
                    writer.append_data(image)

    print("All products created.")
    task.complete = True
    task.execution_end = datetime.now()
    task.update_status("OK", "All products have been generated. Your result will be loaded on the map.")
    shutil.rmtree(task.get_temp_path())
    return True
