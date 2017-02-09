# Copyright 2016 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. All Rights Reserved.
#
# Portion of this code is Copyright Geoscience Australia, Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Django specific
from celery.decorators import task
from celery.signals import worker_process_init, worker_process_shutdown
from celery import group
from celery.task.control import revoke
from .models import Query, Result, Metadata

import numpy as np
import math
import xarray as xr
import collections
import gdal
import shutil
import sys
import osr
import os
import datetime
from collections import OrderedDict
from dateutil.tz import tzutc

from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import create_mosaic, create_median_mosaic, create_max_ndvi_mosaic, create_min_ndvi_mosaic
from utils.dc_utilities import get_spatial_ref, save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask, split_task
from utils.dc_fractional_coverage_classifier import frac_coverage_classify

from utils.dc_utilities import split_task, fill_nodata, min_value, max_value, generate_time_ranges

from data_cube_ui.utils import update_model_bounds_with_dataset, combine_metadata, map_ranges, cancel_task, error_with_message
from data_cube_ui.tasks import generate_chunk

"""
Class for handling loading celery workers to perform tasks asynchronously.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:

# constants up top for easy access/modification
base_result_path = '/datacube/ui_results/fractional_cover/'
base_temp_path = '/datacube/ui_results_temp/'

# Datacube instance to be initialized.
# A seperate DC instance is created for each worker.
dc = None

#default measurements. leaves out all qa bands.
measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']

#holds the different compositing algorithms. Most/least recent, max/min ndvi, median, etc.
# all options are required. setting None to a option will have the algo/task splitting
# process disregard it.
#experimentally optimized geo/time/slices_per_iter
processing_algorithms = {
    'most_recent': {
        'geo_chunk_size': 0.10,
        'time_chunks': None,
        'time_slices_per_iteration': 5,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': create_mosaic,
        'base_path': base_temp_path
    },
    'least_recent': {
        'geo_chunk_size': 0.10,
        'time_chunks': None,
        'time_slices_per_iteration': 1,
        'reverse_time': False,
        'chunk_combination_method': fill_nodata,
        'processing_method': create_mosaic,
        'base_path': base_temp_path
    },
    'max_ndvi': {
        'geo_chunk_size': 0.10,
        'time_chunks': None,
        'time_slices_per_iteration': 5,
        'reverse_time': False,
        'chunk_combination_method': max_value,
        'processing_method': create_max_ndvi_mosaic,
        'base_path': base_temp_path
    },
    'min_ndvi': {
        'geo_chunk_size': 0.10,
        'time_chunks': None,
        'time_slices_per_iteration': 5,
        'reverse_time': False,
        'chunk_combination_method': min_value,
        'processing_method': create_min_ndvi_mosaic,
        'base_path': base_temp_path
    },
    'median_pixel': {
        'geo_chunk_size': 0.01,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': False,
        'chunk_combination_method': fill_nodata,
        'processing_method': create_median_mosaic,
        'base_path': base_temp_path
    },
}

@task(name="fractional_cover_task")
def create_fractional_cover(query_id, user_id, single=False):
    """
    Creates metadata and result objects from a query id. gets the query, computes metadata for the
    parameters and saves the model. Uses the metadata to query the datacube for relevant data and
    creates the result. Results computed in single time slices for memory efficiency, pushed into a
    single numpy array containing the total result. this is then used to create png/tifs to populate
    a result model. Result model is constantly updated with progress and checked for task
    cancellation.

    Args:
        query_id (int): The ID of the query that will be created.
        user_id (string): The ID of the user that requested the query be made.

    Returns:
        Returns image url, data url for use only in tasks that reference this task.
    """

    print("Starting for query:" + query_id)
    # its fair to assume that the query_id will exist at this point, as if it wasn't it wouldn't
    # start the task.
    query = Query.objects.get(query_id=query_id, user_id=user_id)
    # if there is a matching query other than the one we're using now then do nothing.
    # the ui section has already grabbed the result from the db.
    if Result.objects.filter(query_id=query.query_id).exists():
        print("Repeat query, client will receive cached result.")
        return

    print("Got the query, creating metadata.")

    # creates the empty result.
    result = query.generate_result()

    if query.platform == "LANDSAT_ALL":
        error_with_message(result, "Combined products are not supported for fractional cover calculations.", base_temp_path)
        return

    product_details = dc.dc.list_products()[dc.dc.list_products().name == query.product]
    # wrapping this in a try/catch, as it will throw a few different errors
    # having to do with memory etc.
    try:
        # lists all acquisition dates for use in single tmeslice queries.
        acquisitions = dc.list_acquisition_dates(query.platform, query.product, time=(query.time_start, query.time_end), longitude=(
            query.longitude_min, query.longitude_max), latitude=(query.latitude_min, query.latitude_max))

        if len(acquisitions) < 1:
            error_with_message(result, "There were no acquisitions for this parameter set.", base_temp_path)
            return

        processing_options = processing_algorithms[query.compositor]
        #if its a single scene, load it all at once to prevent errors.
        if single:
            processing_options['time_chunks'] = None
            processing_options['time_slices_per_iteration'] = None

        # Reversed time = True will make it so most recent = First, oldest = Last.
        #default is in order from oldest -> newwest.
        lat_ranges, lon_ranges, time_ranges = split_task(resolution=product_details.resolution.values[0][1], latitude=(query.latitude_min, query.latitude_max), longitude=(
            query.longitude_min, query.longitude_max), acquisitions=acquisitions, geo_chunk_size=processing_options['geo_chunk_size'], time_chunks=processing_options['time_chunks'], reverse_time=processing_options['reverse_time'])

        result.total_scenes = len(time_ranges)
        # Iterates through the acquisition dates with the step in acquisitions_per_iteration.
        # Uses a time range computed with the index and index+acquisitions_per_iteration.
        # ensures that the start and end are both valid.
        print("Getting data and creating product")
        # create a temp folder that isn't on the nfs server so we can quickly
        # access/delete.
        if not os.path.exists(base_temp_path + query.query_id):
            os.mkdir(base_temp_path + query.query_id)
            os.chmod(base_temp_path + query.query_id, 0o777)

        # iterate over the time chunks.
        print("Time chunks: " + str(len(time_ranges)))
        print("Geo chunks: " + str(len(lat_ranges)))
        # create a group of geographic tasks for each time slice.
        time_chunk_tasks = [group(generate_fractional_cover_chunk.s(time_range_index, geographic_chunk_index, processing_options=processing_options, query=query, acquisition_list=time_ranges[time_range_index], lat_range=lat_ranges[
                                  geographic_chunk_index], lon_range=lon_ranges[geographic_chunk_index], measurements=measurements) for geographic_chunk_index in range(len(lat_ranges))).apply_async() for time_range_index in range(len(time_ranges))]

        # holds some acquisition based metadata. dict of objs keyed by date
        dataset_out_mosaic = None
        dataset_out_fractional_cover = None
        acquisition_metadata = {}
        for geographic_group in time_chunk_tasks:
            full_dataset = None
            tiles = []
            # get the geographic chunk data and drop all None values
            while not geographic_group.ready():
                result.refresh_from_db()
                if result.status == "CANCEL":
                    #revoke all tasks. Running tasks will continue to execute.
                    for task_group in time_chunk_tasks:
                        for child in task_group.children:
                            child.revoke()
                    cancel_task(query, result, base_temp_path)
                    return
            group_data = [data for data in geographic_group.get()
                          if data is not None]
            result.scenes_processed += 1
            result.save()
            print("Got results for a time slice, computing intermediate product..")
            acquisition_metadata = combine_metadata(acquisition_metadata, [tile[2] for tile in group_data])

            dataset_mosaic = xr.concat(reversed([xr.open_dataset(tile[0]) for tile in group_data]), dim='latitude').load()
            dataset_out_mosaic = processing_options['chunk_combination_method'](dataset_mosaic, dataset_out_mosaic)

            dataset_fractional_cover = xr.concat(reversed([xr.open_dataset(tile[1]) for tile in group_data]), dim='latitude').load()
            dataset_out_fractional_cover = processing_options['chunk_combination_method'](dataset_fractional_cover, dataset_out_fractional_cover)

        latitude = dataset_out_mosaic.latitude
        longitude = dataset_out_mosaic.longitude

        # grabs the resolution.
        geotransform = [longitude.values[0], product_details.resolution.values[0][1],
                        0.0, latitude.values[0], 0.0, product_details.resolution.values[0][0]]
        #hardcoded crs for now. This is not ideal. Should maybe store this in the db with product type?
        crs = str("EPSG:4326")

        # remove intermediates
        shutil.rmtree(base_temp_path + query.query_id)

        # populate metadata values.
        dates = list(acquisition_metadata.keys())
        dates.sort()

        meta = query.generate_metadata(
            scene_count=len(dates), pixel_count=len(latitude)*len(longitude))

        for date in reversed(dates):
            meta.acquisition_list += date.strftime("%m/%d/%Y") + ","
            meta.clean_pixels_per_acquisition += str(
                acquisition_metadata[date]['clean_pixels']) + ","
            meta.clean_pixel_percentages_per_acquisition += str(
                acquisition_metadata[date]['clean_pixels'] * 100 / meta.pixel_count) + ","

        # Count clean pixels and correct for the number of measurements.
        clean_pixels = np.sum(dataset_out_mosaic[measurements[0]].values != -9999)
        meta.clean_pixel_count = clean_pixels
        meta.percentage_clean_pixels = (meta.clean_pixel_count / meta.pixel_count) * 100
        meta.save()

        # generate all the results
        file_path = base_result_path + query_id
        tif_path = file_path + '.tif'
        netcdf_path = file_path + '.nc'
        mosaic_png_path = file_path + '_mosaic.png'
        fractional_cover_png_path = file_path + "_fractional_cover.png"

        print("Creating query results.")
        #Mosaic
        save_to_geotiff(tif_path, gdal.GDT_Int16, dataset_out_mosaic, geotransform, get_spatial_ref(crs),
                        x_pixels=dataset_out_mosaic.dims['longitude'], y_pixels=dataset_out_mosaic.dims['latitude'],
                        band_order=['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])
        # we've got the tif, now do the png. -> RGB
        bands = [3, 2, 1]
        create_rgb_png_from_tiff(tif_path, mosaic_png_path, png_filled_path=None, fill_color=None, bands=bands, scale=(0, 4096))

        #fractional_cover
        dataset_out_fractional_cover.to_netcdf(netcdf_path)
        save_to_geotiff(tif_path, gdal.GDT_Int32, dataset_out_fractional_cover, geotransform, get_spatial_ref(crs),
                        x_pixels=dataset_out_mosaic.dims['longitude'], y_pixels=dataset_out_mosaic.dims['latitude'],
                        band_order=['bs', 'pv', 'npv'])
        create_rgb_png_from_tiff(tif_path, fractional_cover_png_path, png_filled_path=None, fill_color=None, scale=None, bands=[1,2,3])

        # update the results and finish up.
        update_model_bounds_with_dataset([result, meta, query], dataset_out_mosaic)
        result.result_mosaic_path = mosaic_png_path
        result.result_path = fractional_cover_png_path
        result.data_path = tif_path
        result.data_netcdf_path = netcdf_path
        result.status = "OK"
        result.total_scenes = len(acquisitions)
        result.save()
        print("Finished processing results")
        # all data has been processed, create results and finish up.
        query.complete = True
        query.query_end = datetime.datetime.now()
        query.save()
    except:
        error_with_message(
            result, "There was an exception when handling this query.", base_temp_path)
        raise
    # end error wrapping.
    return

@task(name="generate_fractional_cover_chunk")
def generate_fractional_cover_chunk(time_num, chunk_num, processing_options=None, query=None, acquisition_list=None, lat_range=None, lon_range=None, measurements=None):
    """
    responsible for generating a piece of a fractional_cover product. This grabs the x/y area specified in the lat/lon ranges, gets all data
    from acquisition_list, which is a list of acquisition dates, and creates the fractional_cover using the function named in processing_options.
    saves the result to disk using time/chunk num, and returns the path and the acquisition date keyed metadata.
    """

    #if the path has been removed, the task is cancelled and this is only running due to the prefetch.
    if not os.path.exists(base_temp_path + query.query_id):
        return None

    time_index = 0
    iteration_data = None
    acquisition_metadata = {}
    print("Starting chunk: " + str(time_num) + " " + str(chunk_num))

    #dc.load doesn't support generators so do it this way.
    time_ranges = list(generate_time_ranges(acquisition_list, processing_options['reverse_time'], processing_options['time_slices_per_iteration']))

    # holds some acquisition based metadata.
    for time_index, time_range in enumerate(time_ranges):

        raw_data = dc.get_dataset_by_extent(query.product, product_type=None, platform=query.platform, time=time_range, longitude=lon_range, latitude=lat_range, measurements=measurements)

        if "cf_mask" not in raw_data:
            continue

        clear_mask = create_cfmask_clean_mask(raw_data.cf_mask)

        # update metadata. # here the clear mask has all the clean
        # pixels for each acquisition.
        for timeslice in range(clear_mask.shape[0]):
            time = raw_data.time.values[timeslice] if type(raw_data.time.values[timeslice]) == datetime.datetime else datetime.datetime.utcfromtimestamp(raw_data.time.values[timeslice].astype(int) * 1e-9)
            clean_pixels = np.sum(
                clear_mask[timeslice, :, :] == True)
            if time not in acquisition_metadata:
                acquisition_metadata[time] = {}
                acquisition_metadata[time]['clean_pixels'] = 0
            acquisition_metadata[time][
                'clean_pixels'] += clean_pixels

        iteration_data = processing_options['processing_method'](
            raw_data, clean_mask=clear_mask, intermediate_product=iteration_data, reverse_time=processing_options['reverse_time'])

    # Save this geographic chunk to disk.
    geo_path = base_temp_path + query.query_id + "/geo_chunk_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    fractional_cover_path = base_temp_path + query.query_id + "/geo_chunk_fractional_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    # if this is an empty chunk, just return an empty dataset.
    if iteration_data is None or not os.path.exists(base_temp_path + query.query_id):
        return None
    iteration_data.to_netcdf(geo_path)
    ##################################################################
    # Compute fractional cover here.
    clear_mask = create_cfmask_clean_mask(iteration_data.cf_mask)
    # mask out water manually. Necessary for frac. cover.
    clear_mask[iteration_data.cf_mask.values==1] = False
    fractional_cover = frac_coverage_classify(iteration_data, clean_mask=clear_mask)
    ##################################################################
    if not os.path.exists(base_temp_path + query.query_id):
        return None
    fractional_cover.to_netcdf(fractional_cover_path)
    print("Done with chunk: " + str(time_num) + " " + str(chunk_num))
    return [geo_path, fractional_cover_path, acquisition_metadata]

# Init/shutdown functions for handling dc instances.
# this is done to prevent synchronization/conflicts between workers when
# accessing DC resources.
@worker_process_init.connect
def init_worker(**kwargs):
    """
    Creates an instance of the DataAccessApi worker.
    """

    print("Creating DC instance for worker.")
    global dc
    dc = DataAccessApi()
    if not os.path.exists(base_result_path):
        os.mkdir(base_result_path)
        os.chmod(base_result_path, 0o777)


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """
    Deletes the instance of the DataAccessApi worker.
    """

    print('Closing DC instance for worker.')
    global dc
    dc = None
