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
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.forms.models import model_to_dict
from django.views import View
from django.apps import apps

from .models import Application, Satellite, Area


class ToolClass:
    """Base class for all Tool related classes

    Contains common functions for tool related views, e.g. getting tool names etc.
    Attributes defined here will be required for all inheriting classes and will raise
    NotImplementedErrors for required fields.

    Attributes:
        tool_name: label for the tool that the class is used in.
            e.g. custom_mosaic_tool, water_detection, etc.

    """

    tool_name = None
    task_model_name = None

    def _get_tool_name(self):
        """Get the tool_name property

        Meant to implement a general NotImplementedError for required properties

        Raises:
            NotImplementedError in the case of tool_name not being defined

        Returns:
            The value of tool_name.

        """
        if self.tool_name is None:
            raise NotImplementedError(
                "You must specify a tool_name in classes that inherit ToolClass. See the ToolClass docstring for more details."
            )
        return self.tool_name

    def _get_task_model_name(self):
        """Gets the task model name and raises an error if the name is not defined.

        Checks if task_model_name property is None, otherwise return the model name.
        The task_model_name must be a string that can be used to identify your main task
        model. e.g. if your task model is CaTask, you can set task_model_name to
        'catask', 'CaTask', etc.

        """
        if self.task_model_name is None:
            raise NotImplementedError(
                "You must specify a task_model_name in classes that inherit SubmitNewRequest. See the SubmitNewRequest and dc_algorithm.models docstring for more details."
            )
        return self.task_model_name

    def _get_tool_model(self, model):
        """Get a model from the subclassing tool

        Used to get a model from the specific tool - e.g. if tool
        'custom_mosaic_tool' subclasses this, you can get
        custom_mosaic_tool.Query by calling self._get_tool_model('query')

        Returns:
            Model class requested by 'model'
        """

        return apps.get_model('.'.join([self._get_tool_name(), model]))


class ToolView(View, ToolClass):
    """General tool view responsible for displaying the map_tool template

    The generic ToolView class is used to display the fullscreen algorithm application.
    Only the get function is defined, disallowing post/put/etc. Required overrides are
    attributes or functions that -must- be defined in any subclass. This class is meant to
    be used as a base rather than a standalone module.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting the toolview without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        generate_form_dict(QueryDict(Satellite)): Generates a dictionary of forms to render on the page.
            Abstract method, so this will need to be implemented in each class that inherits from this.

    """

    @method_decorator(login_required)
    def get(self, request, area_id):
        """Get the main tool view page using the map_tool template

        Loads the map_tool template with all associated context parameters. Login is required
        for this view, so the userid/username is grabbed from the request without first authenticating.
        Performs an intersection between the area and app satellites to determine what should be displayed.
        Generates forms for each of the satellites to be displayed and lists running queries.

        Args:
            area_id: Area.area_id corresponding to the requested area.

        Context:
            tool_name: tool name used to identify this app - used to form urls
            satellites: Satellite querydict containing all satellites for this app and area.
            forms: form dict created by generate_form_dict, keyed by satellite containing forms to be rendered.
            running_queries: queries registered to this user running over this area that have not yet been completed
            area: requested Area model instance
            application: requested Application model instance

        Returns:
            A rendered HTML response based on the map_tool.html template with the context.
        """

        user_id = request.user.username
        tool_name = self._get_tool_name()
        area = Area.objects.get(area_id=area_id)
        app = Application.objects.get(application_id=tool_name)
        satellites = area.satellites.all() & app.satellites.all()

        forms = self.generate_form_dict(satellites)

        #running_queries = self._get_tool_model(self._get_task_model_name()).objects.filter(
        #    user_id=user_id, area_id=area_id, complete=False)

        context = {
            'tool_name': tool_name,
            'satellites': satellites,
            'forms': forms,
            'running_queries': None,
            'area': area,
            'application': app,
        }

        return render(request, 'map_tool/map_tool.html', context)

    def generate_form_dict(satellites):
        """Generate a dictionary of forms keyed by satellite for rendering

        Forms are generated for each satellite and dynamically hidden and shown by the UI.
        dictionary should be in the format of:
        {
        satellite.satellite_id: {
            'Section title': form(),
            'Section title': form() ...
            }
        satellite.satellite_id: {
            'Section title': form(),
            'Section title': form() ...
            }
        }

        This function is must be provided by the inheriting class, the below only exists as an example.

        Raises:
            NotImplementedError in the case of generate_form_dict not being defined by the child class.

        Args:
            satellites: QueryDict of Satellite models that forms will need to be generated over.

        Returns
            Dictionary containing all forms and labels for each satellite.

        """
        """
        forms = {}
        for satellite in satellites:
            forms[satellite.satellite_id] = {
                'Geospatial Bounds': GeospatialForm(satellite=satellite, auto_id=satellite.satellite_id + "_%s")
            }
        return forms
        """
        raise NotImplementedError(
            "You must define a generate_form_dict(satellites) function in child classes of ToolInfo. See the ToolInfo.generate_form_dict docstring for more details."
        )


class SubmitNewRequest(View, ToolClass):
    """Submit a new request for processing using a query created with form data

    REST API Endpoint for submitting a new request for processing. This is a POST only view,
    so only the post function is defined. Form data is used to create a Query model which is
    then submitted for processing via celery.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting the toolview without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        celery_task_func: A celery task called with .delay() with the only parameter being the pk of a task model
        task_model_name: Name of the model that represents your task - see models.Task for more information

    """

    celery_task_func = None

    @method_decorator(login_required)
    def post(self, request):
        """Generate a query object and start a celery task using POST form data

        Decorated as login_required so the username is fetched without checking.
        A full form set is submitted in one POST request including all of the forms
        associated with a satellite. This formset is generated using the
        ToolView.generate_form_dict function and should be the forms for a single satellite.

        Args:
            POST data including a full form set described above

        Returns:
            JsonResponse containing:
                A 'msg' with either OK or ERROR
                A Json representation of the query object created from form data.
        """

        user_id = request.user.id

        response = {'msg': "OK"}
        try:
            task_model = self._get_tool_model(self._get_task_model_name())
            task, new_task = task_model._get_or_create_query_from_post(self._post_data_to_dict(request.POST))
            #associate task w/ history
            history_model, __ = self._get_tool_model('userhistory').objects.get_or_create(
                user_id=user_id, task_id=task.pk)
            if new_task:
                self._get_celery_task_func().delay(task.pk)
            response.update(model_to_dict(task))
        except:
            response['msg'] = "ERROR"
            raise
        return JsonResponse(response)

    def _get_celery_task_func(self):
        """Gets the celery task function and raises an error if it is not defined.

        Checks if celery_task_func property is None, otherwise return the function.
        The celery_task_func must be a function callable with .delay() with the only
        parameters being the pk of a task model.

        """
        if self.celery_task_func is None:
            raise NotImplementedError(
                "You must specify a celery_task_func in classes that inherit SubmitNewRequest. See the SubmitNewRequest docstring for more details."
            )
        return self.celery_task_func

    def _post_data_to_dict(self, post):
        """Convert a QueryDict object from POST data into usable Python Dicts

        POST data is returned in a QueryDict object that handles things like json
        objects, lists, etc. in a strange way. This maps them back to a usable python
        dict.

        Args:
            post: POST data from request.POST

        Returns:
            Python dict representation of the POST data
        """

        return {k: v[0] if len(v) == 1 else v for k, v in post.lists()}
