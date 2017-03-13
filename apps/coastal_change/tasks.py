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
from .utils import coastline_classification, split_by_year_and_append_stationary_year,adjust_color,darken_color

from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import create_mosaic
from utils.dc_utilities import nearest_key, group_by_year, get_spatial_ref,  save_to_geotiff, create_rgb_png_from_tiff, create_cfmask_clean_mask, split_task, fill_nodata, generate_time_ranges
from utils.dc_baseline import generate_baseline
from utils.dc_demutils import create_slope_mask
from utils.dc_water_classifier import wofs_classify

from data_cube_ui.utils import update_model_bounds_with_dataset, map_ranges, combine_metadata, cancel_task, error_with_message

dc = None

BASE_RESULT_PATH = '/datacube/ui_results/coastal_change/'
BASE_TEMP_PATH = '/datacube/ui_results_temp/'

GREEN        = [89,255,61]
GREEN        = darken_color(GREEN,.8)

NEW_MOSAIC   = (True)
NEW_BOUNDARY = (True)
PINK         = [[255,8,74],[252,8,74],[230,98,137],[255,147,172],[255,192,205]][0]
BLUE         = [[13,222,255],[139,237,236],[0,20,225],[30,144,255]][-1]
MEASUREMENTS = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']


processing_algorithms = {
    'change' : {
        'geo_chunk_size': 0.05,
        'time_chunks': None,
        'time_slices_per_iteration': None,
        'reverse_time': True,
        'chunk_combination_method': fill_nodata,
        'processing_method': None
    },
    'boundary' : {
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


#######################################################################################
#           ＱＵＥＲＹ ｜ ＰＡＲＳＩＮＧ｜ ＡＮＤ ｜ ＣＨＵＮＫ ｜ ＤＥＬＥＧＡＴＩＯＮ｜
#######################################################################################

@task(name="coastal_change_task")
def create_coastal_change(query_id, user_id, single=False):

    query = _fetch_query_object(query_id, user_id)

    if _is_cached(query) == True:
       return
    
    result = query.generate_result()
    product_details = dc.dc.list_products()[dc.dc.list_products().name == query.product]

    try:
        ## Extract Info from query ############################################
        platform    = query.platform
        product     = query.product
        resolution  = product_details.resolution.values[0][1]
        start       = datetime.datetime(int(query.time_start), 1, 1)
        end         = datetime.datetime(int(query.time_end) + 1, 1, 1)
        time        = (start,end)
        longitude   = (query.longitude_min, query.longitude_max)
        latitude    = (query.latitude_min, query.latitude_max)
        display_pref   = query.product_setting
        animation_pref = query.animation_setting 
        ######################################################################

        ## Select chunking process using details from query ##################
        processing_options = processing_algorithms[query.product_setting]
        ######################################################################

        ## Get Acquisition data ##############################################
        acquisitions = dc.list_acquisition_dates(platform, product, time=time, longitude=longitude, latitude=latitude)
        ######################################################################

        ## Rough Validation of acquisitions ##################################
        if len(acquisitions) < 1:
            error_with_message(result, "There were no acquisitions for this parameter set.", BASE_TEMP_PATH)
            return
        ######################################################################

        if single:
            processing_options['time_chunks'] = None
            processing_options['time_slices_per_iteration'] = None
      
        ## This is how chunk sizes are defined ###############################
        lat_ranges, lon_ranges, time_ranges = split_by_year_and_append_stationary_year(
            resolution     = resolution,
            latitude       = latitude,
            longitude      = longitude,
            acquisitions   = acquisitions,
            geo_chunk_size = processing_options['geo_chunk_size'],  
            reverse_time   = processing_options['reverse_time'],
            year_stationary= start.year)
        ######################################################################  

        result.total_scenes = len(time_ranges)

        if os.path.exists(BASE_TEMP_PATH + query.query_id) == False:
            os.mkdir(BASE_TEMP_PATH + query.query_id)
            os.chmod(BASE_TEMP_PATH + query.query_id, 0o777)
            print("||CREATED: " + str(BASE_TEMP_PATH + query.query_id))

        print(">>>>>>>>>>>_Delegating_Coastal_Change_Tasks_>>>>>>>>>>>>:")

        ## This is where tasks are created and and sent for processing
        time_chunk_tasks = [group(generate_coastal_change_chunk.s(time_range_index, 
                                        geographic_chunk_index,
                                        processing_options=processing_options,
                                        query=query,
                                        product = product,
                                        platform = platform,
                                        acquisition_list=time_ranges[time_range_index],
                                        lat_range=lat_ranges[geographic_chunk_index],
                                        lon_range=lon_ranges[geographic_chunk_index], 
                                        measurements=MEASUREMENTS,
                                        year_stationary = start.year
                                        ) for geographic_chunk_index in range(len(lat_ranges))).apply_async() for time_range_index in range(len(time_ranges))]

        ##########################################################################################
        #                       ＰＯＳＴ ｜ ＣＨＵＮＫ ｜ ＰＲＯＣＥＳＳＩＮＧ
        ##########################################################################################

        dataset_out_mosaic          = None
        dataset_out_coastal_change  = None
        dataset_out_baseline_mosaic = None
        dataset_out_coastal_boundary= None
        dataset_out_slip            = None
        acquisition_metadata        = {}

        ### Rebuild product from results.   
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
                    cancel_task(query, result, BASE_TEMP_PATH)
                    return

            ## THIS MAY BE ILLEGAL
            group_data = [data for data in geographic_group.get()
                    if data is not None]

            result.scenes_processed += 1
            result.save()

            print("Got results for a time slice, computing intermediate product..")

            ####################################################
            #create cf mosaic
            dataset_mosaic = xr.concat(reversed([xr.open_dataset(tile[0]) for tile in group_data]), dim='latitude').load()
            dataset_out_mosaic = fill_nodata(dataset_mosaic, dataset_out_mosaic)

            
            #now coastal_cahnge.
            dataset_coastal_change = xr.concat(reversed([xr.open_dataset(tile[1]) for tile in group_data]), dim='latitude').load()
            dataset_out_coastal_change = fill_nodata(dataset_coastal_change, dataset_out_coastal_change)

            #create baseline mosaic
            dataset_coastal_boundary = xr.concat(reversed([xr.open_dataset(tile[2]) for tile in group_data]), dim='latitude').load()
            dataset_out_coastal_boundary = fill_nodata(dataset_coastal_boundary, dataset_out_coastal_boundary)
            

        latitude = dataset_out_mosaic.latitude
        longitude = dataset_out_mosaic.longitude

        # remove intermediates
        shutil.rmtree(BASE_TEMP_PATH + query.query_id)

        ####################################################

        # grabs the resolution.
        geotransform = [longitude.values[0], product_details.resolution.values[0][1],
                        0.0, latitude.values[0], 0.0, product_details.resolution.values[0][0]]
        #hardcoded crs for now. This is not ideal. Should maybe store this in the db with product type?
        crs = str("EPSG:4326")

        ####################################################

        file_path                   = BASE_RESULT_PATH + query_id
        tif_path                    = file_path + '.tif'
        netcdf_path                 = file_path + '.nc'

        mosaic_png_path             = file_path + '_mosaic.png'
        coastal_change_png_path     = file_path + '_coastal_change.png'
        coastal_boundary_png_path   = file_path + "_coastal_boundaries.png"

####################################################

        print("Creating query results.")

        #Mosaic ##############################################################
        save_to_geotiff(tif_path,
            gdal.GDT_Int16,
            dataset_out_mosaic,
            geotransform,
            get_spatial_ref(crs), 
            x_pixels=dataset_out_mosaic.dims['longitude'],
            y_pixels=dataset_out_mosaic.dims['latitude'],
            band_order=['blue', 'green', 'red']
            )

        bands = [3, 2, 1]
        create_rgb_png_from_tiff(tif_path,
            mosaic_png_path,
            png_filled_path=None,
            fill_color=None,
            bands=bands,
            scale=(0, 4096)
            )

        dataset_mosaic.to_netcdf(netcdf_path)
        
        #Coastal Change ######################################################

        save_to_geotiff(tif_path,
            gdal.GDT_Int32,
            dataset_out_coastal_change,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_coastal_change.dims['longitude'],
            y_pixels=dataset_out_coastal_change.dims['latitude'],
            band_order=['red', 'green', 'blue']
            )

        create_rgb_png_from_tiff(tif_path,
            coastal_change_png_path,
            png_filled_path=None,
            fill_color=None,
            scale=(0, 4096),
            bands=[1,2,3]
            )

        dataset_out_coastal_change.to_netcdf(netcdf_path)

        #Boundary Change ####################################################

        save_to_geotiff(tif_path,
            gdal.GDT_Int32,
            dataset_out_coastal_boundary,
            geotransform,
            get_spatial_ref(crs),
            x_pixels=dataset_out_coastal_boundary.dims['longitude'],
            y_pixels=dataset_out_coastal_boundary.dims['latitude'],
            band_order=['red', 'green', 'blue'])

        create_rgb_png_from_tiff(tif_path,
            coastal_boundary_png_path,
            png_filled_path=None,
            fill_color=None,
            scale=(0, 4096),
            bands=[1,2,3])

        dataset_out_coastal_boundary.to_netcdf(netcdf_path)

        # Build Animation!
        if animation_pref == 'yearly':
            print("=====-----=====-----=====-----")
            times = [item for sublist in time_ranges for item in sublist]
            max_year = max(times).year
            min_year = min(times).year
            time_range = range(min_year , max_year + 1)
            

        else:
            pass


        #Build Result Object #################################################

        meta = query.generate_metadata()
        update_model_bounds_with_dataset([result, meta, query], dataset_out_mosaic)

        result.result_mosaic_path       = mosaic_png_path
        result.coastal_change_path      = coastal_change_png_path 
        result.coastline_change_path    = coastal_boundary_png_path

        result.data_path        = tif_path
        result.data_netcdf_path = netcdf_path
        result.status           = "OK"
        result.total_scenes     = len(acquisitions)

        #Select what UI ends up displaying
        if   display_pref == 'change':
            result.result_path      = coastal_change_png_path
        elif display_pref == 'boundary':
            result.result_path      = coastal_boundary_png_path
        else:
            print("!!!!!!!!!!!!!!!!")
            print(display_pref)
        result.save()

        print("Finished processing results")
        
        query.complete = True
        query.query_end = datetime.datetime.now()
        
        query.save()

    except:
        error_with_message(
            result, "There was an exception when handling this query.", BASE_TEMP_PATH)
        raise
    return

##########################################################################################################
#                              ＣＨＵＮＫ ｜ ＰＲＯＣＥＳＳＩＮＧ ｜ ＣＯＤＥ
##########################################################################################################

@task(name="generate_coastal_change_chunk")
def generate_coastal_change_chunk(time_num,
 chunk_num,
 processing_options=None,
 query=None,
 acquisition_list=None,
 lat_range=None, 
 lon_range=None, 
 measurements=None,
 platform = None,
 product = None,
 year_stationary = None):
    
    if not os.path.exists(BASE_TEMP_PATH + query.query_id):
        return None

    time_index              = 0
    old_mosaic              = None
    new_mosaic              = None
    acquisition_metadata    = {}

    ## Building Time Ranges ####################################

    time_dict = group_by_year(acquisition_list)
    stationary_key = nearest_key(time_dict, year_stationary)
    most_recent_key = [key for key in time_dict.keys() if key is not stationary_key][-1]

    stationary_acquisitions  = time_dict[stationary_key]
    most_recent_acquisitions = time_dict[most_recent_key]

    ##Loading Data #############################################

    print("___Loading___\n" + str((min(stationary_acquisitions).year, max(stationary_acquisitions).year)))
    old_landsat = dc.get_dataset_by_extent(product,
            product_type=None,
            platform=platform,
            time=(min(stationary_acquisitions), max(stationary_acquisitions)),
            longitude=lon_range,
            latitude=lat_range,
            measurements=measurements)
    old_landsat = old_landsat.where(old_landsat >= 0)

    print("___Loading___\n" + str((min(most_recent_acquisitions).year, max(most_recent_acquisitions).year)))
    new_landsat = dc.get_dataset_by_extent(product,
            product_type=None,
            platform=platform,
            time=(min(most_recent_acquisitions), max(most_recent_acquisitions)),
            longitude=lon_range,
            latitude=lat_range,
            measurements=measurements)
    new_landsat = new_landsat.where(new_landsat >= 0)

    ##Build Mosaic ###############################################
    old_clear_mask = create_cfmask_clean_mask(old_landsat.cf_mask)
    old_landsat.drop(['cf_mask'])

    new_clear_mask = create_cfmask_clean_mask(new_landsat.cf_mask)
    new_landsat.drop(['cf_mask'])

    old_mosaic = create_mosaic(old_landsat,
        clean_mask=old_clear_mask,
        reverse_time=True,
        intermediate_product=old_mosaic)
    
    new_mosaic = create_mosaic(new_landsat,
        clean_mask=new_clear_mask,
        reverse_time=True,
        intermediate_product=new_mosaic)

    ##Build Wofs #####################################
    old_water = wofs_classify(old_mosaic, mosaic=True)
    old_water = old_water.where(old_water >= 0)

    new_water = wofs_classify(new_mosaic, mosaic=True)
    new_water = new_water.where(new_water >= 0)

    ##########################
    old_landsat.drop(['nir','swir1','swir2'])
    old_mosaic.drop( ['nir','swir1','swir2'])

    ##########################
    new_landsat.drop( ['nir','swir1','swir2'])
    new_mosaic.drop(  ['nir','swir1','swir2'])

    ##Coastal Change Calculation #################################
    coastal_change  = new_water - old_water
    coastal_change = coastal_change.where(coastal_change.wofs != 0)

    ##Coastal Boundary Calculation ###############################
    new_coastline = coastline_classification(new_water)
    old_coastline = coastline_classification(old_water)
    
    ##DISPLAY NEWEST VS OLDEST MOSAIC#############################
    target = new_mosaic if NEW_MOSAIC else old_mosaic

    ##Coastal Change visual Raster ###############################
    change = target.copy(deep =True)
    change.red.values[coastal_change.wofs.values == 1]      = adjust_color(PINK[0])
    change.green.values[coastal_change.wofs.values == 1]    = adjust_color(PINK[1])
    change.blue.values[coastal_change.wofs.values == 1]     = adjust_color(PINK[2])

    change.red.values[coastal_change.wofs.values == -1]     = adjust_color(GREEN[0])
    change.green.values[coastal_change.wofs.values == -1]   = adjust_color(GREEN[1])
    change.blue.values[coastal_change.wofs.values == -1]    = adjust_color(GREEN[2])

    ##Coastal Boundary Visual Raster #############################
    boundary = target.copy(deep = True)
    boundary = boundary
    boundary.red.values[new_coastline.wofs.values == 1]     = adjust_color(BLUE[0])
    boundary.green.values[new_coastline.wofs.values == 1]   = adjust_color(BLUE[1])
    boundary.blue.values[new_coastline.wofs.values == 1]    = adjust_color(BLUE[2])

    boundary.red.values[old_coastline.wofs.values == 1]     = adjust_color(GREEN[0])
    boundary.green.values[old_coastline.wofs.values == 1]   = adjust_color(GREEN[1])
    boundary.blue.values[old_coastline.wofs.values == 1]    = adjust_color(GREEN[2])

    ##WRITE TO TEMPORARY DIR ###############################
    if not os.path.exists(BASE_TEMP_PATH + query.query_id):
        return None

    geo_path = BASE_TEMP_PATH + query.query_id + "/composite_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    boundary_change_path  = BASE_TEMP_PATH + query.query_id + "/boundary_" +  \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    coastal_change_path = BASE_TEMP_PATH + query.query_id + "/change_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"

    print("WRITING::: Target ||" + str(geo_path))
    target.to_netcdf(geo_path)

    print("WRITING::: Coastal Change ||" + str(coastal_change_path))
    change.to_netcdf(coastal_change_path)

    print("WRITING::: Boundary Change ||" + str(boundary_change_path))
    boundary.to_netcdf(boundary_change_path)

    print("Done with chunk: " + str(time_num) + " " + str(chunk_num))
    return [geo_path, coastal_change_path , boundary_change_path]


@worker_process_init.connect
def init_worker(**kwargs):
    """
    Creates an instance of the DataAccessApi worker.
    """

    print("Creating DC instance for worker.")
    global dc
    dc = DataAccessApi()
    if not os.path.exists(BASE_RESULT_PATH):
        os.mkdir(BASE_RESULT_PATH)
        os.chmod(BASE_RESULT_PATH, 0o777)


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """
    Deletes the instance of the DataAccessApi worker.
    """

    print('Closing DC instance for worker.')
    global dc
    dc = None
