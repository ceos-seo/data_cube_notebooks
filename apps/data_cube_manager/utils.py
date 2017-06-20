from . import forms
from collections import OrderedDict
from functools import reduce
import re
import json


#takes a product definition (dict) and transforms it to forms for display.
#returns a dict w/ form:
#'metadata_form': forms.DatasetTypeMetadataForm(),
#'measurements_form': forms.DatasetTypeMeasurementsForm(),
#'mask_form': forms.DatasetTypeMaskForm(),
#measurements: {'measurement_name': {'measurement_form': form(),optional -> 'mask_form': form(),'spectral_form': form()}}
def forms_from_definition(product_def, display_only=True):
    #anything without a fallback for .get is required
    #can't really just do a direct copy/update since things are nested strangly + instrument+data format are held in name.
    metadata_def = product_def.get('metadata')
    storage = product_def.get('storage', {})
    metadata = {
        'name': product_def.get('name'),
        'description': product_def.get('description'),
        'metadata_type': product_def.get('metadata_type'),
        #nested in metadata
        'platform': metadata_def.get('platform', {}).get('code', None),
        'instrument': metadata_def.get('instrument', {}).get('name', None),
        'product_type': metadata_def.get('product_type', None),
        'data_format': metadata_def.get('format', {}).get('name', None),
        #stuff nested in storage.
        'storage_driver': storage.get('driver', ''),
        'resolution_longitude': storage.get('resolution', {}).get('longitude', ''),
        'resolution_latitude': storage.get('resolution', {}).get('latitude', ''),
        'crs': storage.get('crs', ''),
        'tile_size_longitude': storage.get('tile_size', {}).get('longitude', ''),
        'tile_size_latitude': storage.get('tile_size', {}).get('latitude', ''),
        'chunking_time': storage.get('chunking', {}).get('time', ''),
        'chunking_longitude': storage.get('chunking', {}).get('longitude', ''),
        'chunking_latitude': storage.get('chunking', {}).get('latitude', ''),
    }

    measurements_def = product_def.get("measurements", None)
    measurements = OrderedDict()
    initial_measurement = None
    for measurement in measurements_def:
        #get standard measurement info
        measurement_data = {
            'name': measurement.get('name'),
            'dtype': measurement.get('dtype'),
            'nodata': measurement.get('nodata'),
            'units': measurement.get('units'),
            'aliases': ",".join(measurement.get('aliases', [])),
            'flags_definition': measurement.get('flags_definition', False)
        }
        measurement_data['flags_definition'] = True if measurement_data['flags_definition'] else False

        if initial_measurement is None:
            initial_measurement = measurement_data['name']

        #set the measurement form
        measurements[measurement_data['name']] = {
            'measurement_form': forms.DatasetTypeMeasurementsForm(measurement_data, existing_dataset_type=display_only)
        }

        #if flag defs exist populate a form and attach to dict.
        flag_name = list(
            measurement.get('flags_definition').keys())[0] if measurement_data['flags_definition'] else None
        flag_values = sorted(measurement.get('flags_definition').get(flag_name).get('values')
                             .keys()) if measurement_data['flags_definition'] else None
        measurements[measurement_data['name']]['flags_definition_form'] = forms.DatasetTypeFlagsDefinitionForm(
            {
                'flag_name':
                flag_name,
                'bits':
                ",".join(map(str, measurement.get('flags_definition').get(flag_name).get('bits'))),
                'description':
                measurement.get('flags_definition').get(flag_name).get('description'),
                'values_for_bits':
                ",".join(flag_values),
                'values':
                ",".join(
                    [str(measurement.get('flags_definition').get(flag_name).get('values')[key]) for key in flag_values])
            },
            existing_dataset_type=display_only) if measurement_data['flags_definition'] else None

    return {
        'metadata_form': forms.DatasetTypeMetadataForm(metadata, existing_dataset_type=display_only),
        'measurements': measurements,
        'initial_measurement': initial_measurement
    }


def definition_from_forms(metadata, measurements):
    json_definition = OrderedDict()
    #do meta first.
    json_definition['name'] = metadata.cleaned_data['name']
    json_definition['description'] = metadata.cleaned_data['description']
    json_definition['metadata_type'] = metadata.cleaned_data['metadata_type']
    json_definition['managed'] = metadata.cleaned_data['managed']
    json_definition['metadata'] = {
        'platform': {
            'code': metadata.cleaned_data['platform']
        },
        'instrument': {
            'name': metadata.cleaned_data['instrument']
        },
        'product_type': metadata.cleaned_data['product_type'],
        'format': {
            'name': metadata.cleaned_data['data_format']
        }
    }

    #optional stuff nested in storage
    storage_attrs = [
        'storage_driver', 'resolution_latitude', 'resolution_longitude', 'crs', 'tile_size_latitude',
        'tile_size_longitude', 'chunking_time', 'chunking_latitude', 'chunking_longitude'
    ]

    # all of these are optional - if any of them exist, create the storage field.
    if any(storage_attr in metadata.cleaned_data and metadata.cleaned_data[storage_attr]
           for storage_attr in storage_attrs):
        storage = {}

        storage['driver'] = metadata.cleaned_data.get('storage_driver', None)

        storage['crs'] = metadata.cleaned_data.get('crs', None)

        storage['resolution'] = {
            'latitude': metadata.cleaned_data['resolution_latitude'],
            'longitude': metadata.cleaned_data['resolution_longitude']
        } if 'crs' in storage else None

        storage['tile_size'] = {
            'latitude': metadata.cleaned_data['tile_size_latitude'],
            'longitude': metadata.cleaned_data['tile_size_longitude']
        } if metadata.cleaned_data['tile_size_longitude'] else None

        storage['chunking'] = {
            'time': metadata.cleaned_data['chunking_time'],
            'latitude': metadata.cleaned_data['chunking_latitude'],
            'longitude': metadata.cleaned_data['chunking_longitude']
        } if metadata.cleaned_data['chunking_time'] else None

        storage['dimension_order'] = ['time', 'latitude', 'longitude'] if 'crs' in storage else None

        fields = ['driver', 'crs', 'resolution', 'tile_size', 'chunking', 'dimension_order']
        ordered_storage = OrderedDict()
        for field in fields:
            if field in storage and storage[field]:
                ordered_storage[field] = storage[field]
        #set storage, but only from dict values that actually exist.
        json_definition['storage'] = ordered_storage

    #measurements
    measurements_list = []
    for measurement in measurements:
        #static fields..
        unordered_measurements = {}
        unordered_measurements['name'] = measurement['measurement_form'].cleaned_data['name']
        unordered_measurements['dtype'] = measurement['measurement_form'].cleaned_data['dtype']
        unordered_measurements['nodata'] = measurement['measurement_form'].cleaned_data['nodata']
        unordered_measurements['units'] = measurement['measurement_form'].cleaned_data['units']
        #split aliases on comma, strip all spaces if they exist.
        unordered_measurements['aliases'] = list(
            map(lambda x: re.sub('[^0-9a-zA-Z]+', '_', x.strip(" ")), measurement['measurement_form'].cleaned_data[
                'aliases'].split(","))) if measurement['measurement_form'].cleaned_data['aliases'] else None

        unordered_measurements['flags_definition'] = {
            measurement['flags_definition_form'].cleaned_data['flag_name']: {
                'bits':
                list(map(lambda x: int(x), measurement['flags_definition_form'].cleaned_data['bits'].split(","))),
                'description': measurement['flags_definition_form'].cleaned_data['description'],
                'values': {
                    k: v
                    for k, v in zip(measurement['flags_definition_form'].cleaned_data['values_for_bits'].split(","),
                                    map(lambda x: re.sub('[^0-9a-zA-Z]+', '_', x.strip(" ")), measurement[
                                        'flags_definition_form'].cleaned_data['values'].split(",")))
                }
            }
        } if measurement['measurement_form'].cleaned_data['flags_definition'] else None

        fields = ['name', 'dtype', 'nodata', 'units', 'aliases', 'flags_definition']
        measurement_dict = OrderedDict()
        for field in fields:
            if unordered_measurements[field] is not None:
                measurement_dict[field] = unordered_measurements[field]

        measurements_list.append(measurement_dict)

    json_definition['measurements'] = measurements_list

    return json_definition


def create_measurement_form(post_data):
    measurement_forms = {'measurement_form': forms.DatasetTypeMeasurementsForm(post_data)}
    if measurement_forms['measurement_form'].is_valid():
        if measurement_forms['measurement_form'].cleaned_data['flags_definition']:
            measurement_forms['flags_definition_form'] = forms.DatasetTypeFlagsDefinitionForm(post_data)
    return measurement_forms


#only here because I think I may do some additional validation/comparisons.. todo?
def create_metadata_form(post_data):
    metadata_form = forms.DatasetTypeMetadataForm(post_data)
    return metadata_form


def logical_xor(a, b):
    return bool(a) ^ bool(b)
