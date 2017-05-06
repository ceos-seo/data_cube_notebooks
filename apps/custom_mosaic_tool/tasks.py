import celery
from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_utilities import create_cfmask_clean_mask
from utils.dc_chunker import create_geographic_chunks, create_time_chunks, combine_geographic_chunks

from .models import CustomMosaicTask
from datetime import datetime
import shutil
from itertools import groupby
import xarray as xr
import os
import rasterio


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
        'product': task.product,
        'platform': task.platform,
        'time': (task.time_start, task.time_end),
        'longitude': (task.longitude_min, task.longitude_max),
        'latitude': (task.latitude_min, task.latitude_max)
    }

    # Get other parameters here - compositor, result type, everything else.

    return parameters


@task(name="custom_mosaic_tool.validate_parameters")
def validate_parameters(parameters, task_id):
    """
    """
    task = CustomMosaicTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)

    #validate for any number of criteria here - num acquisitions, etc.
    acquisitions = dc.list_acquisition_dates(**parameters)
    if len(acquisitions) < 1:
        task.update_status("ERROR", "There are no acquistions for this parameter set.")
        return None

    dc.close()
    return parameters


@task(name="custom_mosaic_tool.perform_task_chunking")
def perform_task_chunking(parameters, task_id):
    """

    """

    task = CustomMosaicTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)
    dates = dc.list_acquisition_dates(**parameters)
    task_chunk_sizing = task.get_chunk_size()

    geographic_chunks = create_geographic_chunks(
        longitude=parameters['longitude'],
        latitude=parameters['latitude'],
        geographic_chunk_size=task_chunk_sizing['geographic'])

    time_chunks = create_time_chunks(
        dates, _reversed=task.get_reverse_time(), time_chunk_size=task_chunk_sizing['time'])

    print("Time chunks: {}, Geo chunks: {}".format(len(time_chunks), len(geographic_chunks)))

    dc.close()

    return {'parameters': parameters, 'geographic_chunks': geographic_chunks, 'time_chunks': time_chunks}


@task(name="custom_mosaic_tool.start_chunk_processing")
def start_chunk_processing(chunk_details, task_id):
    parameters = chunk_details.get('parameters')
    geographic_chunks = chunk_details.get('geographic_chunks')
    time_chunks = chunk_details.get('time_chunks')

    print("START_CHUNK_PROCESSING")

    #kick off processing-
    # create a group - time chunks, for each geographic chunk
    # chains to combine time chunks, which yields a single time slice chunk
    # this is then chorded to recombine geo chunks, creating result.

    processing_pipeline = [
        group([
            processing_task.s(
                task_id=task_id,
                geo_chunk_id=geo_index,
                time_chunk_id=time_index,
                geographic_chunk=geographic_chunk,
                time_chunk=time_chunk,
                **parameters) for time_index, time_chunk in enumerate(time_chunks)
        ]) | recombine_time_chunks.s(task_id=task_id) for geo_index, geographic_chunk in enumerate(geographic_chunks)
    ]

    full_pipeline = chord(processing_pipeline)(recombine_geographic_chunks.s(task_id=task_id))

    return True


"""
Processing pipeline definitions
"""


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
    iteration_data = None
    for time in times:
        updated_params.update({'time': time})
        data = dc.get_dataset_by_extent(**updated_params)
        if 'time' not in data:
            print("Invalid chunk.")
            continue
        clear_mask = create_cfmask_clean_mask(data.cf_mask)
        iteration_data = task.get_processing_method()(data, clean_mask=clear_mask, intermediate_product=iteration_data)
    path = os.path.join(task.get_temp_path(), chunk_id + ".nc")
    iteration_data.to_netcdf(path)
    print("Done with chunk: " + chunk_id)
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_time_chunks")
def recombine_time_chunks(chunks, task_id=None):
    """
    Geo indexes are the same, only the time index is different - sorting?
    """
    print("RECOMBINE_TIME")
    total_chunks = sorted(chunks, lambda x: x[0]) if isinstance(chunks, list) else [chunks]
    task = CustomMosaicTask.objects.get(pk=task_id)
    geo_chunk_id = total_chunks[0][2]['geo_chunk_id']
    time_chunk_id = total_chunks[0][2]['time_chunk_id']
    metadata = {}
    combined_data = None
    for chunk in total_chunks:
        data = xr.open_dataset(chunk[0])
        if combined_data is None:
            combined_data = data
            continue
        clear_mask = create_cfmask_clean_mask(data.cf_mask)
        combined_data = task.get_processing_method(data, clean_mask=clear_mask, intermediate_product=combined_data)

    path = os.path.join(task.get_temp_path(), str(geo_chunk_id) + ".nc")
    combined_data.to_netcdf(path)
    print("Done combining time chunk: " + str(time_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_geographic_chunks")
def recombine_geographic_chunks(chunks, task_id=None):
    """
    """
    print("RECOMBINE_GEO")
    total_chunks = [chunks] if not isinstance(chunks, list) else chunks
    chunk_data = []
    metadata = {}
    task = CustomMosaicTask.objects.get(pk=task_id)
    for chunk in total_chunks:
        print(chunk[0])
        chunk_data.append(xr.open_dataset(chunk[0]))

    combined_data = combine_geographic_chunks(chunk_data)

    path = os.path.join(task.get_result_path(), str(task.pk) + ".nc")
    combined_data.to_netcdf(path)
    create_output_products.delay([path, metadata], task_id=str(task_id))
    return path, metadata


@task(name="custom_mosaic_tool.create_output_products")
def create_output_products(data, task_id=None):
    """
    """
    print("CREATE_OUTPUT")
    full_metadata = data[1]
    data = xr.open_dataset(data[0])
    task = CustomMosaicTask.objects.get(pk=task_id)
    shutil.rmtree(task.get_temp_path())
    tif_path = os.path.join(task.get_result_path(), str(task.pk) + ".tif")
    write_geotiff_from_xr(
        tif_path, data.astype('int32'), bands=['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask'])
    print("All products created.")
    return tif_path


def write_geotiff_from_xr(tif_path, dataset, bands, nodata=-9999, crs="EPSG:4326"):
    """
    """
    with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=dataset.dims['latitude'],
            width=dataset.dims['longitude'],
            count=len(bands),
            dtype=str(dataset[bands[0]].dtype),
            crs=crs,
            transform=_get_transform_from_xr(dataset),
            nodata=nodata) as dst:
        for index, band in enumerate(bands):
            dst.write(dataset[band].values, index + 1)
        dst.close()
        print("Done writing")


def _get_transform_from_xr(dataset):
    """
    """

    from rasterio.transform import from_bounds
    geotransform = from_bounds(dataset.longitude[0], dataset.latitude[-1], dataset.longitude[-1], dataset.latitude[0],
                               len(dataset.longitude), len(dataset.latitude))
    return geotransform
