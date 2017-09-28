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
        """Get the task_model_name property

        The task model name must be usable for querying for a model with apps.get_model.
        Meant to implement a general NotImplementedError for required properties

        Raises:
            NotImplementedError in the case of task_model_name not being defined

        Returns:
            The value of task_model_name.

        """
        if self.task_model_name is None:
            raise NotImplementedError(
                "You must specify a task_model_name in classes that inherit ToolClass. See the ToolClass and dc_algorithm.models docstring for more details."
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

    Panels defines a list of templates with names and ids to render on the main template.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        generate_form_dict(QueryDict(Satellite)): Generates a dictionary of forms to render on the page.
            Abstract method, so this will need to be implemented in each class that inherits from this.

    """

    panels = [{
        'id': 'history_panel',
        'name': 'History',
        'template': 'panels/history_panel.html'
    }, {
        'id': 'results_panel',
        'name': 'Results',
        'template': 'panels/results_panel.html'
    }, {
        'id': 'output_panel',
        'name': 'Output',
        'template': 'panels/output_panel.html'
    }]

    map_tool_template = 'map_tool.html'
    allow_pixel_drilling = False

    @method_decorator(login_required)
    def get(self, request, area_id):
        """Get the main tool view page using the map_tool template

        Loads the map_tool template with all associated context parameters. Login is required
        for this view, so the userid/username is grabbed from the request without first authenticating.
        Performs an intersection between the area and app satellites to determine what should be displayed.
        Generates forms for each of the satellites to be displayed and lists running queries.

        Args:
            id: Area.id corresponding to the requested area.

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

        user_id = request.user.id
        tool_name = self._get_tool_name()

        area = Area.objects.get(id=area_id)
        app = Application.objects.get(id=tool_name)
        satellites = area.satellites.all() & app.satellites.all()

        forms = self.generate_form_dict(satellites, area)

        task_model_class = self._get_tool_model(self._get_task_model_name())
        user_history = self._get_tool_model('userhistory').objects.filter(user_id=user_id)

        running_tasks = task_model_class.get_queryset_from_history(user_history, complete=False, area_id=area_id)

        context = {
            'tool_name': tool_name,
            'satellites': satellites,
            'forms': forms,
            'running_tasks': running_tasks,
            'area': area,
            'application': app,
            'panels': self.panels,
            'allow_pixel_drilling': self.allow_pixel_drilling
        }

        return render(request, self.map_tool_template, context)

    def generate_form_dict(satellites, area):
        """Generate a dictionary of forms keyed by satellite for rendering

        Forms are generated for each satellite and dynamically hidden and shown by the UI.
        dictionary should be in the format of:
        {
        satellite.datacube_platform: {
            'Section title': form(),
            'Section title': form() ...
            }
        satellite.datacube_platform: {
            'Section title': form(),
            'Section title': form() ...
            }
        }

        This function is must be provided by the inheriting class, the below only exists as an example.

        Raises:
            NotImplementedError in the case of generate_form_dict not being defined by the child class.

        Args:
            satellites: QueryDict of Satellite models that forms will need to be generated over.
            area: area model object.

        Returns
            Dictionary containing all forms and labels for each satellite.

        """
        """
        forms = {}
        for satellite in satellites:
            forms[satellite.pk] = {
                'Geospatial Bounds': GeospatialForm(satellite=satellite, auto_id="{}_%s".format(satellite.pk))
            }
        return forms
        """
        raise NotImplementedError(
            "You must define a generate_form_dict(satellites, area) function in child classes of ToolInfo. See the ToolInfo.generate_form_dict docstring for more details."
        )


class RegionSelection(View, ToolClass):
    """Region selection view responsible for displaying the available areas for the application

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting the toolview without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.

    """

    tool_name = None

    def get(self, request):
        """
        Using the tool_name property, get the application by id and list out all toolinfos and
        areas.

        Context:
            app: app label held by tool_name
            tool_descriptions: ToolInfo objects for the app
            areas: valid areas for the application

        Returns:
            Rendered html page for the region selection for an app
        """

        application = Application.objects.get(id=self._get_tool_name())
        context = {
            'app': self._get_tool_name(),
            'tool_descriptions': self._get_tool_model('toolinfo').objects.all().order_by('id'),
            'areas': application.areas.all()
        }
        return render(request, 'region_selection.html', context)


class UserHistory(View, ToolClass):
    """Generate the content for the user history tab using a user id.

    This is a GET only view, so only the get function is defined. An area id is provided in the
    request and used to get all TaskModels for a user over a given area.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting CancelRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information

    """

    def get(self, request, area_id):
        """Get the user's request history using a user id and format a template

        Requires a 'user_history' model that maps user ids to tasks - Tasks are listed for the
        user then filtered for completion, errors, and area.

        Args:
            id: Area to get tasks for. Tasks are filtered by both user id and area id
                so only tasks valid for the page are shown.

        Returns:
            A rendered html template containing an accordion of past tasks and
            various metadatas. You should be able to load a result using a button on this page.
        """

        user_id = request.user.id
        task_model_class = self._get_tool_model(self._get_task_model_name())
        user_history = self._get_tool_model('userhistory').objects.filter(user_id=user_id)

        task_history = task_model_class.get_queryset_from_history(
            user_history, complete=True, area_id=area_id).exclude(status="ERROR").exclude(pixel_drill_task=True)

        context = {'task_history': task_history}
        return render(request, "/".join([self._get_tool_name(), 'task_history_list.html']), context)


class ResultList(View, ToolClass):
    """Generate the content for the result list tab using a user id.

    This is a GET only view, so only the get function is defined.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting ResultList without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information
        zipped_metadata_fields: list of metadata fields that exist as comma seperated lists that can be seperated and displayed
    """

    def get(self, request, area_id):
        """Get the user's current request list using post data

        Tasks are loaded by ids and rendered using an existing template

        Args:
            POST data: task_ids[] - a list of task ids to load for the panel.

        Returns:
            A rendered html template containing a list of tasks and associated metadata.
        """

        task_ids = request.GET.getlist('task_ids[]')
        task_model_class = self._get_tool_model(self._get_task_model_name())
        tasks = task_model_class.objects.filter(pk__in=task_ids)

        context = {'tasks': tasks}
        return render(request, "/".join([self._get_tool_name(), 'results_list.html']), context)


class OutputList(View, ToolClass):
    """Generate the content for the output list tab post data

    This is a GET only view, so only the get function is defined.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting OutputList without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information
    """

    def get(self, request, area_id):
        """Get the user's currently loaded tasks

        Tasks are loaded by ids and rendered using an existing template

        Args:
            POST data: task_ids[] - a list of task ids to load for the panel.

        Returns:
            A rendered html template containing a list of tasks and associated metadata.
        """

        task_ids = request.GET.getlist('task_ids[]')
        task_model_class = self._get_tool_model(self._get_task_model_name())
        tasks = task_model_class.objects.filter(pk__in=task_ids)

        context = {'tasks': tasks}
        return render(request, "/".join([self._get_tool_name(), 'output_list.html']), context)


class TaskDetails(View, ToolClass):
    """Generate the detals view for the requested task.

    This is a GET only view, so only the get function is defined.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting OutputList without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information
    """

    def get(self, request, uuid):
        """Get the user's currently loaded tasks

        Tasks are loaded by ids and rendered using an existing template

        Args:
            POST data: task_ids[] - a list of task ids to load for the panel.

        Returns:
            A rendered html template containing a list of tasks and associated metadata.
        """

        task_model_class = self._get_tool_model(self._get_task_model_name())
        task = task_model_class.objects.get(pk=uuid)

        context = {'task': task}
        return render(request, "/".join([self._get_tool_name(), 'task_details.html']), context)


class SubmitNewRequest(View, ToolClass):
    """Submit a new request for processing using a task created with form data

    REST API Endpoint for submitting a new request for processing. This is a POST only view,
    so only the post function is defined. Form data is used to create a Task model which is
    then submitted for processing via celery.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting SubmitNewRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        celery_task_func: A celery task called with .delay() with the only parameter being the pk of a task model
        task_model_name: Name of the model that represents your task - see models.Task for more information
        form_list: list [] of form classes (e.g. AdditionalOptionsForm, GeospatialForm) to be used to validate all provided input.

    """

    celery_task_func = None
    form_list = None

    @method_decorator(login_required)
    def post(self, request):
        """Generate a task object and start a celery task using POST form data

        Decorated as login_required so the username is fetched without checking.
        A full form set is submitted in one POST request including all of the forms
        associated with a satellite. This formset is generated using the
        ToolView.generate_form_dict function and should be the forms for a single satellite.
        using the form_list, each form is validated and any errors are returned.

        Args:
            POST data including a full form set described above

        Returns:
            JsonResponse containing:
                A 'status' with either OK or ERROR
                A Json representation of the task object created from form data.
        """

        user_id = request.user.id

        response = {'status': "OK"}
        task_model = self._get_tool_model(self._get_task_model_name())
        forms = [form(request.POST) for form in self._get_form_list()]
        #validate all forms, print any/all errors
        full_parameter_set = {}
        for form in forms:
            if form.is_valid():
                full_parameter_set.update(form.cleaned_data)
            else:
                for error in form.errors:
                    return JsonResponse({'status': "ERROR", 'message': form.errors[error][0]})

        task, new_task = task_model.get_or_create_query_from_post(full_parameter_set)
        #associate task w/ history
        history_model, __ = self._get_tool_model('userhistory').objects.get_or_create(user_id=user_id, task_id=task.pk)
        if new_task:
            self._get_celery_task_func().delay(task_id=task.pk)
        response.update(model_to_dict(task))

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

    def _get_form_list(self):
        """Gets the list of forms used to validate post data and raises an error if it is not defined.

        Checks if form_list property is None, otherwise return the function.
        The celery_task_func must be a function callable with .delay() with the only
        parameters being the pk of a task model.

        """
        if self.form_list is None:
            raise NotImplementedError(
                "You must specify a form_list in classes that inherit SubmitNewRequest. See the SubmitNewRequest docstring for more details."
            )
        return self.form_list


class SubmitPixelDrillRequest(View, ToolClass):
    """Submit a new request for pixel drilling using a task created with form data

    REST API Endpoint for submitting a new pixel drill request for processing. This is a POST only view,
    so only the post function is defined. Form data is used to create a Task model which is
    then submitted for processing via celery.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting SubmitNewRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        celery_task_func: A celery task called with .delay() with the only parameter being the pk of a task model
        task_model_name: Name of the model that represents your task - see models.Task for more information
        form_list: list [] of form classes (e.g. AdditionalOptionsForm, GeospatialForm) to be used to validate all provided input.

    """

    celery_task_func = None
    form_list = None

    @method_decorator(login_required)
    def post(self, request):
        """Generate a task object and start a celery task using POST form data

        Decorated as login_required so the username is fetched without checking.
        A full form set is submitted in one POST request including all of the forms
        associated with a satellite. This formset is generated using the
        ToolView.generate_form_dict function and should be the forms for a single satellite.
        using the form_list, each form is validated and any errors are returned.

        Args:
            POST data including a full form set described above

        Returns:
            JsonResponse containing:
                A 'status' with either OK or ERROR
                A Json representation of the task object created from form data.
        """

        user_id = request.user.id

        response = {'status': "OK"}
        task_model = self._get_tool_model(self._get_task_model_name())
        forms = [form(request.POST) for form in self._get_form_list()]
        #validate all forms, print any/all errors
        full_parameter_set = {}
        for form in forms:
            if form.is_valid():
                full_parameter_set.update(form.cleaned_data)
            else:
                for error in form.errors:
                    return JsonResponse({'status': "ERROR", 'message': form.errors[error][0]})

        task, new_task = task_model.get_or_create_query_from_post(full_parameter_set, pixel_drill=True)
        #associate task w/ history
        history_model, __ = self._get_tool_model('userhistory').objects.get_or_create(user_id=user_id, task_id=task.pk)
        try:
            response['png_path'] = self._get_celery_task_func().delay(task_id=task.pk).get()
            task.refresh_from_db()
            response.update(model_to_dict(task))
            return JsonResponse(response)
        except:
            return JsonResponse({
                'status': "ERROR",
                'message': "There was an unhandled exception while performing your pixel drilling task."
            })

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

    def _get_form_list(self):
        """Gets the list of forms used to validate post data and raises an error if it is not defined.

        Checks if form_list property is None, otherwise return the function.
        The celery_task_func must be a function callable with .delay() with the only
        parameters being the pk of a task model.

        """
        if self.form_list is None:
            raise NotImplementedError(
                "You must specify a form_list in classes that inherit SubmitNewRequest. See the SubmitNewRequest docstring for more details."
            )
        return self.form_list


class GetTaskResult(View, ToolClass):
    """Check the status and fetch the results of a task submitted with Submit*Request

    REST API Endpoint for checking the status of and returning the results of a task.
    This is a GET only view, so only the get function is defined. A Task id is provided in the
    request and used to check the status of a TaskModelClass, returning a dictionary of the model
    if the status is complete.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting GetTaskResult without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information

    """

    def get(self, request):
        """Get a JsonResponse containing a status and Task model if complete

        Check on the execution status of a running tasks by an id provided in the GET parameters
        Default status should be wait - if there is an error in getting the task, or an error in the task
        ERROR will be returned. if complete is set to true, a dictionary of the models attrs is returned.
        If waiting, progress is generated by the tasks model.

        Args:
            'id' in request.GET

        Returns:
            A JsonResponse containing:
                status: WAIT, OK, ERROR
                if completed: Task obj
                if WAIT: progress, containing an integer 0-100 to signify progress.

        """
        task_model = self._get_tool_model(self._get_task_model_name())
        response = {'status': "WAIT"}
        try:
            requested_task = task_model.objects.get(pk=request.GET['id'])
            if requested_task.status == "OK" and requested_task.complete:
                response.update(model_to_dict(requested_task))
                response['status'] = "OK"
            elif requested_task.status == "ERROR":
                response['status'] = "ERROR"
                response['message'] = requested_task.message
            else:
                response['progress'] = requested_task.get_progress()
        except task_model.DoesNotExist:
            response['status'] = "ERROR"
            response['message'] = "Task matching id does not exist."

        return JsonResponse(response)


class SubmitNewSubsetRequest(View, ToolClass):
    """Submit a new subset request based on an existing task result

    REST API Endpoint for submitting a new request based on an existing result. This is a POST only view,
    so only the post function is defined.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting SubmitNewSubsetRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        celery_task_func: A celery task called with .delay() with the only parameter being the pk of a task model
        task_model_name: Name of the model that represents your task - see models.Task for more information
        task_model_update_func: function used to modify an existing task model using any number of kwargs
            params should be the tasks to update and kwargs

    """

    celery_task_func = None
    task_model_update_func = None

    def post(self, request):
        """Use post data to get and modify an existing task model and submit for processing

        Gets the task_tasks by pk, updates it with task_model_update_func, saves the result,
        and returns a dict of the model.

        POST data is required to have:
            id: pk of the task tasks
            any number of named attributes and values used to update the tasks model.

        Returns:
            JsonResponse containing:
                A 'status' with either OK or ERROR
                A Json representation of the tasks object created from form data.

        """

        task_model = self._get_tool_model(self._get_task_model_name())
        response = {'status': "OK"}

        requested_task = task_model.objects.get(pk=request.POST['id'])

        updated_task = self._get_task_model_update_func()(requested_task, **request.POST)
        updated_task.pk = None
        updated_task_data = {field: getattr(updated_task, field) for field in task_model._meta.unique_together[0]}
        try:
            updated_task = task_model.objects.get(**updated_task_data)
        except task_model.DoesNotExist:
            updated_task = task_model(**updated_task_data)
            updated_task.save()
            #only run if this is a new task
            self._get_celery_task_func().delay(task_id=updated_task.pk)

        user_id = request.user.id
        history_model, __ = self._get_tool_model('userhistory').objects.get_or_create(
            user_id=user_id, task_id=updated_task.pk)

        response.update(model_to_dict(updated_task))
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

    def _get_task_model_update_func(self):
        """Gets the task_model_update_func and raises an error if it is not defined.

        Checks if task_model_update_func property is None, otherwise return the function.
        The task_model_update_func must be a function that takes the params of a task model
        and kwargs. Return type should be a task_model object

        """
        if self.task_model_update_func is None:
            raise NotImplementedError(
                "You must specify a task_model_update_func in classes that inherit SubmitNewSubsetRequest. See the SubmitNewSubsetRequest docstring for more details."
            )
        return self.task_model_update_func


class CancelRequest(View, ToolClass):
    """Cancel a running task and disassociate it with the user's history.

    REST API Endpoint for cancelling a task.
    This is a GET only view, so only the get function is defined. A Task id is provided in the
    request and used to get a TaskModelClass, check the status, remove from user history, and delete if applicable.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting CancelRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        task_model_name: Name of the model that represents your task - see models.Task for more information

    """

    def get(self, request):
        """Get a JsonResponse containing a status status signifying task removal

        Cancel on the execution status of a running tasks by an id provided in the GET parameters
        This should just disassociate a tasks from a user's history rather than deleting anything.

        Args:
            'id' in request.GET

        Returns:
            A JsonResponse containing:
                status: WAIT, ERROR

        """
        user_id = request.user.id
        history_model = self._get_tool_model('userhistory')
        try:
            history = history_model.objects.get(user_id=user_id, task_id=request.GET['id'])
            history.delete()
        except history_model.DoesNotExist:
            pass

        return JsonResponse({'status': "OK"})
