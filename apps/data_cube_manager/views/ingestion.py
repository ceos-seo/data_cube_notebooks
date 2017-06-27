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

from urllib import parse
from collections import OrderedDict
import json
import yaml
import uuid

from apps.data_cube_manager import models
from apps.data_cube_manager import forms

from apps.data_cube_manager import utils


class CreateIngestionConfigurationView(View):
    """Create a new dataset type using the measurements and metadata forms"""

    def get(self, request):
        """Return a rendered html page that contains the metadata form and ability to
        add or delete measurements.

        This can be built upon an existing dataset type (dataset_type_id) or a blank form.

        Args:
            dataset_type_id: optional id to an existing dataset

        Returns:
            Rendered HTML for a page that will allow users to customize a dataset

        """
        context = {
            'metadata_form': forms.IngestionMetadataForm(),
            'measurement_form': forms.IngestionMeasurementForm(),
            'storage_form': forms.IngestionStorageForm(),
            'ingestion_bounds_form': forms.IngestionBoundsForm()
        }

        return render(request, 'data_cube_manager/ingestion.html', context)


class IngestionYamlExport(View):
    """Export a dataset type to yaml from forms

    Using the metadata and measurement forms, create an ordered yaml file that can be used to add the dataset
    to the database.

    POST Data:
        measurement form(s), metadata form

    Returns:
        Json response with a status and (if OK) a url to a yaml file
    """

    def post(self, request):
        """Validate form data and create a .yaml file

        Forms include all forms from the ingestion forms module, validated and dump to YAML.

        Returns:
            JsonResponse with a status and url if there is no error.
        """

        form_data = request.POST
        measurements = json.loads(form_data.get('measurements'))
        metadata = json.loads(form_data.get('metadata_form'))
        #each measurement_form contains a dict of other forms..
        measurement_forms = [forms.IngestionMeasurementForm(measurements[measurement]) for measurement in measurements]
        #just a single form
        metadata_form = forms.IngestionMetadataForm(metadata)
        storage_form = forms.IngestionStorageForm(metadata)
        ingestion_bounds_form = forms.IngestionBoundsForm(metadata)

        valid, error = utils.validate_form_groups(metadata_form, storage_form, ingestion_bounds_form,
                                                  *measurement_forms)
        if not valid:
            return JsonResponse({'status': "ERROR", 'message': error})

        #since everything is valid, now create yaml from defs..
        ingestion_def = utils.ingestion_definition_from_forms(metadata_form, storage_form, ingestion_bounds_form,
                                                              measurement_forms)
        try:
            os.makedirs('/datacube/ui_results/data_cube_manager/ingestion_configurations/')
        except:
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

        yaml.SafeDumper.add_representer(OrderedDict, _dict_representer)

        yaml_url = '/datacube/ui_results/data_cube_manager/ingestion_configurations/' + str(uuid.uuid4()) + '.yaml'
        with open(yaml_url, 'w') as yaml_file:
            yaml.dump(ingestion_def, yaml_file, Dumper=yaml.SafeDumper, default_flow_style=False, indent=4)
        return JsonResponse({'status': 'OK', 'url': yaml_url})


class IngestionMeasurement(View):
    """Gets a list of existing measurements and validates user added measurements"""

    def get(self, request):
        """Get existing measurement forms for a dataset type

        Args:
            dataset type id, used to fetch the dataset type and its definition.

        Returns:
            Rendered HTML string containing a form for each measurement and a panel that
            enumerates all measurements. Essentially just the right side panel of the ingestion/dataset type page.
        """

        dataset_type = models.DatasetType.objects.using('agdc').get(id=request.GET.get('dataset_type'))
        measurements = dataset_type.definition['measurements']
        for measurement in measurements:
            measurement['src_varname'] = measurement['name']
            # conversion from uint16->32 to handle USGS Coll 1.
            measurement['dtype'] = 'int32' if measurement['dtype'] in ['uint16'] else measurement['dtype']
        measurement_dict = {
            measurement['name']: forms.IngestionMeasurementForm(measurement)
            for measurement in measurements
        }
        return JsonResponse({
            'status':
            "OK",
            'message':
            "OK",
            'html':
            render_to_string('data_cube_manager/existing_measurements.html', {'measurements': measurement_dict})
        })

    def post(self, request):
        """Valid a form using POST data and return any error messages

        Validates an IngestionMeasurementForm and returns any errors
        """

        form_data = request.POST

        measurement_form = forms.IngestionMeasurementForm(form_data)
        #filters out all valid forms.
        if not measurement_form.is_valid():
            for error in measurement_form.errors:
                return JsonResponse({'status': "ERROR", 'message': measurement_form.errors[error][0]})
        return JsonResponse({'status': "OK", 'message': "OK"})
