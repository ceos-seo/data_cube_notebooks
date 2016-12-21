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

from django.shortcuts import render
from django.template import loader, RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

import json
from datetime import datetime, timedelta

from apps.custom_mosaic_tool.models import Result as cm_result, Query as cm_query, Metadata as cm_meta
from apps.water_detection.models import Query as wd_query, Result as wd_result, Metadata as wd_meta
from apps.tsm.models import Query as tsm_query, Result as tsm_result, Metadata as tsm_meta
from apps.fractional_cover.models import Query as fractional_cover_query, Result as fractional_cover_result, Metadata as fractional_cover_meta

from collections import OrderedDict

"""
Class holding all the views for the Task_Manager application in the UI Suite.
"""

def build_headers_dictionary(model):
    """
    Utility method for dynamically building headres for any html table in a Django app.

    Params:
        model: Class from which to pull attributes

    Returns:
        headers_dictionary (dict): Dictionary with all the attributes from the model passed in.
    """

    # List of attributes to filter out.  Note that these should match the attributes of the
    # class being passed in.
    exclusion_list = ['query_id', 'user_id', 'product_type', 'description']

    headers = list()
    headers_dictionary = OrderedDict()
    for field in model._meta.get_fields():
        header = str(field).rsplit('.', 1)[-1]
        if not any(header == exclusion for exclusion in exclusion_list):
            headers.append(header)

    headers_dictionary[model.__class__.__name__] = headers

    return headers_dictionary


def format_headers(unformatted_dict):
    """
    Utility method for formatting a dictionary of headers.

    Params:
        unformatted_dict (dict): Unformatted dictionary being submitted for formatting.

    Returns:
        formatted_headers (dict): Dictionary that has been camel cased with spaces replacing
        underscores("_")
    """

    # Split and title the headers_dicionary for better display.
    formatted_headers = list()

    for field in unformatted_dict['ModelBase']:
        formatted_headers.append(field.replace('_', " ").title())

    return formatted_headers


@login_required
def get_task_manager(request, app_id):
    """
    View method for returning and rending the HTML for the task manager in the application.

    **Context**

    ``data_dictionary``
        List of all information for every Query that will be shown on the screen.
    ``formatted_headers_dictionary``
        List of headers associated with the Query that will be use to build the table.

    **Template**

    :template:`task_manager/APP_NAME`
    """

    # Lists to be returned to the html for display.
    headers_dictionary = OrderedDict()
    data_dictionary = OrderedDict()

    queries = cm_query if app_id == "custom_mosaic_tool" else wd_query if app_id == "water_detection" else fractional_cover_query if app_id == "fractional_cover" else tsm_query

    headers_dictionary = build_headers_dictionary(queries)
    for query in queries.objects.all().order_by('-query_start')[:100]:
        data = list()
        for v in headers_dictionary['ModelBase']:
            data.append(str(query.__dict__[v]))
            data_dictionary[query] = data

    formatted_headers_dictionary = OrderedDict()
    formatted_headers_dictionary['Query'] = format_headers(headers_dictionary)

    # Context being built up.
    context = {
        'data_dictionary': data_dictionary,  # Data to match headerss.
        # Formatted headers for easier viewing.
        'formatted_headers_dictionary': formatted_headers_dictionary,
        'application_id': app_id,
    }

    return render(request, 'task_manager.html', context)


@login_required
def get_query_details(request, app_id, requested_query_id):
    """
    Returns the rendered html with appropriate data for a Query and its Metadata and Results.
    Requires an ID to be passed from the previous page.

    **Context**

    ``query``
        The specific query for which details are desired.
    ``metadata``
        The metadata model for a specific query.
    ``result``
        The result model for a specifi query.

    **Template**

    :template:`custom_mosaic_tool/query_details.html`
    """

    queries = cm_query if app_id == "custom_mosaic_tool" else wd_query if app_id == "water_detection" else fractional_cover_query if app_id == "fractional_cover" else tsm_query
    metas = cm_meta if app_id == "custom_mosaic_tool" else wd_meta if app_id == "water_detection" else fractional_cover_meta if app_id == "fractional_cover" else tsm_meta
    results = cm_result if app_id == "custom_mosaic_tool" else wd_result if app_id == "water_detection" else fractional_cover_result if app_id == "fractional_cover" else tsm_result
    template = 'custom_mosaic_tool/query_details.html' if app_id == "custom_mosaic_tool" else 'water_detection/query_details.html' if app_id == "water_detection" else 'fractional_cover/query_details.html' if app_id == "fractional_cover" else 'tsm/query_details.html'

    query = queries.objects.get(id=requested_query_id)
    metadata = metas.objects.get(query_id=query.query_id)
    result = results.objects.get(query_id=query.query_id)

    context = {
        'query': query,
        'metadata': metadata,
        'result': result,
    }

    return render(request, template, context)
