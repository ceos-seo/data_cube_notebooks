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


def count_not_nan(np_array):
    return np.count_nonzero(~np.isnan(np_array))


def count_nan(np_array):
    return np.count_nonzero(np.isnan(np_array))


def count_pixels(array, element):
    return np.count_nonzero(array == element)


def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy.

    See more at:
        http://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression

    """
    z = x.copy()
    z.update(y)
    return z


def extract_landsat_scene_metadata(landsat_xarray, no_data=-9999):
    times = (time for time in landsat_xarray.time.values)
    scenes = (landsat_xarray.sel(time=time) for time in times)

    metadata = {"scene": {}}

    for number, scene in enumerate(scenes):
        total_pixels, clear_pixels, clear_percent = [-1] * 3

        date = n64_to_datetime(scene.time.values)

        id = date
        total_pixels = count_not_nan(scene.red.values)
        clear_pixels = count_not_nan(scene.where((scene.cf_mask < 2) & (scene >= 0)).red.values)
        clear_percent = (float(clear_pixels) / float(total_pixels)) * 100

        metadata['scene'][id] = {
            "total_pixels": total_pixels,
            "clear_pixels": clear_pixels,
            "clear_percent": clear_percent,
            'date': date
        }

    return metadata


def extract_coastal_change_metadata(wofs_difference_xarray, no_data=-9999):

    metadata = {"coastal_change": {}}

    sea_converted = count_pixels(wofs_difference_xarray.wofs_change.values, -1)
    land_converted = count_pixels(wofs_difference_xarray.wofs_change.values, 1)

    metadata['coastal_change'] = {
        "sea_converted": sea_converted,
        "land_converted": land_converted,
    }

    return metadata


def count_nans(dataset, band=None):
    np.count_nonzero(~np.isnan(data))


def adjust_color(color, scale=4096):
    return int(float(color * scale) / 255.0)


def darken_color(color, scale=0.8):
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
    query = Query(
        query_start=datetime.now(),
        query_end=datetime.now(),
        user_id=user_id,
        latitude_max=post['latitude_max'],
        latitude_min=post['latitude_min'],
        longitude_max=post['longitude_max'],
        longitude_min=post['longitude_min'],
        time_start=post['old'],
        time_end=post['new'],
        animated_product=post['animated_product'],
        platform=post['platform'],
        area_id=post['area_id'],)

    query.title = "Coastal Change Products" if 'title' not in post or post['title'] == '' else post['title']
    query.description = "None" if 'description' not in post or post['description'] == '' else post['description']

    query.product = Satellite.objects.get(satellite_id=query.platform).product_prefix + Area.objects.get(
        area_id=query.area_id).area_id
    query.query_id = query.generate_query_id()
    if not Query.objects.filter(query_id=query.query_id).exists():
        query.save()
    return query.query_id


def group_by_year(list_of_datetimes):
    grouped_by_year = {}
    for date in list_of_datetimes:
        if date.year in grouped_by_year:
            grouped_by_year[date.year].append(date)
        else:
            grouped_by_year[date.year] = [date]
    return grouped_by_year


def dict_to_iterable(the_dict):
    for key in the_dict.keys():
        yield the_dict[key]


def split_task_by_year(resolution=0.000269,
                       latitude=None,
                       longitude=None,
                       acquisitions=None,
                       geo_chunk_size=None,
                       reverse_time=False):
    '''
        Along with Lat-Lon Ranges, this function returns a list of lists to be used for time chunking.
        The sublists contain acquisition dates for a given year.
        The sublists are sorted such that the most recent year comes first in the list

        IE.

        [[
        datetime.datetime(2016, 1, 8, 10, 11, 2),
        datetime.datetime(2016, 1, 24, 10, 11, 15),
        datetime.datetime(2016, 2, 9, 10, 11, 22)
        ],[
        datetime.datetime(2015, 1, 5, 10, 8, 3),
        datetime.datetime(2015, 1, 21, 10, 8, 4)
        ],[
        datetime.datetime(2014, 1, 2, 10, 5, 57)
        ]]

    '''

    lat_range, lon_range, times = split_task(
        resolution=resolution,
        latitude=latitude,
        longitude=longitude,
        acquisitions=acquisitions,
        geo_chunk_size=geo_chunk_size,
        time_chunks=None,
        reverse_time=reverse_time)

    times = list(dict_to_iterable(group_by_year(times[0])))
    times = list(reversed(sorted(times)))

    return lat_range, lon_range, times


def year_in_list_of_acquisitions(acquisitions, year):
    for a in acquisitions:
        if a.year == year:
            return True
    return False
