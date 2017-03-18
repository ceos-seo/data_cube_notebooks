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
import numpy as np

from .utils import (nearest_key, group_by_year, coastline_classification, coastline_classification_2,
                    split_by_year_and_append_stationary_year, adjust_color, darken_color, year_in_list_of_acquisitions,
                    most_recent_in_list_of_acquisitions, extract_landsat_scene_metadata,
                    extract_coastal_change_metadata)

from dateutil.relativedelta import relativedelta
from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import create_mosaic, create_median_mosaic
from utils.dc_utilities import (get_spatial_ref, save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask,
                                split_task, fill_nodata, generate_time_ranges)

from utils.dc_baseline import generate_baseline
from utils.dc_demutils import create_slope_mask
from utils.dc_water_classifier import wofs_classify
from data_cube_ui.utils import (update_model_bounds_with_dataset, map_ranges, combine_metadata, cancel_task,
                                error_with_message)

dc = None

base_result_path = '/datacube/ui_results/coastal_change/'
base_temp_path = '/datacube/ui_results_temp/'

green = [89, 255, 61]
green = darken_color(green, .8)

new_mosaic = (True)
new_boundary = (True)
pink = [[255, 8, 74], [252, 8, 74], [230, 98, 137], [255, 147, 172], [255, 192, 205]][0]
blue = [[13, 222, 255], [139, 237, 236], [0, 20, 225], [30, 144, 255]][-1]

measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']

processing_algorithms = {
    'coastal_change': {
        'geo_chunk_size': 0.05,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': None
    }
}


def _is_cached(query):
    if Result.objects.filter(query_id=query.query_id).exists():
        print("Repeat query, client will receive cached result.")
        return True
    else:
        return False


def _fetch_query_object(query_id, user_id):
    print("Starting for query:" + str(query_id))
    return Query.objects.get(query_id=query_id, user_id=user_id)


@task(name="coastal_change_task")
def create_coastal_change(query_id, user_id, single=False):

    query = _fetch_query_object(query_id, user_id)

    if _is_cached(query) == True:
        return

    result = query.generate_result()
    product_details = dc.dc.list_products()[dc.dc.list_products().name == query.product]

    try:
        platform = query.platform
        product = query.product
        resolution = product_details.resolution.values[0][1]
        start = datetime.datetime(int(query.time_start), 1, 1)
        end = datetime.datetime(int(query.time_end), 1, 1)
        time = (start, end + relativedelta(years=1))
        longitude = (query.longitude_min, query.longitude_max)
        latitude = (query.latitude_min, query.latitude_max)
        animation_pref = query.animated_product

        processing_options = processing_algorithms['coastal_change']

        acquisitions = dc.list_acquisition_dates(platform, product, time=time, longitude=longitude, latitude=latitude)

        if len(acquisitions) < 1:
            error_with_message(result, "There were no acquisitions for this parameter set.", base_temp_path)
            return

        if single:
            processing_options['time_chunks'] = None
            processing_options['time_slices_per_iteration'] = None

        latest_acquisition = most_recent_in_list_of_acquisitions(acquisitions)

        if end.year > latest_acquisition.year:
            raw_err_message = "Your end date is out of bounds! You've picked the year {choice},The latest acquistion that exists can be found at {actual}."
            err_message = raw_err_message.format(choice=end.year, actual=latest_acquisition)
            error_with_message(result, err_message, base_temp_path)
            return

        lat_ranges, lon_ranges, time_ranges = split_by_year_and_append_stationary_year(
            resolution=resolution,
            latitude=latitude,
            longitude=longitude,
            acquisitions=acquisitions,
            geo_chunk_size=processing_options['geo_chunk_size'],
            reverse_time=processing_options['reverse_time'],
            year_stationary=start.year)

        result.total_scenes = len(time_ranges)

        if animation_pref == "None":
            most_recent = max(time_ranges, key=lambda x: max([int(y.year) for y in x]))
            time_ranges = [most_recent]

        if os.path.exists(base_temp_path + query.query_id) == False:
            os.mkdir(base_temp_path + query.query_id)
            os.chmod(base_temp_path + query.query_id, 0o777)

        end_range_for_meta_data = (end - relativedelta(days=1), end + relativedelta(years=1))

        time_chunk_tasks = [
            group(
                generate_coastal_change_chunk.s(
                    time_range_index,
                    geographic_chunk_index,
                    processing_options=processing_options,
                    query=query,
                    product=product,
                    platform=platform,
                    acquisition_list=time_ranges[time_range_index],
                    lat_range=lat_ranges[geographic_chunk_index],
                    lon_range=lon_ranges[geographic_chunk_index],
                    measurements=measurements,
                    year_stationary=start.year,
                    end_range=end_range_for_meta_data)
                for geographic_chunk_index in range(len(lat_ranges))).apply_async()
            for time_range_index in range(len(time_ranges))
        ]

        dataset_out_mosaic = None
        dataset_out_coastal_change = None
        dataset_out_baseline_mosaic = None
        dataset_out_coastal_boundary = None
        dataset_out_slip = None
        acquisition_metadata = {}

        global_meta_data = {'scenes': {}, 'coastal_change': {}}

        for geographic_group in time_chunk_tasks:
            full_dataset = None
            tiles = []
            while not geographic_group.ready():
                result.refresh_from_db()
                if result.status == "CANCEL":
                    # revoke all tasks. Running tasks will continue to execute.
                    for task_group in time_chunk_tasks:
                        for child in task_group.children:
                            child.revoke()
                    cancel_task(query, result, base_temp_path)
                    return

            group_data = [data for data in geographic_group.get() if data is not None]

            result.scenes_processed += 1
            result.save()

            print("Got results for a time slice, computing intermediate product..")

            dataset_mosaic = xr.concat(
                reversed([xr.open_dataset(tile[0]) for tile in group_data]), dim='latitude').load()
            dataset_out_mosaic = fill_nodata(dataset_mosaic, dataset_out_mosaic)

            dataset_coastal_change = xr.concat(
                reversed([xr.open_dataset(tile[1]) for tile in group_data]), dim='latitude').load()
            dataset_out_coastal_change = fill_nodata(dataset_coastal_change, dataset_out_coastal_change)

            dataset_coastal_boundary = xr.concat(
                reversed([xr.open_dataset(tile[2]) for tile in group_data]), dim='latitude').load()
            dataset_out_coastal_boundary = fill_nodata(dataset_coastal_boundary, dataset_out_coastal_boundary)

            list_of_metadata = [tile[3] for tile in group_data]

            for data in list_of_metadata:
                scenes = data['scene']
                for key in scenes.keys():
                    if key not in global_meta_data['scenes']:
                        global_meta_data['scenes'][key] = {'total_pixels': 0, 'clear_pixels': 0}
                    global_meta_data['scenes'][key]["total_pixels"] = global_meta_data['scenes'][key][
                        "total_pixels"] + scenes[key]["total_pixels"]
                    global_meta_data['scenes'][key]["clear_pixels"] = global_meta_data['scenes'][key][
                        "clear_pixels"] + scenes[key]["clear_pixels"]

                task = data['coastal_change']

                if not global_meta_data['coastal_change']:
                    global_meta_data['coastal_change'] = {'sea_converted': 0, 'land_converted': 0}

                global_meta_data['coastal_change']['sea_converted'] = global_meta_data['coastal_change'][
                    'sea_converted'] + task['sea_converted']
                global_meta_data['coastal_change']['land_converted'] = global_meta_data['coastal_change'][
                    'land_converted'] + task['land_converted']

        dates = list(global_meta_data['scenes'].keys())
        dates.sort()

        meta = query.generate_metadata(
            scene_count=len(dates), pixel_count=len(dataset_mosaic.latitude) * len(dataset_mosaic.longitude))

        for date in reversed(dates):
            meta.acquisition_list += date.strftime("%m/%d/%Y") + ","
            meta.clean_pixels_per_acquisition += str(global_meta_data['scenes'][date]['clear_pixels']) + ","
            meta.clean_pixel_percentages_per_acquisition += str(global_meta_data['scenes'][date]['clear_pixels'] * 100 /
                                                                meta.pixel_count) + ","

        meta.land_converted = global_meta_data["coastal_change"]['land_converted']
        meta.sea_converted = global_meta_data["coastal_change"]['sea_converted']
        meta.save()

        latitude = dataset_out_mosaic.latitude
        longitude = dataset_out_mosaic.longitude

        shutil.rmtree(base_temp_path + query.query_id)

        geotransform = [
            longitude.values[0], product_details.resolution.values[0][1], 0.0, latitude.values[0], 0.0,
            product_details.resolution.values[0][0]
        ]
        crs = str("EPSG:4326")

        file_path = base_result_path + query_id
        tif_path = file_path + '.tif'
        netcdf_path = file_path + '.nc'

        mosaic_png_path = file_path + '_mosaic.png'
        coastal_change_png_path = file_path + '_coastal_change.png'
        coastal_boundary_png_path = file_path + "_coastal_boundaries.png"

        print("Creating query results.")

        save_to_geotiff(
            tif_path,
            gdal.GDT_Int16,
            dataset_out_mosaic,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_mosaic.dims['longitude'],
            y_pixels=dataset_out_mosaic.dims['latitude'],
            band_order=['blue', 'green', 'red'])

        bands = [3, 2, 1]
        create_rgb_png_from_tiff(
            tif_path, mosaic_png_path, png_filled_path=None, fill_color=None, bands=bands, scale=(0, 4096))

        dataset_mosaic.to_netcdf(netcdf_path)

        save_to_geotiff(
            tif_path,
            gdal.GDT_Int32,
            dataset_out_coastal_change,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_coastal_change.dims['longitude'],
            y_pixels=dataset_out_coastal_change.dims['latitude'],
            band_order=['red', 'green', 'blue'])

        create_rgb_png_from_tiff(
            tif_path, coastal_change_png_path, png_filled_path=None, fill_color=None, scale=(0, 4096), bands=[1, 2, 3])

        dataset_out_coastal_change.to_netcdf(netcdf_path)

        save_to_geotiff(
            tif_path,
            gdal.GDT_Int32,
            dataset_out_coastal_boundary,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_coastal_boundary.dims['longitude'],
            y_pixels=dataset_out_coastal_boundary.dims['latitude'],
            band_order=['red', 'green', 'blue'])

        create_rgb_png_from_tiff(
            tif_path,
            coastal_boundary_png_path,
            png_filled_path=None,
            fill_color=None,
            scale=(0, 4096),
            bands=[1, 2, 3])

        dataset_out_coastal_boundary.to_netcdf(netcdf_path)

        if animation_pref == 'yearly':
            print("=====-----=====-----=====-----")
            times = [item for sublist in time_ranges for item in sublist]
            max_year = max(times).year
            min_year = min(times).year
            time_range = range(min_year, max_year + 1)

        else:
            pass

        update_model_bounds_with_dataset([result, meta, query], dataset_out_mosaic)

        result.result_path = coastal_boundary_png_path
        result.result_mosaic_path = mosaic_png_path
        result.result_coastal_change_path = coastal_change_png_path

        result.data_path = tif_path
        result.data_netcdf_path = netcdf_path
        result.status = "OK"
        result.total_scenes = len(acquisitions)

        result.save()

        print("Finished processing results")

        query.complete = True
        query.query_end = datetime.datetime.now()

        query.save()

    except:
        error_with_message(result, "There was an exception when handling this query.", base_temp_path)
        raise
    return


@task(name="generate_coastal_change_chunk")
def generate_coastal_change_chunk(time_num,
                                  chunk_num,
                                  processing_options=None,
                                  query=None,
                                  acquisition_list=None,
                                  lat_range=None,
                                  lon_range=None,
                                  measurements=None,
                                  platform=None,
                                  product=None,
                                  year_stationary=None,
                                  end_range=None):

    if not os.path.exists(base_temp_path + query.query_id):
        return None

    per_scene_clear_pixel = 0
    percentage_clear_pixel = 0
    per_scene_water_pixel = 0
    cf_mask_per_scene = 0

    time_index = 0
    old_mosaic = None
    new_mosaic = None
    acquisition_metadata = {}

    time_dict = group_by_year(acquisition_list)
    stationary_key = min([int(key) for key in time_dict.keys()])
    most_recent_key = max([int(key) for key in time_dict.keys()])

    stationary_acquisitions = time_dict[stationary_key]
    most_recent_acquisitions = time_dict[most_recent_key]

    old_landsat = dc.get_dataset_by_extent(
        product,
        product_type=None,
        platform=platform,
        time=(min(stationary_acquisitions), max(stationary_acquisitions)),
        longitude=lon_range,
        latitude=lat_range,
        measurements=measurements)
    old_landsat = old_landsat.where(old_landsat >= 0)

    new_landsat = dc.get_dataset_by_extent(
        product,
        product_type=None,
        platform=platform,
        time=(min(most_recent_acquisitions), max(most_recent_acquisitions)),
        longitude=lon_range,
        latitude=lat_range,
        measurements=measurements)
    new_landsat = new_landsat.where(new_landsat >= 0)

    old_mosaic = create_mosaic(old_landsat)

    new_mosaic = create_median_mosaic(new_landsat)

    old_water = wofs_classify(old_mosaic, mosaic=True)

    new_water = wofs_classify(new_mosaic, mosaic=True)

    old_landsat.drop(['nir', 'swir1', 'swir2'])
    old_mosaic.drop(['nir', 'swir1', 'swir2'])

    new_landsat.drop(['nir', 'swir1', 'swir2'])
    new_mosaic.drop(['nir', 'swir1', 'swir2'])

    coastal_change = new_water - old_water
    coastal_change.rename({"wofs": "wofs_change"}, inplace=True)

    coastal_change = coastal_change.where(coastal_change.wofs_change != 0)

    new_coastline = coastline_classification_2(new_water)

    old_coastline = coastline_classification_2(old_water)

    target = new_mosaic if new_mosaic else old_mosaic

    change = target.copy(deep=True)
    change.red.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[0])
    change.green.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[1])
    change.blue.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[2])

    change.red.values[coastal_change.wofs_change.values == -1] = adjust_color(green[0])
    change.green.values[coastal_change.wofs_change.values == -1] = adjust_color(green[1])
    change.blue.values[coastal_change.wofs_change.values == -1] = adjust_color(green[2])

    boundary = target.copy(deep=True)
    boundary = boundary

    boundary.red.values[new_coastline.coastline.values == 1] = adjust_color(blue[0])
    boundary.green.values[new_coastline.coastline.values == 1] = adjust_color(blue[1])
    boundary.blue.values[new_coastline.coastline.values == 1] = adjust_color(blue[2])

    boundary.red.values[old_coastline.coastline.values == 1] = adjust_color(green[0])
    boundary.green.values[old_coastline.coastline.values == 1] = adjust_color(green[1])
    boundary.blue.values[old_coastline.coastline.values == 1] = adjust_color(green[2])

    if not os.path.exists(base_temp_path + query.query_id):
        return None

    geo_path = base_temp_path + query.query_id + "/composite_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    boundary_change_path  = base_temp_path + query.query_id + "/boundary_" +  \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    coastal_change_path = base_temp_path + query.query_id + "/change_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"

    target.to_netcdf(geo_path)

    change.to_netcdf(coastal_change_path)

    boundary.to_netcdf(boundary_change_path)

    meta_data = {"scene": {}, "coastal_change": {"land_converted": 0, "sea_converted": 0}}

    latest_year = datetime.datetime(most_recent_key, 2, 2)
    date_floor = end_range[0]
    date_ceil = end_range[1]

    if (latest_year >= date_floor) & (latest_year <= date_ceil):

        old_acquisition_meta_data = extract_landsat_scene_metadata(old_landsat)

        new_acquisition_meta_data = extract_landsat_scene_metadata(new_landsat)

        task_meta_data = extract_coastal_change_metadata(coastal_change)

        old_and_new_acquisition_meta_data = {'scene': {
            **old_acquisition_meta_data['scene'],
            **new_acquisition_meta_data['scene']
        }}

        meta_data = {**old_and_new_acquisition_meta_data, **task_meta_data}

    return [geo_path, coastal_change_path, boundary_change_path, meta_data]


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
