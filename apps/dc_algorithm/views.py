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


class ToolView(View):
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

    Attributes:
        get: Handles the get request and returns a rendered html response.

    """

    tool_name = None
    query_model = None

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
        tool_name = self.get_tool_name()
        area = Area.objects.get(area_id=area_id)
        app = Application.objects.get(application_id=tool_name)
        satellites = area.satellites.all() & app.satellites.all()

        forms = self.generate_form_dict(satellites)

        running_queries = apps.get_model('.'.join([tool_name, 'query'])).objects.filter(
            user_id=user_id, area_id=area_id, complete=False)

        context = {
            'tool_name': tool_name,
            'satellites': satellites,
            'forms': forms,
            'running_queries': running_queries,
            'area': area,
            'application': app,
        }

        return render(request, 'map_tool/map_tool.html', context)

    def get_tool_name(self):
        """Get the tool_name property

        Meant to implement a general NotImplementedError for required properties

        Raises:
            NotImplementedError in the case of tool_name not being defined

        Returns:
            The value of tool_name.

        """
        if self.tool_name is None:
            raise NotImplementedError(
                "You must specify a tool_name in child classes of ToolInfo. See the ToolInfo docstring for more details."
            )
        return self.tool_name

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
