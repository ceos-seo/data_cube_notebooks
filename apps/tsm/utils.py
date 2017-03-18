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

from .models import Query, ResultType
from datetime import datetime
from data_cube_ui.models import Area, Satellite
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
    query = Query(
        query_start=datetime.now(),
        query_end=datetime.now(),
        user_id=user_id,
        query_type=post['result_type'],
        latitude_max=post['latitude_max'],
        latitude_min=post['latitude_min'],
        longitude_max=post['longitude_max'],
        longitude_min=post['longitude_min'],
        time_start=start,
        time_end=end,
        platform=post['platform'],
        animated_product=post['animated_product'],
        area_id=post['area_id'])

    query.title = query.get_type_name() + " Background TSM" if 'title' not in post or post['title'] == '' else post[
        'title']
    query.description = "None" if 'description' not in post or post['description'] == '' else post['description']

    query.product = Satellite.objects.get(satellite_id=query.platform).product_prefix + Area.objects.get(
        area_id=query.area_id).area_id
    query.query_id = query.generate_query_id()
    if not Query.objects.filter(query_id=query.query_id).exists():
        query.save()
    return query.query_id
