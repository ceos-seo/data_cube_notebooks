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

from .models import Query
from data_cube_ui.models import Area, Satellite
from datetime import datetime
from utils.dc_utilities import split_task

import scipy.ndimage.filters as conv
import numpy as np

"""
Utility class designed to take repeated functional code and abstract out for reuse through
application.
"""

# Author: OW
# Creation date: 2017-02-14

def coastline_classification(dataset, water_band = 'wofs'):
    kern = np.array([[1,1,1],[1,0,1],[1,1,1]])
    convolved = conv.convolve(dataset[water_band], kern, mode ='constant')
    ds = dataset.where(convolved>0)
    ds = ds.where(convolved<5)
    ds.wofs.values[~np.isnan(ds.wofs.values)] = 1
    ds.wofs.values[ np.isnan(ds.wofs.values)] = 0
    return ds

def adjust_color(color, scale = 4096):
    return int(float(color * scale)/255.0)

def darken_color(color, scale = 0.8):
    return [int(float(x * scale)) for x in color]

def create_query_from_post(user_id, post):
    """
    Takes post data from a request with a user id and creates a model.
    TODO: use form validation rather than doing it this way.

    Args:
        user_id (string): Id of the user requesting the creation of the query.
        post (HttpPost): A post that contains a variety of information regarding how to construct the
                         query

    Returns:
        query_id (string): The ID of the query that has been created.
    """
    # hardcoded product, user id. Will be changed.
    query = Query(query_start=datetime.now(),
                  query_end=datetime.now(), user_id=user_id,
                  latitude_max=post['latitude_max'],
                  latitude_min=post['latitude_min'],
                  longitude_max=post['longitude_max'],
                  longitude_min=post['longitude_min'],
                  time_start=post['old'],
                  time_end=post['new'],
                  animation_setting = post['animation_setting'],
                  platform=post['platform'],
                  area_id=post['area_id'],
                  )

    query.title = "Coastal Change Products" if 'title' not in post or post['title'] == '' else post['title']
    query.description = "None" if 'description' not in post or post['description'] == '' else post['description']

    query.product = Satellite.objects.get(satellite_id=query.platform).product_prefix + Area.objects.get(area_id=query.area_id).area_id
    query.query_id = query.generate_query_id()
    if not Query.objects.filter(query_id=query.query_id).exists():
        query.save()
    return query.query_id

def group_by_year(list_of_datetimes):
    groupedByYear={}
    for date in list_of_datetimes:
        if date.year in groupedByYear:
            groupedByYear[date.year].append(date)
        else:
            groupedByYear[date.year]=[date]
    return groupedByYear

def dict_to_iterable(the_dict):
    for key in the_dict.keys():
        yield the_dict[key]

def nearest_key(the_dict, key):
    for i in range( key , max(the_dict.keys())):
        if i in the_dict.keys():
            return i

def split_task_by_year(resolution=0.000269,
    latitude=None,
    longitude=None,
    acquisitions=None,
    geo_chunk_size=None,
    reverse_time=False):

    lat_range, lon_range, __ = split_task(resolution=resolution,
        latitude=latitude,
        longitude=longitude,
        acquisitions=acquisitions,
        geo_chunk_size=geo_chunk_size,
        time_chunks=None,
        reverse_time=reverse_time)

    times = list( dict_to_iterable( group_by_year( acquisitions )))
    times = list(reversed(sorted(times)))
    return lat_range,lon_range,times

def split_by_year_and_append_stationary_year(resolution=0.000269,
        latitude=None,
        longitude=None,
        acquisitions=None,
        geo_chunk_size=None,
        reverse_time=False,
        year_stationary = None):

    lat_range,lon_range, yearly_time_ranges = split_task_by_year(resolution=resolution,
        latitude=latitude,
        longitude=longitude,
        acquisitions=acquisitions,
        geo_chunk_size=geo_chunk_size,
        reverse_time=reverse_time)

    year_dict = group_by_year(acquisitions)
    key = nearest_key(year_dict, year_stationary)
    augmented_time_ranges = [year + year_dict[key] for year in yearly_time_ranges if year[0].year != key]
    return lat_range, lon_range, augmented_time_ranges
