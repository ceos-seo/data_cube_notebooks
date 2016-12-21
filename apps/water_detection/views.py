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

from .models import ResultType, Result, Query, Metadata
from data_cube_ui.models import Satellite, Area, AnimationType
from .forms import DataSelectForm, GeospatialForm
from .tasks import perform_water_analysis
from .utils import create_query_from_post

from collections import OrderedDict

"""
Class holding all the views for the water_detection app in the project.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by: MAP
# Last modified date:


@login_required
def water_detection(request, area_id):
    """
    Loads the custom mosaic tool page. Includes the relevant forms/satellites, as well as running
    queries for the user. A form is created for each satellite based on the db contents for any
    given satellite.

    **Context**

    ``satellites``
        List of available satellites to choose from for submission
    ``forms``
        The forms to be loaded to allow for user input.
    ``running_queries``
        A list of all tasks currently running.

    ``area``
    The desired area that was selected from the previous screen.

    **Template**

    :template:`water_detection/map_tool.html`
    """

    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    satellites = Satellite.objects.all().order_by('satellite_id')
    forms = {}
    area = Area.objects.get(area_id=area_id)
    for satellite in satellites:
        forms[satellite.satellite_id] = {'Output Image Characteristics': DataSelectForm(
            satellite_id=satellite.satellite_id, auto_id=satellite.satellite_id + "_%s"), 'Geospatial Bounds': GeospatialForm(area=area, auto_id=satellite.satellite_id + "_%s") }
        # gets a flat list of the bands/result types and populates the choices.
    # will later be populated after we have authentication working.
    running_queries = Query.objects.filter(
        user_id=user_id, area_id=area_id, complete=False)

    context = {
        'tool_name': 'water_detection',
        'info_panel': 'water_detection/info_panel.html',
        'satellites': satellites,
        'forms': forms,
        'running_queries': running_queries,
        'area': area
    }

    return render(request, 'map_tool.html', context)


def submit_new_request(request):
    """
    Submit a new request using post data. A query model is created with the relevant information and
    user id, then the data task is started. The response is a json obj. containing the query id.

    **Context**

    **Template**
    """

    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    if request.method == 'POST':
        response = {}
        response['msg'] = "OK"
        try:
            query_id = create_query_from_post(user_id, request.POST)
            perform_water_analysis.delay(query_id, user_id)
            response['request_id'] = query_id
        except:
            response['msg'] = "ERROR"
            raise
        return JsonResponse(response)
    else:
        return JsonResponse({'msg': "ERROR"})
    return None


def submit_new_single_request(request):
    """
    Submit a new requset for a single scene from an existing query. Clones the existing query and
    updates the date fields for a single day.

    **Context**

    **Template**
    """

    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    if request.method == 'POST':
        response = {}
        response['msg'] = "OK"
        try:
            # Get the query that this is a derivation of, clone it by setting
            # pk to none.
            query = Query.objects.filter(
                query_id=request.POST['query_id'], user_id=user_id)[0]
            query.pk = None
            query.time_start = datetime.strptime(
                request.POST['date'], '%m/%d/%Y')
            query.time_end = query.time_start + timedelta(days=1)
            query.complete = False
            query.title = "Single scene analysis " + request.POST['date']
            query.query_id = query.generate_query_id()
            query.save()
            perform_water_analysis.delay(query.query_id, user_id)
            response['request_id'] = query.query_id
        except:
            response['msg'] = "ERROR"
        return JsonResponse(response)
    else:
        return JsonResponse({'msg': "ERROR"})


def cancel_request(request):
    """
    Cancel a running task by id. Post data includes a query id to be cancelled. The result model is
    obtained, and if it is still running then the job is cancelled. If it is too late, then the job
    will proceed until completion.

    **Context**

    **Template**
    """

    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    if request.method == 'POST':
        response = {}
        response['msg'] = "OK"
        try:
            query = Query.objects.get(query_id=request.POST[
                                      'query_id'], user_id=user_id)
            result = Result.objects.get(query_id=request.POST['query_id'])
            if result.status == "WAIT" and query.complete == False:
                result.status = "CANCEL"
                result.save()
        except:
            response['msg'] = "ERROR"
        return JsonResponse(response)
    else:
        return JsonResponse({'msg': "ERROR"})


@login_required
def get_result(request):
    """
    Gets a result by its query id. If the result does not yet exist in the db or there are no errors
    or "ok" signals, wait. If the result has errored in some way, all offending models are removed.
    If the result returns ok, then post a result. Response is a json obj containing a msg and result.
    the result can either be the data or an obj containing the total scenes/progress.
    The result object is passed directly into the queries[query_id] object on the front end.
    This means that any data you pass into the response will be available from the templates.

    **Context**

    **Template**
    """

    if request.method == 'POST':
        user_id = 0
        if request.user.is_authenticated():
            user_id = request.user.username
        response = {}
        try:
            result = Result.objects.get(query_id=request.POST['query_id'])
        except Result.DoesNotExist:
            result = None
            response['msg'] = "WAIT"
        except:
            result = None
            response['msg'] = "ERROR"
        if result:
            if result.status == "ERROR":
                response['msg'] = "ERROR"
                response['error_msg'] = result.data_path
                # get rid of the offending results, queries, metadatas.
                Query.objects.filter(query_id=result.query_id).delete()
                Metadata.objects.filter(query_id=result.query_id).delete()
                result.delete()
            elif result.status == "OK":
                response['msg'] = "OK"
                response['result'] = {'data_url': result.data_path, 'nc_url': result.data_netcdf_path, 'image_url': getattr(result, 'water_percentage_path'), 'water_observations_url': getattr(result, 'water_observations_path'), 'clear_observations_url': getattr(result, 'clear_observations_path'), 'min_lat': result.latitude_min, 'max_lat': result.latitude_max,
                                      'water_animation_url': result.water_animation_path, 'min_lon': result.longitude_min, 'max_lon': result.longitude_max, 'total_scenes': result.total_scenes, 'scenes_processed': result.scenes_processed}
                # since there is a result, update all the currently running
                # identical queries with complete=true;
                Query.objects.filter(
                    query_id=result.query_id).update(complete=True)
            else:
                response['msg'] = "WAIT"
                response['result'] = {
                    'total_scenes': result.total_scenes, 'scenes_processed': result.scenes_processed}
        return JsonResponse(response)
    return JsonResponse({'msg': "ERROR"})


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

    :template:`water_detection/query_history`
    """
    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    history = Query.objects.filter(
        user_id=user_id, area_id=area_id).order_by('-query_start')[:10]
    context = {
        'query_history': history,
    }
    return render(request, 'water_detection/query_history.html', context)


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

    :template:`water_detection/results_list.html`

    """

    if request.method == 'POST':
        query_ids = request.POST.getlist('query_ids[]')
        queries = []
        metadata_entries = []
        for query_id in query_ids:
            queries.append(Query.objects.filter(query_id=query_id).order_by('-query_start')[0])
            metadata_entries.append(
                Metadata.objects.filter(query_id=query_id)[0])

        context = {
            'queries': queries,
            'metadata_entries': metadata_entries
        }
        return render(request, 'water_detection/results_list.html', context)
    return HttpResponse("Invalid Request.")


@login_required
def get_output_list(request, area_id):
    """
    Loads the output of the given query for a requested ID.

    **Context**

    ``data``
        The information to be returned to the user.

    **Template**

    :template: `water_detection/output_list.html`
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
        return render(request, 'water_detection/output_list.html', context)
    return HttpResponse("Invalid Request.")
