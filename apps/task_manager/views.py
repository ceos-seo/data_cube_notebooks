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
from django.apps import apps


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

    app_id_camel_case = "".join(x.title() for x in app_id.split('_'))

    task_model = apps.get_model(".".join([app_id, app_id_camel_case + "Task"]))
    tasks = task_model.objects.filter(complete=True).exclude(status="ERROR")

    # use the unique fields to form header.
    header_fields = task_model._meta.unique_together[0]
    header_fields = map(lambda x: " ".join(part.title() for part in x.split("_")), header_fields)

    # Context being built up.
    context = {
        'header_fields': header_fields,
        'tasks': tasks,
        'application_id': app_id,
    }

    return render(request, 'task_manager/task_manager.html', context)
