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
from utils.dc_mosaic import create_mosaic
from utils.dc_utilities import get_spatial_ref, save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask, split_task, fill_nodata, generate_time_ranges
from utils.dc_baseline import generate_baseline
from utils.dc_demutils import create_slope_mask

from data_cube_ui.utils import update_model_bounds_with_dataset, map_ranges, combine_metadata, cancel_task, error_with_message
"""
Class for handling loading celery workers to perform tasks asynchronously.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:

# constants up top for easy access/modification
base_result_path = '/datacube/ui_results/slip/'
base_temp_path = '/datacube/ui_results_temp/'

# Datacube instance to be initialized.
# A seperate DC instance is created for each worker.
dc = None

#default measurements. leaves out all qa bands.
measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'cf_mask']

#holds the different compositing algorithms. Most/least recent, max/min ndvi, median, etc.
# all options are required. setting None to a option will have the algo/task splitting
# process disregard it.
#experimentally optimized geo/time/slices_per_iter
processing_algorithms = {
    'average': {
        'geo_chunk_size': 0.05,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': None
    },
    'composite': {
        'geo_chunk_size': 0.05,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': None
    }
}


@task(name="slip_task")
def create_slip(query_id, user_id, single=False):
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
        error_with_message(result, "Combined products are not supported for SLIP calculations.", base_temp_path)
        return

    product_details = dc.dc.list_products()[dc.dc.list_products().name == query.product]
    # wrapping this in a try/catch, as it will throw a few different errors
    # having to do with memory etc.
    try:
        # lists all acquisition dates for use in single tmeslice queries.
        acquisitions = dc.list_acquisition_dates(
            query.platform,
            query.product,
            time=(query.time_start, query.time_end),
            longitude=(query.longitude_min, query.longitude_max),
            latitude=(query.latitude_min, query.latitude_max))

        if len(acquisitions) < 1:
            error_with_message(result, "There were no acquisitions for this parameter set.", base_temp_path)
            return

        #if dems don't exist for the area, cancel.
        if dc.get_scene_metadata(
                'TERRA',
                'terra_aster_gdm_' + query.area_id,
                longitude=(query.longitude_min, query.longitude_max),
                latitude=(query.latitude_min, query.latitude_max))['scene_count'] == 0:
            error_with_message(result, "There is no elevation data for your parameter set.", base_temp_path)
            return
        #extend acquisitions list by the baseline length..
        acquisitions_extension = dc.list_acquisition_dates(
            query.platform,
            query.product,
            longitude=(query.longitude_min, query.longitude_max),
            latitude=(query.latitude_min, query.latitude_max))
        initial_acquisition = acquisitions_extension.index(
            acquisitions[0]) - query.baseline_length if acquisitions_extension.index(
                acquisitions[0]) - query.baseline_length > 0 else 0
        acquisitions = acquisitions_extension[initial_acquisition:acquisitions_extension.index(acquisitions[-1]) + 1]
        if len(acquisitions) < query.baseline_length + 1:
            error_with_message(
                result, "There are only " + str(len(acquisitions)) +
                " acquisitions for your parameter set. The acquisition count must be at least one greater than the baseline length.",
                base_temp_path)
            return

        processing_options = processing_algorithms[query.baseline]
        #if its a single scene, load it all at once to prevent errors.
        if single:
            processing_options['time_chunks'] = None
            processing_options['time_slices_per_iteration'] = None

        # Reversed time = True will make it so most recent = First, oldest = Last.
        #default is in order from oldest -> newwest.
        lat_ranges, lon_ranges, time_ranges = split_task(
            resolution=product_details.resolution.values[0][1],
            latitude=(query.latitude_min, query.latitude_max),
            longitude=(query.longitude_min, query.longitude_max),
            acquisitions=acquisitions,
            geo_chunk_size=processing_options['geo_chunk_size'],
            time_chunks=processing_options['time_chunks'],
            reverse_time=processing_options['reverse_time'])

        result.total_scenes = len(time_ranges)
        result.save()
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
        time_chunk_tasks = [
            group(
                generate_slip_chunk.s(
                    time_range_index,
                    geographic_chunk_index,
                    processing_options=processing_options,
                    query=query,
                    acquisition_list=time_ranges[time_range_index],
                    lat_range=lat_ranges[geographic_chunk_index],
                    lon_range=lon_ranges[geographic_chunk_index],
                    measurements=measurements) for geographic_chunk_index in range(len(lat_ranges))).apply_async()
            for time_range_index in range(len(time_ranges))
        ]

        # holds some acquisition based metadata. dict of objs keyed by date
        dataset_out_mosaic = None
        dataset_out_baseline_mosaic = None
        dataset_out_slip = None
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
            group_data = [data for data in geographic_group.get() if data is not None]
            result.scenes_processed += 1
            result.save()
            print("Got results for a time slice, computing intermediate product..")

            if len(group_data) < 1:
                time_range_index += 1
                continue

            acquisition_metadata = combine_metadata(acquisition_metadata, [tile[3] for tile in group_data])

            #create cf mosaic
            dataset_mosaic = xr.concat(
                reversed([xr.open_dataset(tile[0]) for tile in group_data]), dim='latitude').load()
            dataset_out_mosaic = processing_options['chunk_combination_method'](dataset_mosaic, dataset_out_mosaic)

            #now slip.
            dataset_slip = xr.concat(reversed([xr.open_dataset(tile[1]) for tile in group_data]), dim='latitude').load()
            dataset_out_slip = processing_options['chunk_combination_method'](dataset_slip, dataset_out_slip)

            #create baseline mosaic
            dataset_baseline_mosaic = xr.concat(
                reversed([xr.open_dataset(tile[2]) for tile in group_data]), dim='latitude').load()
            dataset_out_baseline_mosaic = processing_options['chunk_combination_method'](dataset_baseline_mosaic,
                                                                                         dataset_out_baseline_mosaic)

        latitude = dataset_out_mosaic.latitude
        longitude = dataset_out_mosaic.longitude

        # grabs the resolution.
        geotransform = [
            longitude.values[0], product_details.resolution.values[0][1], 0.0, latitude.values[0], 0.0,
            product_details.resolution.values[0][0]
        ]
        #hardcoded crs for now. This is not ideal. Should maybe store this in the db with product type?
        crs = str("EPSG:4326")

        # remove intermediates
        shutil.rmtree(base_temp_path + query.query_id)

        # populate metadata values.
        dates = list(acquisition_metadata.keys())
        dates.sort()

        meta = query.generate_metadata(scene_count=len(dates), pixel_count=len(latitude) * len(longitude))

        for date in reversed(dates):
            meta.acquisition_list += date.strftime("%m/%d/%Y") + ","
            meta.clean_pixels_per_acquisition += str(acquisition_metadata[date]['clean_pixels']) + ","
            meta.clean_pixel_percentages_per_acquisition += str(acquisition_metadata[date]['clean_pixels'] * 100 /
                                                                meta.pixel_count) + ","
            meta.slip_pixels_per_acquisition += str(acquisition_metadata[date]['slip_pixels']) + ","

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
        baseline_mosaic_png_path = file_path + '_baseline_mosaic.png'
        slip_png_path = file_path + "_slip.png"

        print("Creating query results.")
        #Mosaic

        save_to_geotiff(
            tif_path,
            gdal.GDT_Int16,
            dataset_out_baseline_mosaic,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_mosaic.dims['longitude'],
            y_pixels=dataset_out_mosaic.dims['latitude'],
            band_order=['blue', 'green', 'red'])
        # we've got the tif, now do the png. -> RGB
        bands = [3, 2, 1]
        create_rgb_png_from_tiff(
            tif_path, baseline_mosaic_png_path, png_filled_path=None, fill_color=None, bands=bands, scale=(0, 4096))

        save_to_geotiff(
            tif_path,
            gdal.GDT_Int16,
            dataset_out_mosaic,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_mosaic.dims['longitude'],
            y_pixels=dataset_out_mosaic.dims['latitude'],
            band_order=['blue', 'green', 'red'])
        # we've got the tif, now do the png. -> RGB
        bands = [3, 2, 1]
        create_rgb_png_from_tiff(
            tif_path, mosaic_png_path, png_filled_path=None, fill_color=None, bands=bands, scale=(0, 4096))

        #slip
        dataset_out_slip.to_netcdf(netcdf_path)
        save_to_geotiff(
            tif_path,
            gdal.GDT_Int32,
            dataset_out_slip,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_mosaic.dims['longitude'],
            y_pixels=dataset_out_mosaic.dims['latitude'],
            band_order=['red', 'green', 'blue', 'slip'])
        create_rgb_png_from_tiff(
            tif_path, slip_png_path, png_filled_path=None, fill_color=None, scale=(0, 4096), bands=[1, 2, 3])

        # update the results and finish up.
        update_model_bounds_with_dataset([result, meta, query], dataset_out_mosaic)
        result.result_mosaic_path = mosaic_png_path
        result.baseline_mosaic_path = baseline_mosaic_png_path
        result.result_path = slip_png_path
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
        error_with_message(result, "There was an exception when handling this query.", base_temp_path)
        raise
    # end error wrapping.
    return


@task(name="generate_slip_chunk")
def generate_slip_chunk(time_num,
                        chunk_num,
                        processing_options=None,
                        query=None,
                        acquisition_list=None,
                        lat_range=None,
                        lon_range=None,
                        measurements=None):
    """
    responsible for generating a piece of a slip product. This grabs the x/y area specified in the lat/lon ranges, gets all data
    from acquisition_list, which is a list of acquisition dates, and creates the slip using the function named in processing_options.
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
    time_ranges = list(
        generate_time_ranges(acquisition_list, processing_options['reverse_time'], processing_options[
            'time_slices_per_iteration']))

    # holds some acquisition based metadata.
    for time_index, time_range in enumerate(time_ranges):

        raw_data = dc.get_dataset_by_extent(
            query.product,
            product_type=None,
            platform=query.platform,
            time=time_range,
            longitude=lon_range,
            latitude=lat_range,
            measurements=measurements)
        aster = dc.get_dataset_by_extent(
            'terra_aster_gdm_' + query.area_id, latitude=lat_range, longitude=lon_range, measurements=['dem'])
        #Pretty much for metadata only.. Not all that useful, only kept for consistency.
        if "cf_mask" not in raw_data or "dem" not in aster:
            continue

        clear_mask = create_cfmask_clean_mask(raw_data.cf_mask)

        #Mosaic.
        iteration_data = create_mosaic(
            raw_data, clean_mask=clear_mask, reverse_time=True, intermediate_product=iteration_data)

        #Slip starts here. Remove nodata and filter by clear land pixels only.
        comparison = raw_data.where((raw_data.cf_mask == 0) & (raw_data >= 0))
        #mode is either average or composite
        baseline = generate_baseline(comparison, composite_size=query.baseline_length, mode=query.baseline)

        ndwi_comparison = (comparison.nir - comparison.swir1) / (comparison.nir + comparison.swir1)
        ndwi_baseline = (baseline.nir - baseline.swir1) / (baseline.nir + baseline.swir1)
        ndwi_change = ndwi_comparison - ndwi_baseline

        comparison_ndwi_filtered = comparison.where(abs(ndwi_change) > 0.20)
        red_change = (comparison.red - baseline.red) / (baseline.red)
        comparison_red_filtered = comparison_ndwi_filtered.where(red_change > 0.40)
        is_above_slope_threshold = create_slope_mask(aster, degree_threshold=15, resolution=30)
        comparison_red_slope_filtered = comparison_red_filtered.where(is_above_slope_threshold)

        #gather all relevant values from the baseline mosaics, average them, and insert them into the mosaic for the baseline mosaic.
        baseline_mosaic_data = iteration_data.where(comparison_red_slope_filtered > 0).mean('time')
        baseline_mosaic = iteration_data.copy(deep=True)
        # update metadata. # here the clear mask has all the clean
        # pixels for each acquisition.
        for timeslice in range(len(comparison_red_slope_filtered.time)):
            slip_slice = comparison_red_slope_filtered.isel(time=timeslice).red.values
            baseline_slice = baseline.isel(time=timeslice).red.values
            if len(slip_slice[slip_slice > 0]) > 0:
                time = raw_data.time.values[timeslice] if type(
                    raw_data.time.values[timeslice]) == datetime.datetime else datetime.datetime.utcfromtimestamp(
                        raw_data.time.values[timeslice].astype(int) * 1e-9)
                if time not in acquisition_metadata:
                    acquisition_metadata[time] = {}
                    acquisition_metadata[time]['clean_pixels'] = 0
                    acquisition_metadata[time]['slip_pixels'] = 0
                acquisition_metadata[time]['clean_pixels'] += len(baseline_slice[baseline_slice > 0])
                acquisition_metadata[time]['slip_pixels'] += len(slip_slice[slip_slice > 0])

        comparison_red_slope_filtered = comparison_red_slope_filtered.mean('time')

        #replace the pixels in the mosaic with the landslide pixels in slip.
        #Turn pixels red and fill in the rest from the mosaic.
        slip = comparison_red_slope_filtered.copy(deep=True)
        slip.red.values[~comparison_red_slope_filtered.isnull().red.values] = 4096
        slip.green.values[~comparison_red_slope_filtered.isnull().green.values] = 0
        slip.blue.values[~comparison_red_slope_filtered.isnull().red.values] = 0
        for band in iteration_data.data_vars:
            slip[band].values[comparison_red_slope_filtered.isnull()[band].values] = iteration_data[band].values[
                comparison_red_slope_filtered.isnull()[band].values]
            iteration_data[band].values[~comparison_red_slope_filtered.isnull()[
                band].values] = comparison_red_slope_filtered[band].values[~comparison_red_slope_filtered.isnull()[band]
                                                                           .values]
            baseline_mosaic[band].values[~baseline_mosaic_data.isnull()[band].values] = baseline_mosaic_data[
                band].values[~baseline_mosaic_data.isnull()[band].values]
        slip_mask = slip.red.copy(deep=True)
        slip_mask.values[~comparison_red_slope_filtered.isnull().red.values] = 1
        slip_mask.values[comparison_red_slope_filtered.isnull().red.values] = 0
        slip['slip'] = slip_mask.astype('int16')
    # Save this geographic chunk to disk.
    geo_path = base_temp_path + query.query_id + "/geo_chunk_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    geo_path_baseline = base_temp_path + query.query_id + "/geo_chunk_baseline" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    slip_path = base_temp_path + query.query_id + "/geo_chunk_slip_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    # if this is an empty chunk, just return an empty dataset.
    if iteration_data is None or not os.path.exists(base_temp_path + query.query_id):
        return None
    iteration_data.to_netcdf(geo_path)
    slip.to_netcdf(slip_path)
    baseline_mosaic.to_netcdf(geo_path_baseline)
    print("Done with chunk: " + str(time_num) + " " + str(chunk_num))
    return [geo_path, slip_path, geo_path_baseline, acquisition_metadata]


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
    from django.conf import settings
    dc = DataAccessApi(config='/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf')
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
    dc.dc.close()
