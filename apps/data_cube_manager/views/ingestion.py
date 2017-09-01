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
            'metadata_form':
            forms.IngestionMetadataForm(),
            'measurement_form':
            forms.IngestionMeasurementForm(),
            'storage_form':
            forms.IngestionStorageForm(),
            'ingestion_bounds_form':
            forms.IngestionBoundsForm(),
            'product_details':
            models.DatasetType.objects.using('agdc').filter(~Q(definition__has_keys=['managed']) & Q(
                definition__has_keys=['measurements']))
        }

        return render(request, 'data_cube_manager/ingestion.html', context)

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


class SubmitIngestion(View):
    """Submit an ingestion form for actual ingestion"""

    @method_decorator(login_required)
    def post(self, request):
        """Validate a set of measurements, metadata, storage, and bounds forms to create an ingestion task

        Validates all forms, returning any errors. In the case of no errors, populate an ingestion
        definition and kick off a celery task that will multiproc ingestion.

        """

        if not request.user.is_superuser:
            return JsonResponse({'status': "ERROR", 'message': "Only superusers can ingest new data."})
        if models.IngestionRequest.objects.filter(
                user=request.user.username).exists() and models.IngestionRequest.objects.filter(
                    user=request.user.username)[0].status != "OK":
            return JsonResponse({
                'status':
                "ERROR",
                'message':
                "Please wait until your previous ingestion request is complete before submitting."
            })

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

        output_id = tasks.run_ingestion(ingestion_def)

        return JsonResponse({'status': 'OK', 'dataset_type_ref': output_id})


class CreateDataCubeSubset(View):
    """Submit an ingestion form to create a sample Data Cube for user download"""

    @method_decorator(login_required)
    def get(self, request):
        """Return a rendered html page that contains the metadata form and ability to
        add or delete measurements.

        This can be built upon an existing dataset type (dataset_type_id) or a blank form.

        Args:
            dataset_type_id: optional id to an existing dataset

        Returns:
            Rendered HTML for a page that will allow users to customize a dataset

        """
        context = {}

        available_fields = [
            'dataset_type_ref', 'longitude_min', 'longitude_max', 'latitude_min', 'latitude_max', 'start_date',
            'end_date'
        ]
        existing_data = {
            key: request.GET.get(key, None)
            for key in available_fields if request.GET.get(key, None) is not None
        }

        ingestion_storage_defaults = None
        if 'dataset_type_ref' in existing_data:
            dataset_type = models.DatasetType.objects.using('agdc').get(id=existing_data['dataset_type_ref'])
            measurements = dataset_type.definition['measurements']
            for measurement in measurements:
                measurement['src_varname'] = measurement['name']
                # conversion from uint16->32 to handle USGS Coll 1.
                measurement['dtype'] = 'int32' if measurement['dtype'] in ['uint16'] else measurement['dtype']
            measurement_dict = OrderedDict(
                [(measurement['name'], forms.IngestionMeasurementForm(measurement)) for measurement in measurements])

            context.update({'measurements': measurement_dict, 'initial_measurement': measurements[0]['name']})

            ingestion_storage_defaults = {
                'crs': "EPSG:4326",
                'crs_units': "degrees",
                'tile_size_longitude': dataset_type.definition['storage']['tile_size']['longitude'],
                'tile_size_latitude': dataset_type.definition['storage']['tile_size']['latitude'],
                'resolution_latitude': dataset_type.definition['storage']['resolution']['latitude'],
                'resolution_longitude': dataset_type.definition['storage']['resolution']['longitude'],
                'chunking_latitude': 200,
                'chunking_longitude': 200
            }

        context.update({
            'ingestion_request_form':
            forms.IngestionRequestForm(initial=existing_data),
            'measurement_form':
            forms.IngestionMeasurementForm(),
            'storage_form':
            forms.IngestionStorageForm(ingestion_storage_defaults if ingestion_storage_defaults else {
                'crs': "EPSG:4326",
                'crs_units': "degrees",
                'tile_size_longitude': 0.943231048326,
                'tile_size_latitude': 0.943231048326,
                'resolution_latitude': -0.000269494585236,
                'resolution_longitude': 0.000269494585236,
                'chunking_latitude': 200,
                'chunking_longitude': 200
            })
        })

        return render(request, 'data_cube_manager/ingestion_request.html', context)

    @method_decorator(login_required)
    def post(self, request):
        """Submit a Data Cube subset request using form data

        POST Data:
            IngestionRequestForm, IngestionStorageForm, IngestionBoundsForm

        Returns:
            Json response containing a pk to an ingestion request.

        """

        form_data = request.POST
        measurements = json.loads(form_data.get('measurements'))
        metadata = json.loads(form_data.get('metadata_form'))

        #each measurement_form contains a dict of other forms..
        measurement_forms = [forms.IngestionMeasurementForm(measurements[measurement]) for measurement in measurements]
        #just a single form
        metadata_form = forms.IngestionRequestForm(metadata)
        storage_form = forms.IngestionStorageForm(metadata)
        ingestion_bounds_form = forms.IngestionBoundsForm({
            'left': metadata.get('longitude_min', None),
            'right': metadata.get('longitude_max', None),
            'bottom': metadata.get('latitude_min', None),
            'top': metadata.get('latitude_max', None)
        })

        valid, error = utils.validate_form_groups(metadata_form, storage_form, ingestion_bounds_form,
                                                  *measurement_forms)
        if not valid:
            return JsonResponse({'status': "ERROR", 'message': error})

        dataset_type = metadata_form.cleaned_data.get('dataset_type_ref')
        metadata_form.cleaned_data.update({'dataset_type': dataset_type, 'dataset_type_ref': [dataset_type]})
        if not models.Dataset.filter_datasets(metadata_form.cleaned_data).exists():
            return JsonResponse({
                'status':
                "ERROR",
                'message':
                "There are no datasets for the entered parameter set. Use the Dataset Viewer page to create a request from a list of datasets."
            })

        metadata_form.cleaned_data.update({
            'dataset_type_ref':
            metadata_form.cleaned_data['dataset_type_ref'][0],
            'output_type':
            dataset_type.name + "_sample",
            'description':
            "Sample subset of {} created for {}".format(dataset_type.name, request.user.username),
            'location':
            "/datacube/ingested_data/{}".format(request.user.username),
            'file_path_template':
            "SAMPLE_CUBE_4326_{tile_index[0]}_{tile_index[1]}_{start_time}.nc",
            'summary':
            "Contains a small subset of {}.".format(dataset_type.name),
            'platform':
            dataset_type.get_description(),
            'instrument':
            dataset_type.get_instrument(),
            'processing_level':
            dataset_type.get_processing_level(),
            'title':
            "Sample Data Cube created by the CEOS Data Cube UI",
            'source':
            "CEOS Data Cube UI",
            'institution':
            "CEOS",
            'product_version':
            "1.0",
            'references':
            "https://github.com/ceos-seo/data_cube_ui",
        })

        #since everything is valid, now create yaml from defs..
        ingestion_def = utils.ingestion_definition_from_forms(metadata_form, storage_form, ingestion_bounds_form,
                                                              measurement_forms)

        existing_requests = models.IngestionRequest.objects.filter(user=request.user.username)

        if existing_requests.exists():
            if existing_requests[0].status in ['OK', 'ERROR']:
                tasks.delete_ingestion_request.delay(ingestion_request_id=existing_requests[0].pk).get()
                existing_requests.delete()
            else:
                return JsonResponse({
                    'status':
                    'ERROR',
                    'message':
                    "Please wait until your existing ingestion request has been completed before submitting another."
                })

        ingestion_request = models.IngestionRequest(
            user=request.user.username,
            dataset_type_ref=dataset_type.pk,
            ingestion_definition=ingestion_def,
            start_date=metadata_form.cleaned_data['start_date'],
            end_date=metadata_form.cleaned_data['end_date'],
            latitude_min=metadata_form.cleaned_data['latitude_min'],
            latitude_max=metadata_form.cleaned_data['latitude_max'],
            longitude_min=metadata_form.cleaned_data['longitude_min'],
            longitude_max=metadata_form.cleaned_data['longitude_max'])
        ingestion_request.save()

        tasks.ingestion_on_demand.delay(ingestion_request_id=ingestion_request.pk)

        return JsonResponse({'status': 'OK', 'ingestion_request_id': ingestion_request.pk})


class CheckIngestionRequestStatus(View):
    """Status page for an ingestion request"""

    def get(self, request, ingestion_request_id):
        """Check the status of an ingestion request and update the model

        Returns a rendered html response containing a non-editable form displaying the ingestion request data,
        instructions, and a progress bar.
        """

        context = {'ingestion_request_id': ingestion_request_id}
        try:
            ingestion_request = models.IngestionRequest.objects.get(pk=ingestion_request_id)
        except models.IngestionRequest.DoesNotExist:
            return redirect('/data_cube_manager/ingestion/subset')
        filtering_options = {
            key: getattr(ingestion_request, key)
            for key in [
                'dataset_type_ref', 'start_date', 'end_date', 'latitude_min', 'latitude_max', 'longitude_min',
                'longitude_max'
            ]
        }
        context['form'] = forms.IngestionRequestForm(initial=filtering_options, readonly=True)
        context.update(model_to_dict(ingestion_request))
        return render(request, 'data_cube_manager/ingestion_request_status.html', context)

    def post(self, request, ingestion_request_id):
        """Check on the status of an ingestion request, returning a json response containing the model"""
        context = {'ingestion_request_id': ingestion_request_id}
        ingestion_request = models.IngestionRequest.objects.get(pk=ingestion_request_id)
        ingestion_request.update_storage_unit_count()
        context.update(model_to_dict(ingestion_request))
        return JsonResponse(context)


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
        dataset_type = models.DatasetType.objects.using('agdc').get(id=request.GET.get('dataset_type_ref'))
        measurements = dataset_type.definition['measurements']
        for measurement in measurements:
            measurement['src_varname'] = measurement['name']
            # conversion from uint16->32 to handle USGS Coll 1.
            measurement['dtype'] = 'int32' if measurement['dtype'] in ['uint16'] else measurement['dtype']
        measurement_dict = OrderedDict(
            [(measurement['name'], forms.IngestionMeasurementForm(measurement)) for measurement in measurements])

        product_details = {}
        if 'managed' in dataset_type.definition and models.IngestionDetails.objects.filter(
                dataset_type_ref=dataset_type.pk).exists():
            product_details = {
                'crs': "EPSG:4326",
                'crs_units': "degrees",
                'tile_size_longitude': dataset_type.definition['storage']['tile_size']['longitude'],
                'tile_size_latitude': dataset_type.definition['storage']['tile_size']['latitude'],
                'resolution_latitude': dataset_type.definition['storage']['resolution']['latitude'],
                'resolution_longitude': dataset_type.definition['storage']['resolution']['longitude'],
                'chunking_latitude': 200,
                'chunking_longitude': 200
            }
            product_details.update(model_to_dict(models.IngestionDetails.objects.get(dataset_type_ref=dataset_type.pk)))

        return JsonResponse({
            'status':
            "OK",
            'message':
            "OK",
            'html':
            render_to_string('data_cube_manager/existing_measurements.html',
                             {'measurements': measurement_dict,
                              'initial_measurement': measurements[0]['name']}),
            'product_details':
            product_details
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
