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

from .utils import (group_by_year, split_task_by_year, adjust_color, darken_color, year_in_list_of_acquisitions,
                    extract_coastal_change_metadata)

from dateutil.relativedelta import relativedelta
from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import create_median_mosaic, create_mosaic
from utils.dc_utilities import (get_spatial_ref, save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask,
                                split_task, fill_nodata, generate_time_ranges)

from utils.dc_coastline_classification import coastline_classification, coastline_classification_2
from utils.dc_baseline import generate_baseline
from utils.dc_demutils import create_slope_mask
from utils.dc_water_classifier import wofs_classify
from data_cube_ui.utils import (update_model_bounds_with_dataset, map_ranges, combine_metadata, cancel_task,
                                error_with_message, n64_to_datetime)

# Datacube instance to be initialized.
# A seperate DC instance is created for each worker.
dc = None

base_result_path = '/datacube/ui_results/coastal_change/'
base_temp_path = '/datacube/ui_results_temp/'

green = [89, 255, 61]
green = darken_color(green, .8)

pink = [[255, 8, 74], [252, 8, 74], [230, 98, 137], [255, 147, 172], [255, 192, 205]][0]
blue = [[13, 222, 255], [139, 237, 236], [0, 20, 225], [30, 144, 255]][-1]

#default measurements. leaves out all qa bands.
measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']

#holds the different compositing algorithms. Most/least recent, max/min ndvi, median, etc.
# all options are required. setting None to a option will have the algo/task splitting
# process disregard it.
#experimentally optimized geo/time/slices_per_iter
#set up for median.
processing_algorithms = {
    'coastal_change': {
        'geo_chunk_size': 0.01,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': create_median_mosaic
    }
}


@task(name="coastal_change_task")
def create_coastal_change(query_id, user_id, single=False):

    print("Starting for query:" + query_id)

    query = Query._fetch_query_object(query_id, user_id)

    if query is None:
        print("Query does not yet exist.")
        return

    if query._is_cached(Result):
        print("Repeat query, client will receive cached result.")
        return

    print("Got the query, creating metadata.")

    result = query.generate_result()
    product_details = dc.dc.list_products()[dc.dc.list_products().name == query.product]

    try:
        platform = query.platform
        product = query.product
        resolution = product_details.resolution.values[0][1]
        start = datetime.datetime(int(query.time_start), 1, 1)
        end = datetime.datetime(int(query.time_end), 1, 1)
        #time is inclusive of the last year.
        time = (start, end + relativedelta(years=1))
        longitude = (query.longitude_min, query.longitude_max)
        latitude = (query.latitude_min, query.latitude_max)
        animated_product = query.animated_product

        processing_options = processing_algorithms['coastal_change']

        acquisitions = dc.list_acquisition_dates(platform, product, time=time, longitude=longitude, latitude=latitude)

        if len(acquisitions) < 1:
            error_with_message(result, "There were no acquisitions for this parameter set.", base_temp_path)
            return

        #acquisitions is sorted, so the latest one is the last in the array.
        latest_acquisition = acquisitions[-1]

        if end.year > latest_acquisition.year:
            raw_err_message = "Your end date is out of bounds! You've picked the year {choice},The latest acquistion that exists can be found at {actual}."
            err_message = raw_err_message.format(choice=end.year, actual=latest_acquisition)
            error_with_message(result, err_message, base_temp_path)
            return

        lat_ranges, lon_ranges, time_ranges = split_task_by_year(
            resolution=resolution,
            latitude=latitude,
            longitude=longitude,
            acquisitions=acquisitions,
            geo_chunk_size=processing_options['geo_chunk_size'],
            reverse_time=processing_options['reverse_time'])

        year_dict = group_by_year(acquisitions)

        if query.time_start not in year_dict:
            error_with_message(result, "There are no acquisitions for your desired starting year.", base_temp_path)
        if query.time_end not in year_dict:
            error_with_message(result, "There are no acquisitions for your desired ending year.", base_temp_path)

        processing_options['stationary_year_acquisitions'] = year_dict[query.time_start]
        #remove the initial year's acquisitions as they're included above.
        time_ranges.pop(-1)
        result.total_scenes = len(time_ranges)
        result.save()

        #we can skip everything except for the most recent year if there's no animation
        if animated_product == "None":
            time_ranges = [time_ranges[0]]

        if os.path.exists(base_temp_path + query.query_id) == False:
            os.mkdir(base_temp_path + query.query_id)
            os.chmod(base_temp_path + query.query_id, 0o777)

        print("Time chunks: " + str(len(time_ranges)))
        print("Geo chunks: " + str(len(lat_ranges)))

        time_chunk_tasks = [
            group(
                generate_coastal_change_chunk.s(
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

        dataset_out_mosaic = None
        dataset_out_coastal_change = None
        dataset_out_baseline_mosaic = None
        dataset_out_coastal_boundary = None
        acquisition_metadata = {}

        time_range_index = 0

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

            if len(group_data) < 1:
                time_range_index += 1
                continue

            acquisition_metadata = combine_metadata(acquisition_metadata, [tile[3] for tile in group_data])

            dataset_mosaic = xr.concat(
                reversed([xr.open_dataset(tile[0]) for tile in group_data]), dim='latitude').load()

            dataset_coastal_change = xr.concat(
                reversed([xr.open_dataset(tile[1]) for tile in group_data]), dim='latitude').load()

            dataset_coastal_boundary = xr.concat(
                reversed([xr.open_dataset(tile[2]) for tile in group_data]), dim='latitude').load()

            #we only want the most recent year comparison results..
            if dataset_out_mosaic is None:
                dataset_out_coastal_boundary = fill_nodata(dataset_coastal_boundary, dataset_out_coastal_boundary)
                dataset_out_coastal_change = fill_nodata(dataset_coastal_change, dataset_out_coastal_change)
                dataset_out_mosaic = fill_nodata(dataset_mosaic, dataset_out_mosaic)

            #create animation frames
            if query.animated_product != "None":
                animation_data = dataset_coastal_change if query.animated_product == "coastal_change" else dataset_coastal_boundary
                latitude = dataset_out_mosaic.latitude
                longitude = dataset_out_mosaic.longitude

                geotransform = [
                    longitude.values[0], product_details.resolution.values[0][1], 0.0, latitude.values[0], 0.0,
                    product_details.resolution.values[0][0]
                ]
                crs = str("EPSG:4326")

                tif_path = base_temp_path + query.query_id + '/' + \
                    '/' + str(time_range_index) + '_animation_frame.tif'
                png_path = base_temp_path + query.query_id + \
                    '/' + str(time_range_index) + '_animation_frame.png'

                save_to_geotiff(
                    tif_path,
                    gdal.GDT_Int16,
                    animation_data,
                    geotransform,
                    get_spatial_ref(crs),
                    x_pixels=dataset_out_mosaic.dims['longitude'],
                    y_pixels=dataset_out_mosaic.dims['latitude'],
                    band_order=['blue', 'green', 'red'])

                bands = [3, 2, 1]
                create_rgb_png_from_tiff(
                    tif_path, png_path, png_filled_path=None, fill_color=None, bands=bands, scale=(0, 4096))

                time_range_index += 1
                os.remove(tif_path)

        dates = list(acquisition_metadata.keys())
        dates.sort()

        meta = query.generate_metadata(
            scene_count=len(dates), pixel_count=len(dataset_mosaic.latitude) * len(dataset_mosaic.longitude))

        for date in reversed(dates):
            meta.acquisition_list += date.strftime("%m/%d/%Y") + ","
            meta.clean_pixels_per_acquisition += str(acquisition_metadata[date]['clean_pixels']) + ","
            meta.clean_pixel_percentages_per_acquisition += str(acquisition_metadata[date]['clean_pixels'] * 100 /
                                                                meta.pixel_count) + ","

        coastal_metadata = extract_coastal_change_metadata(dataset_out_coastal_change)
        meta.land_converted = coastal_metadata["coastal_change"]['land_converted']
        meta.sea_converted = coastal_metadata["coastal_change"]['sea_converted']
        clean_pixels = np.sum(dataset_out_coastal_change[measurements[0]].values != -9999)
        meta.clean_pixel_count = clean_pixels
        meta.percentage_clean_pixels = (meta.clean_pixel_count / meta.pixel_count) * 100
        meta.save()

        latitude = dataset_out_mosaic.latitude
        longitude = dataset_out_mosaic.longitude

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
        animation_path = file_path + '_mosaic_animation.gif'

        print("Creating query results.")

        if query.animated_product != "None":
            import imageio
            with imageio.get_writer(animation_path, mode='I', duration=1.0) as writer:
                for index in range(time_range_index):
                    image = imageio.imread(base_temp_path + query.query_id + \
                        '/' + str(index) + '_animation_frame.png')
                    writer.append_data(image)
            result.animation_path = animation_path

        shutil.rmtree(base_temp_path + query.query_id)

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

        dataset_out_coastal_boundary['coastal_change'] = dataset_out_coastal_change['coastal_change']
        save_to_geotiff(
            tif_path,
            gdal.GDT_Int32,
            dataset_out_coastal_boundary,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_coastal_boundary.dims['longitude'],
            y_pixels=dataset_out_coastal_boundary.dims['latitude'],
            band_order=[
                'blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask', 'coastline_old', 'coastline_new',
                'coastal_change'
            ])

        create_rgb_png_from_tiff(
            tif_path,
            coastal_boundary_png_path,
            png_filled_path=None,
            fill_color=None,
            scale=(0, 4096),
            bands=[3, 2, 1])

        dataset_out_coastal_boundary.to_netcdf(netcdf_path)

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
                                  measurements=None):

    if not os.path.exists(base_temp_path + query.query_id):
        return None

    time_index = 0
    acquisition_metadata = {}

    print("Starting chunk: " + str(time_num) + " " + str(chunk_num))
    #base year, then current year. [0] = acquisition list, [1] = mosaic dataset
    _acquisitions = {
        'start': [processing_options['stationary_year_acquisitions'], None],
        'end': [acquisition_list, None]
    }

    for acq_set in _acquisitions:
        time_ranges = list(
            generate_time_ranges(_acquisitions[acq_set][0], processing_options['reverse_time'], processing_options[
                'time_slices_per_iteration']))

        for time_index, time_range in enumerate(time_ranges):
            raw_data = dc.get_dataset_by_extent(
                query.product,
                product_type=None,
                platform=query.platform,
                time=time_range,
                longitude=lon_range,
                latitude=lat_range,
                measurements=measurements)

            clear_mask = create_cfmask_clean_mask(raw_data.cf_mask)
            _acquisitions[acq_set][1] = processing_options['processing_method'](
                raw_data,
                clean_mask=clear_mask,
                intermediate_product=_acquisitions[acq_set][1],
                reverse_time=processing_options['reverse_time'])

            for timeslice in range(clear_mask.shape[0]):
                time = raw_data.time.values[timeslice] if type(
                    raw_data.time.values[timeslice]) == datetime.datetime else n64_to_datetime(
                        raw_data.time.values[timeslice])
                clean_pixels = np.sum(clear_mask[timeslice, :, :] == True)
                if time not in acquisition_metadata:
                    acquisition_metadata[time] = {}
                    acquisition_metadata[time]['clean_pixels'] = 0
                acquisition_metadata[time]['clean_pixels'] += clean_pixels

    old_mosaic = _acquisitions['start'][1]
    new_mosaic = _acquisitions['end'][1]

    #now that we have the mosaics, we can do wofs..
    combined_mask = create_cfmask_clean_mask(old_mosaic.cf_mask) & create_cfmask_clean_mask(new_mosaic.cf_mask)
    print(combined_mask[~combined_mask])
    old_water = wofs_classify(old_mosaic, mosaic=True, clean_mask=combined_mask)
    new_water = wofs_classify(new_mosaic, mosaic=True)

    coastal_change = new_water - old_water
    coastal_change.rename({"wofs": "wofs_change"}, inplace=True)

    coastal_change = coastal_change.where(coastal_change.wofs_change != 0)

    new_coastline = coastline_classification_2(new_water)
    old_coastline = coastline_classification_2(old_water)

    change = new_mosaic.copy(deep=True)
    change.red.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[0])
    change.green.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[1])
    change.blue.values[coastal_change.wofs_change.values == 1] = adjust_color(pink[2])

    change.red.values[coastal_change.wofs_change.values == -1] = adjust_color(green[0])
    change.green.values[coastal_change.wofs_change.values == -1] = adjust_color(green[1])
    change.blue.values[coastal_change.wofs_change.values == -1] = adjust_color(green[2])
    change['coastal_change'] = coastal_change.wofs_change

    boundary = new_mosaic.copy(deep=True)
    boundary.red.values[new_coastline.coastline.values == 1] = adjust_color(blue[0])
    boundary.green.values[new_coastline.coastline.values == 1] = adjust_color(blue[1])
    boundary.blue.values[new_coastline.coastline.values == 1] = adjust_color(blue[2])

    boundary.red.values[old_coastline.coastline.values == 1] = adjust_color(green[0])
    boundary.green.values[old_coastline.coastline.values == 1] = adjust_color(green[1])
    boundary.blue.values[old_coastline.coastline.values == 1] = adjust_color(green[2])
    boundary['coastline_old'] = old_coastline.coastline
    boundary['coastline_new'] = new_coastline.coastline

    if not os.path.exists(base_temp_path + query.query_id):
        return None

    geo_path = base_temp_path + query.query_id + "/composite_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    boundary_change_path  = base_temp_path + query.query_id + "/boundary_" +  \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    coastal_change_path = base_temp_path + query.query_id + "/change_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"

    new_mosaic.to_netcdf(geo_path)
    change.to_netcdf(coastal_change_path)
    boundary.to_netcdf(boundary_change_path)

    return [geo_path, coastal_change_path, boundary_change_path, acquisition_metadata]


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
