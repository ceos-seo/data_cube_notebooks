from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.conf import settings
from django.views import View

import os
import yaml
from yaml import SafeDumper
import uuid
from collections import OrderedDict
from datacube.index import index_connect

from . import models
from . import forms
from . import utils

import json


class DatasetTypeListView(View):
    """Main end point for viewing the list of active dataset types"""

    def get(self, request):
        """Display a DataTables based list of dataset types

        Context:
            dataset_types: queryset of dataset types
        """
        context = {}
        context['dataset_types'] = models.DatasetType.objects.using('agdc').all()
        return render(request, 'data_cube_manager/dataset_types.html', context)


class DatasetTypeView(View):
    """Main end piont for viewing or adding a dataset type"""

    def get(self, request, dataset_type_id=None):
        """View a dataset type and all its attributes

        Context:
            Bound forms for: DatasetTypeMeasurementsForm, DatasetTypeFlagsDefinitionForm
            dataset_type_id: id/pk of the dataset type
        """
        context = {
            'measurements_form': forms.DatasetTypeMeasurementsForm(),
            'flags_definition_form': forms.DatasetTypeFlagsDefinitionForm(),
            'dataset_type_id': dataset_type_id,
        }
        dataset_type = models.DatasetType.objects.using('agdc').get(id=dataset_type_id)
        context.update(utils.forms_from_definition(dataset_type.definition, display_only=True))
        return render(request, 'data_cube_manager/dataset_type.html', context)

    def post(self, request):
        """Add a dataset type to the database

        Using forms, create a json representation of a dataset type and attempt to index it in the database.

        POST Data:
            Measurement forms, metadata forms
        """
        if not request.user.is_superuser:
            return JsonResponse({'status': "ERROR", 'message': "Only superusers can add or update datasets."})

        form_data = request.POST
        measurements = json.loads(form_data.get('measurements'))
        metadata = json.loads(form_data.get('metadata_form'))
        #each measurement_form contains a dict of other forms..
        measurement_forms = [utils.create_measurement_form(measurements[measurement]) for measurement in measurements]
        #just a single form
        metadata_form = utils.create_metadata_form(metadata)

        valid, error = utils.validate_dataset_type_forms(metadata_form, measurement_forms)
        if not valid:
            return JsonResponse({'status': "ERROR", 'message': error})

        if models.DatasetType.objects.using('agdc').filter(name=metadata_form.cleaned_data['name']).exists():
            return JsonResponse({
                'status':
                "ERROR",
                'message':
                'A dataset type already exists with the entered name. Please enter a new name for your dataset and ensure that the definition is different.'
            })

        #since everything is valid, now create yaml from defs..
        product_def = utils.definition_from_forms(metadata_form, measurement_forms)

        index = index_connect()
        try:
            type_ = index.products.from_doc(product_def)
            index.products.add(type_)
        except:
            return JsonResponse({
                'status':
                "ERROR",
                'message':
                'Invalid product definition. Please contact a system administrator if this problem persists.'
            })

        return JsonResponse({'status': 'OK', 'message': 'Your dataset type has been added to the database.'})


class DatasetYamlExport(View):
    """Export a dataset type to yaml from forms

    Using the metadata and measurement forms, create an ordered yaml file that can be used to add the dataset
    to the database.

    POST Data:
        measurement form(s), metadata form

    Returns:
        Json response with a status and (if OK) a url to a yaml file
    """

    def post(self, request):
        """
        """
        form_data = request.POST
        measurements = json.loads(form_data.get('measurements'))
        metadata = json.loads(form_data.get('metadata_form'))
        #each measurement_form contains a dict of other forms..
        measurement_forms = [utils.create_measurement_form(measurements[measurement]) for measurement in measurements]
        #just a single form
        metadata_form = utils.create_metadata_form(metadata)

        valid, error = utils.validate_dataset_type_forms(metadata_form, measurement_forms)
        if not valid:
            return JsonResponse({'status': "ERROR", 'message': error})

        #since everything is valid, now create yaml from defs..
        product_def = utils.definition_from_forms(metadata_form, measurement_forms)
        try:
            os.makedirs('/datacube/ui_results/data_cube_manager/product_defs/')
        except:
            pass

        represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
        yaml.add_representer(OrderedDict, represent_dict_order)

        yaml_url = '/datacube/ui_results/data_cube_manager/product_defs/' + str(uuid.uuid4()) + '.yaml'
        with open(yaml_url, 'w') as yaml_file:
            yaml.dump(product_def, yaml_file)
        return JsonResponse({'status': 'OK', 'url': yaml_url})


class CreateDatasetType(View):
    """Create a new dataset type using the measurements and metadata forms"""

    def get(self, request, dataset_type_id=None):
        """Return a rendered html page that contains the metadata form and ability to
        add or delete measurements.

        This can be built upon an existing dataset type (dataset_type_id) or a blank form.

        Args:
            dataset_type_id: optional id to an existing dataset

        Returns:
            Rendered HTML for a page that will allow users to customize a dataset

        """
        context = {
            'measurements_form': forms.DatasetTypeMeasurementsForm(),
            'flags_definition_form': forms.DatasetTypeFlagsDefinitionForm(),
        }
        if dataset_type_id:
            dataset_type = models.DatasetType.objects.using('agdc').get(id=dataset_type_id)
            context.update(utils.forms_from_definition(dataset_type.definition, display_only=False))
        else:
            context['metadata_form'] = forms.DatasetTypeMetadataForm()
        return render(request, 'data_cube_manager/dataset_type.html', context)


class DeleteDatasetType(View):
    """Delete an existing dataset type including all the datasets associated with the type"""

    def get(self, request, dataset_type_id=None):
        """Get a confirmation page for the dataset type deletion

        List out all the datasets that will be removed alongside the type and prompt for confirmation

        Args:
            dataset_type_id: required kwarg that specifies the pk of a dataset type to remove

        """
        context = {
            'datasets': models.Dataset.objects.using('agdc').filter(dataset_type_ref=dataset_type_id),
            'dataset_type_id': dataset_type_id
        }
        return render(request, 'data_cube_manager/delete_dataset.html', context)

    def post(self, request, dataset_type_id=None):
        """Delete the type by id

        Remove the dataset type by id - due to the cascade settings, this will remove all the datasets/locs/etc
        as well.

        Args:
            dataset_type_id: required kwarg that specifies the pk of a dataset type to remove

        """
        #should cascade
        models.DatasetType.objects.using('agdc').get(id=dataset_type_id).delete()
        return JsonResponse({'status': 'OK'})


class DatasetListView(View):
    """
    """

    def get(self, request, dataset_type_id=None):
        """
        """
        context = {}
        context['datasets'] = models.Dataset.objects.using('agdc').filter(dataset_type_ref=dataset_type_id)
        context['downloadable'] = 'managed' in models.DatasetType.objects.using('agdc').get(
            id=dataset_type_id).definition
        return render(request, 'data_cube_manager/view_datasets.html', context)

    def post(self, request, dataset_type_id=None):
        """
        """
        location = models.DatasetLocation.objects.using('agdc').get(dataset_ref=dataset_ref)
        return redirect(settings.BASE_HOST + location.uri_body.strip("/"))


class DeleteDataset(View):
    """
    """

    def get(self, request, dataset_type_id=None):
        """
        """

    def post(self, request, dataset_type_id=None):
        """
        """


class ValidateMeasurement(View):
    """"""

    def post(self, request):
        """"""

        form_data = request.POST
        measurement_forms = utils.create_measurement_form(form_data)
        #filters out all valid forms.
        for form in filter(lambda x: not measurement_forms[x].is_valid(), measurement_forms):
            for error in measurement_forms[form].errors:
                return JsonResponse({'status': "ERROR", 'message': measurement_forms[form].errors[error][0]})
        return JsonResponse({'status': "OK", 'message': "OK"})
