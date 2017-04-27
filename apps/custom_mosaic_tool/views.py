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
from django.forms.models import model_to_dict

import json
from datetime import datetime, timedelta

from .models import ResultType, Result, Query, Metadata
from data_cube_ui.models import Satellite, Area, Application
from data_cube_ui.forms import GeospatialForm
from .forms import DataSelectForm
from .tasks import create_cloudfree_mosaic

from collections import OrderedDict

from apps.dc_algorithm.views import (ToolView, SubmitNewRequest, GetTaskResult, SubmitNewSubsetRequest, CancelRequest)


class CustomMosaicTool(ToolView):
    """Creates the main view for the custom mosaic tool by extending the ToolView class

    Extends the ToolView abstract class - required attributes are the tool_name and the
    generate_form_dict function.

    See the dc_algorithm.views docstring for more details.
    """

    tool_name = 'custom_mosaic_tool'
    task_model_name = 'CustomMosaicTask'

    def generate_form_dict(self, satellites):
        forms = {}
        for satellite in satellites:
            forms[satellite.satellite_id] = {
                'Data Selection':
                DataSelectForm(satellite_id=satellite.satellite_id, auto_id=satellite.satellite_id + "_%s"),
                'Geospatial Bounds':
                GeospatialForm(satellite=satellite, auto_id=satellite.satellite_id + "_%s")
            }
        return forms


class SubmitNewRequest(SubmitNewRequest):
    """
    Submit new request REST API Endpoint
    Extends the SubmitNewRequest abstract class - required attributes are the tool_name,
    task_model_name, and celery_task_func.

    Note:
        celery_task_func should be callable with .delay() and take a single argument of a TaskModel pk.

    See the dc_algorithm.views docstrings for more information.
    """
    tool_name = 'custom_mosaic_tool'
    task_model_name = 'CustomMosaicTask'
    celery_task_func = create_cloudfree_mosaic


class GetTaskResult(GetTaskResult):
    """
    Get task result REST API endpoint
    Extends the GetTaskResult abstract class, required attributes are the tool_name
    and task_model_name

    See the dc_algorithm.views docstrings for more information.
    """
    tool_name = 'custom_mosaic_tool'
    task_model_name = 'CustomMosaicTask'


class SubmitNewSubsetRequest(SubmitNewSubsetRequest):
    """
    Submit new subset request REST API endpoint
    Extends the SubmitNewSubsetRequest abstract class, required attributes are
    the tool_name, task_model_name, celery_task_func, and task_model_update_func.

    See the dc_algorithm.views docstrings for more information.
    """
    tool_name = 'custom_mosaic_tool'
    task_model_name = 'CustomMosaicTask'
    celery_task_func = create_cloudfree_mosaic

    def task_model_update_func(task_model, **kwargs):
        """
        Basic funct that updates a task model with kwargs. In this case only the date
        needs to be changed, and results reset.
        """
        task_model.time_start = datetime.strptime(kwargs.get('date'), '%m/%d/%Y')
        task_model.time_end = query.time_start + timedelta(days=1)
        task_model.complete = False
        task_model.scenes_processed = 0
        task_model.total_scenes = 0
        task_model.title = "Single acquisition for " + request.POST['date']
        return task_model


class CancelRequest(CancelRequest):
    tool_name = 'custom_mosaic_tool'
    task_model_name = 'CustomMosaicTask'
    pass


@login_required
def get_query_history(request, area_id):
    """
    Gets a formatted view displaying a user's task history. Used in the custom mosaic tool view.
    No post data required. The user's authentication provides username, returns a view w/
    context including the last n query objects.

    **Context**

    ``query_history``
        List of queries ran ordered by query_start ascending.  Currently only first 10 rows returned

    **Template**

    :template:`custom_mosaic_tool/query_history`
    """
    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    history = Query.objects.filter(user_id=user_id, area_id=area_id, complete=True).order_by('-query_start')[:10]
    context = {
        'query_history': history,
    }
    return render(request, 'map_tool/custom_mosaic_tool/query_history.html', context)


@login_required
def get_results_list(request, area_id):
    """
    Loads the results list from a list of query ids. Error handling: N/a. getlist always returns a
    list, so even if its a bad request it'll return an empty list of queries and metadatas.

    **Context**

    ``queries``
        The queries found given the query_ids[] list passed in through the POST
    ``metadata_entries``
        The metadata objects found for each query

    **Template**

    :template:`custom_mosaic_tool/results_list.html`

    """

    if request.method == 'POST':
        query_ids = request.POST.getlist('query_ids[]')
        queries = []
        metadata_entries = []
        for query_id in query_ids:
            queries.append(Query.objects.filter(query_id=query_id).order_by('-query_start')[0])
            metadata_entries.append(Metadata.objects.filter(query_id=query_id)[0])

        context = {'queries': queries, 'metadata_entries': metadata_entries}
        return render(request, 'map_tool/custom_mosaic_tool/results_list.html', context)
    return HttpResponse("Invalid Request.")


@login_required
def get_output_list(request, area_id):
    """
    Loads the output of the given query for a requested ID.

    **Context**

    ``data``
        The information to be returned to the user.

    **Template**

    :template: `custom_mosaic_tool/output_list.html`
    """

    if request.method == 'POST':
        query_ids = request.POST.getlist('query_ids[]')
        #queries = []
        #metadata_entries = []
        data = {}
        for query_id in query_ids:
            # queries.append(Query.objects.filter(query_id=query_id)[0])
            # metadata_entries.append(Metadata.objects.filter(query_id=query_id)[0])
            data[Query.objects.filter(query_id=query_id).order_by('-query_start')[0]] = Metadata.objects.filter(
                query_id=query_id)[0]

        context = {
            #'queries': queries,
            #'metadata_entries': metadata_entries
            'data': data
        }
        return render(request, 'map_tool/custom_mosaic_tool/output_list.html', context)
    return HttpResponse("Invalid Request.")
