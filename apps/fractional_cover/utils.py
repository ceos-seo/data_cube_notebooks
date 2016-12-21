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
from data_cube_ui.models import Area
from datetime import datetime

"""
Utility class designed to take repeated functional code and abstract out for reuse through
application.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:


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

    start = datetime.strptime(post['time_start'], '%m/%d/%Y')
    end = datetime.strptime(post['time_end'], '%m/%d/%Y')

    # hardcoded product, user id. Will be changed.
    query = Query(query_start=datetime.now(), query_end=datetime.now(), user_id=user_id, latitude_max=post[
        'latitude_max'], latitude_min=post['latitude_min'],
        longitude_max=post['longitude_max'], longitude_min=post[
        'longitude_min'],
        time_start=start, time_end=end, platform=post[
        'platform'], compositor=post['compositor_selection'])
    if 'title' not in post or post['title'] == '':
        query.title = "Fractional Cover"
    else:
        query.title = post['title']
    if 'description' not in post or post['description'] == '':
        query.description = "None"
    else:
        query.description = post['description']

    query.area_id = post['area_id']
    query.product = Area.objects.get(area_id=query.area_id).area_product
    query.query_id = query.generate_query_id()
    query.complete = False
    query.save()
    return query.query_id


# pulled from peterbe.com since there were benchmarks listed.
# removes duplicates from python lists.
def uniquify_list(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def update_model_bounds_with_dataset(model_list, dataset):
    for model in model_list:
        model.latitude_max = dataset.latitude.values[0]
        model.latitude_min = dataset.latitude.values[-1]
        model.longitude_max = dataset.longitude.values[-1]
        model.longitude_min = dataset.longitude.values[0]
        model.save()

def map_ranges(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    import numpy as np
    # Convert the left range into a 0-1 range (float)
    valueScaled = (value.astype(np.float64) - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)
