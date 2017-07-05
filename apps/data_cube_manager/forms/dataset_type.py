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

from django import forms
from django.core.validators import RegexValidator, validate_comma_separated_integer_list, validate_slug
from django.core import validators

import re
import datetime

from apps.data_cube_manager.utils import logical_xor
from apps.data_cube_manager.models import DatasetType

comma_separated_float_list_re = re.compile('^([-+]?\d*\.?\d+[,\s]*)+$')
validate_comma_separated_float_list = RegexValidator(
    comma_separated_float_list_re,
    'Enter only floats separated by commas and ensure there are no leading or trailing commas.', 'invalid')


class DatasetTypeMetadataForm(forms.Form):
    """Dataset type metadata form, meant to validate and clean the metadata section of dataset types

    Validates a block of .yaml inputs that resemble below:

    name: ls5_ledaps_scene
    description: Landsat 5 LEDAPS 25 metre
    metadata_type: eo

    metadata:
        platform:
            code: LANDSAT_5
        instrument:
            name: TM
        product_type: ledaps
        format:
            name: GeoTiff

    storage:
        crs: EPSG:4326
        resolution:
            longitude: 1
            latitude: 1
        driver: GeoTiff
    """
    #standard meta in the definition - no nesting
    name = forms.CharField(
        label="Dataset Name",
        help_text="Enter a name for your dataset. Spaces and special characters are not allowed. We recommend an all lowercase, underscore seperated string.",
        widget=forms.TextInput(attrs={'placeholder': "ls7_ledaps_kenya"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Dataset name is required. Please enter a valid name in the Dataset Metadata panel.'
        })
    description = forms.CharField(
        label="Dataset Description",
        help_text="Enter a description for your dataset. Spaces, special characters, etc. are all allowed.",
        widget=forms.TextInput(
            attrs={'placeholder': "Landsat 7 LEDAPS SR Product - UTM based projection, 30m resolution."}),
        required=True,
        error_messages={
            'required': 'Dataset description is required. Please enter a description in the Dataset Metadata panel.'
        })
    metadata_type = forms.CharField(
        label="Metadata Type",
        help_text="Metadata type reference. This must correspond with a metadata type that exists in the database. This will generally remain 'eo'.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="eo",
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Metadata type is required. Please enter a valid metadata type in the Dataset Metadata panel.'
        })
    managed = forms.BooleanField(
        label="Managed",
        help_text="Is this dataset managed by the Data Cube? This will be true for products of the ingestion process.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial=False,
        required=False)

    #nested in metadata - required.
    platform = forms.CharField(
        label="Platform",
        help_text="Enter the platform for your dataset. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "LANDSAT_7"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Platform is required. Please enter a valid platform in the Dataset Metadata panel.'
        })
    instrument = forms.CharField(
        label="Instrument",
        help_text="Enter an instrument name for your dataset. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "TM"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Instrument is required. Please enter a valid instrument in the Dataset Metadata panel.'
        })
    product_type = forms.CharField(
        label="Product Type",
        help_text="Enter a product type for your dataset. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "ledaps"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Product type is required. Please enter a product type in the Dataset Metadata panel.'
        })
    data_format = forms.CharField(
        label="Data File Format",
        help_text="Enter your dataset's file format - examples include GeoTIFF, NetCDF, JPEG2000, and ENVI.",
        widget=forms.TextInput(attrs={'placeholder': "GeoTIFF, NetCDF, JPEG2000, ENVI"}),
        initial="GeoTIFF",
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Data format is required. Please enter a valid data format in the Dataset Metadata panel.'
        })

    #additional - nested in storage. All of this is Optional
    driver = forms.CharField(
        label="Storage Driver",
        help_text="This must correspond with the driver of the dataset - generally only set on products that have been ingested.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
        required=False)
    resolution_longitude = forms.FloatField(
        label="Resolution (x, Longitude)",
        help_text="Optional parameter. Please enter a x/longitude resolution for this dataset. This value should correspond with the actual resolution of the dataset this configuration is referencing.",
        widget=forms.TextInput(),
        initial="",
        required=False)
    resolution_latitude = forms.FloatField(
        label="Resolution (y, Latitude)",
        help_text="Optional parameter. Please enter a y/latitude resolution for this dataset. This value should correspond with the actual resolution of the dataset this configuration is referencing.",
        widget=forms.TextInput(),
        initial="",
        required=False)
    crs = forms.CharField(
        label="Dataset CRS",
        help_text="Optional parameter. Please enter a CRS in WKT or EPSG format. This value should correspond with the crs of the dataset this configuration is referencing.",
        widget=forms.TextInput({
            'placeholder': "EPSG:4326"
        }),
        required=False)

    def __init__(self, *args, **kwargs):
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeMetadataForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DatasetTypeMetadataForm, self).clean()
        #if a latitude attr is provided a lon value must be specified as well.
        if logical_xor(cleaned_data['resolution_latitude'], cleaned_data['resolution_longitude']):
            self.add_error(
                'resoltion_latitude',
                'Please enter a value for both resolution attributes. If one of latitude/longitude attribute is set, the other must be as well.'
            )

        if cleaned_data['resolution_latitude'] and cleaned_data['resolution_longitude'] and not cleaned_data[
                'crs'] or cleaned_data['crs'] and not (cleaned_data['resolution_latitude'] and
                                                       cleaned_data['resolution_longitude']):
            self.add_error(
                'crs',
                'CRS, latitude resolution, and longitude resolution must all be provided if one of the fields is not null.'
            )


class DatasetTypeMeasurementsForm(forms.Form):
    """Dataset measurement form, meant to validate measurements for dataset types

    Validates a block of .yaml that resembles below:

    - name: 'sr_atmos_opacity'
      aliases: [atmos_opacity]
      dtype: uint8
      nodata: 0
      units: 'unitless'

    """
    name = forms.CharField(
        label="Measurement Name",
        help_text="Please enter the name of the measurement. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "swir1"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Measurement name is required. Please enter a valid name in the Measurement panel.'
        })

    dtypes = ["float16", "float32", "float64", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"]
    dtype = forms.ChoiceField(
        label="Data Type",
        help_text="Choose your dataset's data type from the provided options.",
        choices=((dtype, dtype) for dtype in dtypes),
        initial="int16",
        required=True)

    nodata = forms.FloatField(
        label="Nodata Value",
        help_text="Please enter the number that represents nodata in your dataset.",
        required=True,
        error_messages={'required': 'Nodata value is required. Please enter a valid value in the Measurement panel.'})
    units = forms.CharField(
        label="Units",
        initial="1",
        help_text="Please enter the units for your dataset. This can be dB, nG/h, etc. Enter 1 if there are no units.",
        required=True,
        validators=[validate_slug],
        error_messages={'required': 'Measurement units is required. Please enter a value in the Measurement panel.'})
    aliases = forms.CharField(
        label="Aliases",
        help_text="Enter a comma seperated list of aliases for the measurement. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "mask, CFmask"}),
        required=False)

    #if mask is true then bits, description, and values must be provided
    flags_definition = forms.BooleanField(
        label="Flags Definition",
        help_text="Do you want to enter mask attributes for this measurement?",
        widget=forms.CheckboxInput(attrs={'onchange': "toggle_flags_definition(this)"}),
        initial=False,
        required=False)

    def __init__(self, *args, **kwargs):
        """If this is an existing dataset type, the form is set to readonly as a 'viewing' form."""
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeMeasurementsForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True


class DatasetTypeFlagsDefinitionForm(forms.Form):
    """Dataset flags defintiion form, meant to validate any instances of flags definitions in measurements.

    Meant to validate the flags definition portion of the .yaml block below.

    - name: 'cfmask'
      aliases: [mask, CFmask]
      dtype: uint8
      nodata: 255
      units: '1'
      flags_definition:
        cfmask:
          bits: [0,1,2,3,4,5,6,7]
          description: CFmask
          values:
            0: clear
            1: water
            2: shadow
            3: snow
            4: cloud
    """
    flag_name = forms.CharField(
        label="Mask Name",
        help_text="Enter the name (lower case, underscore seperated) of the mask.",
        widget=forms.TextInput(attrs={'placeholder': 'cloud_confidence'}),
        required=False)
    bits = forms.CharField(
        label="Mask Bits",
        help_text="Please enter a comma seperated list of valid bits for this mask.",
        widget=forms.TextInput(attrs={'placeholder': "0,1,2,3,4,5,6,7"}),
        required=False,
        validators=[validate_comma_separated_integer_list])
    description = forms.CharField(label="Description", help_text="Enter a description for your mask.", required=False)
    values_for_bits = forms.CharField(
        label="Values (bits)",
        help_text="Enter a comma seperated list of bit values that you'd like assign a description to. These values will correspond with the values field.",
        widget=forms.TextInput(attrs={'placeholder': "0,1,2,3,4"}),
        required=False,
        validators=[validate_comma_separated_integer_list])
    values = forms.CharField(
        label="Values (description)",
        help_text="Enter a comma seperated list of strings that will be used as labels for the bit values.",
        widget=forms.TextInput(attrs={'placeholder': "clear,water,shadow,snow,cloud"}),
        required=False)

    def __init__(self, *args, **kwargs):
        """If this is an existing dataset type, the form is set to readonly as a 'viewing' form."""
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeFlagsDefinitionForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

    def clean_values(self):
        return self.cleaned_data['values'].strip(",")

    def clean(self):
        """Clean the flags definition form - ensure that there are bits, values, and descriptions"""

        cleaned_data = super(DatasetTypeFlagsDefinitionForm, self).clean()
        if not cleaned_data.get('flag_name'):
            self.add_error("flag_name", "Mask name is required when flag definitions are enabled.")
        values_for_bits = cleaned_data.get('values_for_bits')
        values = cleaned_data.get('values')
        bits = cleaned_data.get('bits')
        description = cleaned_data.get('description')

        if not bits:
            self.add_error('bits', 'Mask bits is required when flag definitions are enabled.')
        if not values_for_bits:
            self.add_error("values_for_bits", "Values (bits) is required when flag definitions are enabled")
            return
        if not values:
            self.add_error("values_for_bits", "Values (bits) is required when flag definitions are enabled")
            return
        if not description:
            self.add_error('description', "Please enter a description for this flag definition.")
        if len(values_for_bits.split(",")) != len(values.split(",")):
            self.add_error("values_for_bits", "Values (bits) and Values must have an equal number of entries.")
