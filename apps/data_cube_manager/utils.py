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


def dataset_type_definition_from_forms(metadata, measurements):
    json_definition = OrderedDict([
        ('name', metadata.cleaned_data['name']),
        ('description', metadata.cleaned_data['description']),
        ('metadata_type', metadata.cleaned_data['metadata_type']),
        ('managed', metadata.cleaned_data['managed']),
        ('metadata', OrderedDict([
            ('platform', {
                'code': metadata.cleaned_data['platform']
            }),
            ('instrument', {
                'name': metadata.cleaned_data['instrument']
            }),
            ('product_type', metadata.cleaned_data['product_type']),
            ('format', {
                'name': metadata.cleaned_data['data_format']
            }),
        ])),
    ])

    #optional stuff nested in storage
    storage_attrs = ['driver', 'resolution_latitude', 'resolution_longitude', 'crs']

    # all of these are optional - if any of them exist, create the storage field.
    if any(metadata.cleaned_data.get(storage_attr, None) for storage_attr in storage_attrs):
        storage = OrderedDict()

        storage['driver'] = metadata.cleaned_data.get('storage_driver', None)

        storage['crs'] = metadata.cleaned_data.get('crs', None)

        storage['resolution'] = {
            'latitude': metadata.cleaned_data['resolution_latitude'],
            'longitude': metadata.cleaned_data['resolution_longitude']
        } if 'crs' in storage else None

        #set storage, but only from dict values that actually exist.
        json_definition['storage'] = OrderedDict([(key, val) for key, val in storage.items() if val is not None])

    def get_measurment_data(measurement):
        #static fields..
        ordered_measurements = OrderedDict([
            ('name', measurement['measurement_form'].cleaned_data['name']),
            ('dtype', measurement['measurement_form'].cleaned_data['dtype']),
            ('nodata', measurement['measurement_form'].cleaned_data['nodata']),
            ('units', measurement['measurement_form'].cleaned_data['units']),
        ])

        #split aliases on comma, strip all spaces if they exist.
        ordered_measurements['aliases'] = list(
            map(lambda x: re.sub('[^0-9a-zA-Z]+', '_', x.strip(" ")), measurement['measurement_form'].cleaned_data[
                'aliases'].split(","))) if measurement['measurement_form'].cleaned_data['aliases'] else None

        ordered_measurements['flags_definition'] = {
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

        return OrderedDict([(key, val) for key, val in ordered_measurements.items() if val is not None])

    json_definition['measurements'] = [get_measurment_data(measurement) for measurement in measurements]

    return json_definition


def ingestion_definition_from_forms(metadata, storage_form, ingestion_bounds_form, measurement_forms):
    json_definition = OrderedDict(
        [('source_type', metadata.cleaned_data['dataset_type_ref'].name),
         ('output_type', metadata.cleaned_data['output_type']), ('description', metadata.cleaned_data['description']),
         ('location', metadata.cleaned_data['location']),
         ('file_path_template', metadata.cleaned_data['file_path_template'])])

    json_definition['global_attributes'] = OrderedDict(
        [('title', metadata.cleaned_data['title']), ('summary', metadata.cleaned_data['summary']),
         ('source', metadata.cleaned_data['source']), ('institution', metadata.cleaned_data['institution']),
         ('platform', metadata.cleaned_data['platform']), ('instrument', metadata.cleaned_data['instrument']),
         ('processing_level', metadata.cleaned_data['processing_level']),
         ('product_version', metadata.cleaned_data['product_version']),
         ('references', metadata.cleaned_data['references'])])

    json_definition['ingestion_bounds'] = OrderedDict([
        ('left', ingestion_bounds_form.cleaned_data['left']),
        ('bottom', ingestion_bounds_form.cleaned_data['bottom']),
        ('right', ingestion_bounds_form.cleaned_data['right']),
        ('top', ingestion_bounds_form.cleaned_data['top']),
    ])

    storage_units = ('longitude', 'latitude') if storage_form.cleaned_data['crs_units'] == "degrees" else ('x', 'y')

    json_definition['storage'] = OrderedDict([
        ('driver', "NetCDF CF"),
        ('crs', storage_form.cleaned_data['crs']),
        ('tile_size', OrderedDict([(storage_units[0], storage_form.cleaned_data['tile_size_longitude']),
                                   (storage_units[1], storage_form.cleaned_data['tile_size_latitude'])])),
        ('resolution', OrderedDict([(storage_units[0], storage_form.cleaned_data['resolution_longitude']),
                                    (storage_units[1], storage_form.cleaned_data['resolution_latitude'])])),
        # chunking is a dict w/ x/lon, y/lat, time
        ('chunking', OrderedDict([(storage_units[0], storage_form.cleaned_data['chunking_longitude']),
                                  (storage_units[1], storage_form.cleaned_data['chunking_latitude']), ('time', 1)])),
        # time, y, x indexing.
        ('dimension_order', ['time', storage_units[1], storage_units[0]]),
    ])

    #measurements
    def get_measurment_data(measurement_form):
        #static fields..
        measurement_data = OrderedDict(
            [('name', measurement_form.cleaned_data['name']), ('dtype', measurement_form.cleaned_data['dtype']),
             ('nodata', measurement_form.cleaned_data['nodata']),
             ('resampling_method', measurement_form.cleaned_data['resampling_method']),
             ('src_varname', measurement_form.cleaned_data['src_varname']), ('zlib', True)])

        if measurement_form.cleaned_data.get('long_name', None) or measurement_form.cleaned_data.get('alias', None):
            measurement_data['attrs'] = {
                key: measurement_form.cleaned_data[key]
                for key in ['long_name', 'attrs'] if measurement_form.cleaned_data.get(key, None)
            }
        return measurement_data

    json_definition['measurements'] = [get_measurment_data(measurement) for measurement in measurement_forms]
    json_definition['fuse_data'] = 'copy'

    return json_definition


def validate_dataset_type_forms(metadata_form, measurement_forms):
    for measurement_form_group in measurement_forms:
        for form in filter(lambda x: not measurement_form_group[x].is_valid(), measurement_form_group):
            for error in measurement_form_group[form].errors:
                return False, measurement_form_group[form].errors[error][0]
    if not metadata_form.is_valid():
        for error in metadata_form.errors:
            return False, metadata_form.errors[error][0]

    return True, None


def validate_form_groups(*forms):
    for form in filter(lambda x: not x.is_valid(), forms):
        for error in form.errors:
            return False, form.errors[error][0]
    return True, None


def create_measurement_form(post_data):
    measurement_forms = {'measurement_form': forms.DatasetTypeMeasurementsForm(post_data)}
    if measurement_forms['measurement_form'].is_valid():
        if measurement_forms['measurement_form'].cleaned_data['flags_definition']:
            measurement_forms['flags_definition_form'] = forms.DatasetTypeFlagsDefinitionForm(post_data)
    return measurement_forms


def logical_xor(a, b):
    return bool(a) ^ bool(b)
