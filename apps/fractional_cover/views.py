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

from .models import Result, Query, Metadata
from .forms import DataSelectForm
from data_cube_ui.forms import GeospatialForm
from .tasks import create_fractional_cover
from data_cube_ui.models import Satellite, Area, Application

from .utils import create_query_from_post

from collections import OrderedDict

"""
Class holding all the views for the fractional_cover app in the project.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by: MAP
# Last modified date:

@login_required
def fractional_cover(request, area_id):
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

    :template:`fractional_cover/map_tool.html`
    """

    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    area = Area.objects.get(area_id=area_id)
    app = Application.objects.get(application_id="fractional_cover")
    satellites = area.satellites.all() & app.satellites.all() #Satellite.objects.all().order_by('satellite_id')
    forms = {}
    for satellite in satellites:
        forms[satellite.satellite_id] = {'Data Selection': DataSelectForm(auto_id=satellite.satellite_id + "_%s"),
                                         'Geospatial Bounds': GeospatialForm(satellite=satellite, auto_id=satellite.satellite_id + "_%s") }
    running_queries = Query.objects.filter(user_id=user_id, area_id=area_id, complete=False)

    context = {
        'tool_name': 'fractional_cover',
        'info_panel': 'fractional_cover/info_panel.html',
        'satellites': satellites,
        'forms': forms,
        'running_queries': running_queries,
        'area': area
    }

    return render(request, 'map_tool.html', context)

@login_required
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
            create_fractional_cover.delay(query_id, user_id)
            response.update(model_to_dict(Query.objects.filter(query_id=query_id, user_id=user_id)[0]))
        except:
            response['msg'] = "ERROR"
            raise
        return JsonResponse(response)
    else:
        return JsonResponse({'msg': "ERROR"})

@login_required
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
            #Get the query that this is a derivation of, clone it by setting pk to none.
            query = Query.objects.filter(query_id=request.POST['query_id'], user_id=user_id)[0]
            query.pk = None
            query.time_start = datetime.strptime(request.POST['date'], '%m/%d/%Y')
            query.time_end = query.time_start + timedelta(days=1)
            query.complete = False
            query.title = "Single acquisition for " + request.POST['date']
            query.query_id = query.generate_query_id()
            query.save();
            create_fractional_cover.delay(query.query_id, user_id)
            response.update(model_to_dict(query))
        except:
            response['msg'] = "ERROR"
        return JsonResponse(response)
    else:
        return JsonResponse({'msg': "ERROR"})

@login_required
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
            query = Query.objects.get(query_id=request.POST['query_id'], user_id=user_id)
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
    If the result returns ok, then post a result. Response is a json obj containing a msg and result.    the result can either be the data or an obj containing the total scenes/progress.

    **Context**

    **Template**
    """

    if request.method == 'POST':
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
                response['error_msg'] = result.result_path
                # get rid of the offending results, queries, metadatas.
                Query.objects.filter(query_id=result.query_id).delete()
                Metadata.objects.filter(query_id=result.query_id).delete()
                result.delete()
            elif result.status == "OK":
                response['msg'] = "OK"
                response.update(model_to_dict(result))
                # since there is a result, update all the currently running identical queries with complete=true;
                Query.objects.filter(query_id=result.query_id).update(complete=True)
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

    :template:`fractional_cover/query_history`
    """
    user_id = 0
    if request.user.is_authenticated():
        user_id = request.user.username
    history = Query.objects.filter(
        user_id=user_id, area_id=area_id).order_by('-query_start')[:10]
    context = {
        'query_history': history,
    }
    return render(request, 'fractional_cover/query_history.html', context)


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

    :template:`fractional_cover/results_list.html`

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
        return render(request, 'fractional_cover/results_list.html', context)
    return HttpResponse("Invalid Request.")

@login_required
def get_output_list(request, area_id):
    """
    Loads the output of the given query for a requested ID.

    **Context**

    ``data``
        The information to be returned to the user.

    **Template**

    :template: `fractional_cover/output_list.html`
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
        return render(request, 'fractional_cover/output_list.html', context)
    return HttpResponse("Invalid Request.")
