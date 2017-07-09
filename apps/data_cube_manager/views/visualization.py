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

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.conf import settings
from django.views import View
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from urllib import parse
from collections import OrderedDict
import json
import yaml
import uuid
import shutil

from apps.data_cube_manager import models
from apps.data_cube_manager import forms
from apps.data_cube_manager import utils
from apps.data_cube_manager import tasks


class DataCubeVisualization(View):
    """Visualize ingested and indexed Data Cube regions using leaflet"""

    def get(self, request):
        """Main end point for viewing datasets and their extents on a leaflet map"""

        context = {'form': forms.VisualizationForm()}
        context['dataset_types'] = models.DatasetType.objects.using('agdc').filter(
            definition__has_keys=['measurements'])
        return render(request, 'data_cube_manager/visualization.html', context)


class GetIngestedAreas(View):
    """Get a dict containing details on the ingested areas, grouped by Platform"""

    def get(self, request):
        """Call a synchronous task to produce a dict containing ingestion details

        Work performed in a synchrounous task so the execution is done on a worker rather than on
        the webserver. Gets a dict like:
            {Landsat_5: [{}, {}, {}],
            Landsat_7: [{}, {}, {}]}
        """

        platforms = models.IngestionDetails.objects.filter(
            global_dataset=False).order_by().values_list('platform').distinct()

        ingested_area_details = {
            platform[0]: [
                ingestion_detail_listing.get_serialized_response()
                for ingestion_detail_listing in models.IngestionDetails.objects.filter(
                    global_dataset=False, platform=platform[0])
            ]
            for platform in platforms
        }

        return JsonResponse(ingested_area_details)
