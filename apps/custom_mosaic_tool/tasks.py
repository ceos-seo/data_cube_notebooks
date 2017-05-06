from django.conf import settings

import celery
from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_chunker import create_geographic_chunks, create_time_chunks, combine_geographic_chunks
from utils.dc_mosaic import (create_mosaic, create_median_mosaic, create_max_ndvi_mosaic, create_min_ndvi_mosaic)
from utils.dc_utilities import (get_spatial_ref, save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask,
                                split_task, fill_nodata, max_value, min_value)

from .models import CustomMosaicTask

from datetime import datetime
import shutil
from itertools import groupby
import xarray as xr
import os
import rasterio


class Algorithm:
    """Base class for a Data Cube algorithm"""

    task_id = None
    config_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']
    result_dir = '/datacube/ui_results/custom_mosaic_tool'
    temp_dir = None
    iterative = True
    processing_method = create_mosaic

    def __init__(self, _id, iterative=True):
        self.task_id = str(_id)
        self.iterative = iterative
        self.temp_dir = os.path.join(self.result_dir, 'temp', self.task_id)
        self.result_dir = os.path.join(self.result_dir, self.task_id)
        try:
            os.makedirs(self.temp_dir)
            os.makedirs(self.result_dir)
        except OSError:
            pass

    def run(self):
        """
        """
        chain(
            parse_parameters_from_task.s(self),
            validate_parameters.s(self), perform_task_chunking.s(self), start_chunk_processing.s(self))()
        return True


@task(name="custom_mosaic_tool.parse_parameters_from_task")
def parse_parameters_from_task(algorithm):
    """
    """
    task = CustomMosaicTask.objects.get(pk=algorithm.task_id)

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
def validate_parameters(parameters, algorithm):
    """
    """

    dc = DataAccessApi(config=algorithm.config_path)
    task = CustomMosaicTask.objects.get(pk=algorithm.task_id)

    #validate for any number of criteria here - num acquisitions, etc.
    acquisitions = dc.list_acquisition_dates(**parameters)
    if len(acquisitions) < 1:
        task.update_status("ERROR", "There are no acquistions for this parameter set.")
        return None

    dc.close()
    return parameters


@task(name="custom_mosaic_tool.perform_task_chunking")
def perform_task_chunking(parameters, algorithm):
    """

    """

    dc = DataAccessApi(config=algorithm.config_path)
    dates = dc.list_acquisition_dates(**parameters)

    geographic_chunks = create_geographic_chunks(
        longitude=parameters['longitude'], latitude=parameters['latitude'], geographic_chunk_size=0.01)

    time_chunks = create_time_chunks(dates, _reversed=True)

    print("Time chunks: {}, Geo chunks: {}".format(len(time_chunks), len(geographic_chunks)))

    dc.close()

    return {'parameters': parameters, 'geographic_chunks': geographic_chunks, 'time_chunks': time_chunks}


@task(name="custom_mosaic_tool.start_chunk_processing")
def start_chunk_processing(chunk_details, algorithm):
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
                algorithm=algorithm,
                geo_chunk_id=geo_index,
                time_chunk_id=time_index,
                geographic_chunk=geographic_chunk,
                time_chunk=time_chunk,
                **parameters) for time_index, time_chunk in enumerate(time_chunks)
        ]) | recombine_time_chunks.s(algorithm=algorithm)
        for geo_index, geographic_chunk in enumerate(geographic_chunks)
    ]

    full_pipeline = chord(processing_pipeline)(recombine_geographic_chunks.s(algorithm=algorithm))

    return True


"""
Processing pipeline definitions
"""


@task(name="custom_mosaic_tool.processing_task")
def processing_task(algorithm=None,
                    geo_chunk_id=None,
                    time_chunk_id=None,
                    geographic_chunk=None,
                    time_chunk=None,
                    **parameters):
    """
    """

    chunk_id = "_".join([str(geo_chunk_id), str(time_chunk_id)])

    print("Starting chunk: " + chunk_id)
    if not os.path.exists(algorithm.temp_dir):
        return None

    iteration_data = None
    metadata = {}

    def _get_datetime_range_containing(*time_ranges):
        return (min(time_ranges), max(time_ranges))

    times = list(
        map(_get_datetime_range_containing, time_chunk)
        if algorithm.iterative else (_get_datetime_range_containing(time_chunk[0], time_chunk[-1])))

    dc = DataAccessApi(config=algorithm.config_path)
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
        iteration_data = create_mosaic(data, clean_mask=clear_mask, intermediate_product=iteration_data)
    path = os.path.join(algorithm.temp_dir, chunk_id + ".nc")
    iteration_data.to_netcdf(path)
    print("Done with chunk: " + chunk_id)
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_time_chunks")
def recombine_time_chunks(chunks, algorithm=None):
    """
    Geo indexes are the same, only the time index is different - sorting?
    """
    print("RECOMBINE_TIME")
    total_chunks = sorted(chunks, lambda x: x[0]) if isinstance(chunks, list) else [chunks]
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
        combined_data = create_mosaic(data, clean_mask=clear_mask, intermediate_product=combined_data)

    path = os.path.join(algorithm.temp_dir, str(geo_chunk_id) + ".nc")
    combined_data.to_netcdf(path)
    print("Done combining time chunk: " + str(time_chunk_id))
    return path, metadata, {'geo_chunk_id': geo_chunk_id, 'time_chunk_id': time_chunk_id}


@task(name="custom_mosaic_tool.recombine_geographic_chunks")
def recombine_geographic_chunks(chunks, algorithm=None):
    """
    """
    print("RECOMBINE_GEO")
    chunk_data = []
    metadata = {}
    for chunk in chunks:
        chunk_data.append(xr.open_dataset(chunk[0]))

    combined_data = combine_geographic_chunks(chunk_data)

    path = os.path.join(algorithm.result_dir, algorithm.task_id + ".nc")
    combined_data.to_netcdf(path)
    create_output_products.delay([path, metadata], algorithm=algorithm)
    return path, metadata


@task(name="custom_mosaic_tool.create_output_products")
def create_output_products(data, algorithm=None):
    """
    """
    print("CREATE_OUTPUT")
    full_metadata = data[1]
    data = xr.open_dataset(data[0])
    shutil.rmtree(algorithm.temp_dir)
    tif_path = os.path.join(algorithm.result_dir, algorithm.task_id + ".tif")
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
