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
from django.db.models import Q

import re
import datetime

from apps.data_cube_manager.models import DatasetType


class IngestionMetadataForm(forms.Form):
    """Form meant to validate all metadata fields for an ingestion configuration file."""

    dataset_type_ref = forms.ModelChoiceField(
        queryset=None,
        label="Source Dataset Type",
        help_text="Select an existing source dataset type for this ingestion configuration.",
        error_messages={'required': 'Source Dataset Type is required.'},
        widget=forms.Select(attrs={'class': "onchange_refresh",
                                   'onchange': "update_forms()"}),
        required=True)

    output_type = forms.CharField(
        label="Output Type Name",
        help_text="Enter a description for this new ingested dataset",
        error_messages={'required': 'Output Type Name is required.'},
        widget=forms.TextInput())

    description = forms.CharField(
        label="Description",
        help_text="Enter a description for this new ingested dataset",
        error_messages={'required': "Description is required."},
        widget=forms.TextInput())

    location = forms.CharField(
        label="Data Storage Location",
        help_text="Enter the absolute base path for your storage units",
        error_messages={'required': 'Data Storage Location is required.'},
        widget=forms.TextInput(attrs={'placeholder': "/datacube/ingested_data/"}))
    file_path_template = forms.CharField(
        label="Storage Unit Naming Template",
        help_text="Enter the naming template for your storage units. Available variables include {tile_index[0]}, {tile_index[1]}, and {start_time}. This will be appended to the data storage location to create the path to your storage units.",
        error_messages={'required': 'Storage Unit Naming Template is required.'},
        widget=forms.TextInput(attrs={
            'placeholder':
            "LS7_ETM_LEDAPS/General/LS7_ETM_LEDAPS_4326_{tile_index[0]}_{tile_index[1]}_{start_time}.nc"
        }))

    title = forms.CharField(
        label="Title",
        help_text="Enter a title for your new dataset.",
        error_messages={'required': 'Title is required.'},
        widget=forms.TextInput(attrs={'placeholder': "CEOS Data Cube Landsat Surface Reflectance"}))

    summary = forms.CharField(
        label="Summary",
        help_text="Enter a brief summary describing your dataset.",
        error_messages={'required': 'Summary is required.'},
        widget=forms.TextInput(
            attrs={'placeholder': "Landsat 7 Enhanced Thematic Mapper Plus ARD prepared by NASA on behalf of CEOS."}))

    source = forms.CharField(
        label="Source",
        help_text="Enter the source of your dataset.",
        error_messages={'required': 'Source is required.'},
        widget=forms.TextInput(
            attrs={'placeholder': "LEDAPS surface reflectance product prepared using USGS Collection 1 data."}))

    institution = forms.CharField(
        label="Institution",
        help_text="Enter your institution affiliation",
        error_messages={'required': 'Institution is required.'},
        initial="CEOS",
        widget=forms.TextInput(attrs={'placeholder': "CEOS"}))

    platform = forms.CharField(
        label="Platform",
        help_text="Enter your dataset's platform. This should correspond with the source dataset type.",
        error_messages={'required': 'Platform is required.'},
        widget=forms.TextInput(attrs={'placeholder': "LANDSAT_7"}))

    instrument = forms.CharField(
        label="Instrument",
        help_text="Enter this dataset's instrument. This should correspond with the source dataset type.",
        error_messages={'required': 'Instrument is required.'},
        widget=forms.TextInput(attrs={'placeholder': "ETM"}))

    processing_level = forms.CharField(
        label="Processing Level",
        help_text="Enter the processing level for your dataset.",
        error_messages={'required': 'Processing Level is required.'},
        widget=forms.TextInput(attrs={'placeholder': "L2"}))

    product_version = forms.CharField(
        label="Product Version",
        help_text="Enter your product's version.",
        error_messages={'required': 'Product Version is required.'},
        widget=forms.TextInput(attrs={'placeholder': "2.0.0"}))

    references = forms.CharField(
        label="References",
        help_text="Enter any reference links for your dataset.",
        error_messages={'required': 'References is required.'},
        widget=forms.TextInput(attrs={'placeholder': "http://dx.doi.org/10.3334/ORNLDAAC/1146"}))

    def __init__(self, *args, **kwargs):
        super(IngestionMetadataForm, self).__init__(*args, **kwargs)
        self.fields['dataset_type_ref'].queryset = DatasetType.objects.using('agdc').filter(~Q(
            definition__has_keys=['managed']) & Q(definition__has_keys=['measurements']))


class IngestionBoundsForm(forms.Form):
    """Form meant to validate the ingestion bounds section of the ingestion configuration file."""

    left = forms.FloatField(
        label="Minimum Longitude",
        help_text="Enter your desired minimum longitude ingestion bound. Ensure that the maximum value is greater than the minimum value.",
        required=True,
        initial=-180,
        error_messages={
            'required': 'Ingestion bounding box values are required. Please enter a valid number in the Metadata panel.'
        })

    right = forms.FloatField(
        label="Maximum Longitude",
        help_text="Enter your desired maximum longitude ingestion bound. Ensure that the maximum value is greater than the minimum value.",
        required=True,
        initial=180,
        error_messages={
            'required': 'Ingestion bounding box values are required. Please enter a valid number in the Metadata panel.'
        })

    bottom = forms.FloatField(
        label="Minimum Latitude",
        help_text="Enter your desired minimum latitude ingestion bound. Ensure that the maximum value is greater than the minimum value.",
        required=True,
        initial=-90,
        error_messages={
            'required': 'Ingestion bounding box values are required. Please enter a valid number in the Metadata panel.'
        })

    top = forms.FloatField(
        label="Maximum Latitude",
        help_text="Enter your desired maximum latitude ingestion bound. Ensure that the maximum value is greater than the minimum value.",
        required=True,
        initial=90,
        error_messages={
            'required': 'Ingestion bounding box values are required. Please enter a valid number in the Metadata panel.'
        })

    def clean(self, clean=True):
        cleaned_data = super(IngestionBoundsForm, self).clean()

        if cleaned_data['left'] > cleaned_data['right']:
            self.add_error('left', 'The minimum ingestion bound longitude must be less than the maximum longitude.')
        if cleaned_data['bottom'] > cleaned_data['top']:
            self.add_error('left', 'The minimum ingestion bound latitude must be less than the maximum latitude.')


class IngestionStorageForm(forms.Form):
    """Validate the storage section of the ingestion configuration file

    Added additional validation to ensure that the resolution evenly divides into the tile sizing.
    """

    crs = forms.CharField(
        label="CRS",
        help_text="Please enter the EPSG code of your desired CRS.",
        widget=forms.TextInput(attrs={'placeholder': "EPSG:4326"}),
        initial="EPSG:4326",
        required=True,
        error_messages={'required': 'CRS is required. Please enter a valid EPSG code in the metadata panel.'})

    units = ["degrees", "meters"]
    crs_units = forms.ChoiceField(
        label="CRS Units",
        help_text="Select the units of your chosen CRS. For Mercator projections this will be meters, while projections like EPSG:4326 will be degrees.",
        choices=((unit, unit) for unit in units),
        initial="degrees",
        required=True)

    tile_size_longitude = forms.DecimalField(
        label="Longitude/X Tile Size",
        help_text="Enter your desired tile size in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution.",
        required=True,
        initial=0.943231048326,
        decimal_places=12,
        error_messages={
            'max_decimal_places': "Please ensure that the tile size values do not exceed 12 decimal places.",
            'required': 'Tile size is required. Please enter a valid number in the Metadata panel.'
        })
    tile_size_latitude = forms.DecimalField(
        label="Latitude/Y Tile Size",
        help_text="Enter your desired tile size in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution.",
        required=True,
        initial=0.943231048326,
        decimal_places=12,
        error_messages={
            'max_decimal_places': "Please ensure that the tile size values do not exceed 12 decimal places.",
            'required': 'Tile size is required. Please enter a valid number in the Metadata panel.'
        })

    resolution_longitude = forms.DecimalField(
        label="Longitude/X Resolution",
        help_text="Enter your desired resolution in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution",
        required=True,
        initial=0.000269494585236,
        decimal_places=15,
        error_messages={
            'max_decimal_places': "Please ensure that the resolution values do not exceed 15 decimal places.",
            'required': 'Resoultion values are required. Please enter a valid number in the Metadata panel.'
        })
    resolution_latitude = forms.DecimalField(
        label="Latitude/Y Resolution",
        help_text="Enter your desired resolution in the units of your CRS. The latitude resolution must be less than zero (negative). This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution",
        required=True,
        initial=-0.000269494585236,
        decimal_places=15,
        validators=[validators.MaxValueValidator(0)],
        error_messages={
            'max_decimal_places': "Please ensure that the resolution values do not exceed 15 decimal places.",
            'required': 'Resoultion values are required. Please enter a valid number in the Metadata panel.'
        })

    chunking_longitude = forms.IntegerField(
        label="Longitude Chunk Size",
        help_text="Enter the NetCDF internal chunk size in number of pixels.",
        required=True,
        initial=200,
        error_messages={'required': 'Chunk size is required. Pleaes enter a valid integer in the Metadata panel.'})
    chunking_latitude = forms.IntegerField(
        label="Latitude Chunk Size",
        help_text="Enter the NetCDF internal chunk size in number of pixels.",
        required=True,
        initial=200,
        error_messages={'required': 'Chunk size is required. Pleaes enter a valid integer in the Metadata panel.'})

    def clean(self):
        cleaned_data = super(IngestionStorageForm, self).clean()

        if not self.is_valid():
            return

        float_casting = ['tile_size_latitude', 'tile_size_longitude', 'resolution_latitude', 'resolution_longitude']
        for field in float_casting:
            self.cleaned_data[field] = float(self.cleaned_data[field])

        if (cleaned_data['tile_size_latitude'] / cleaned_data['resolution_latitude']) != int(
                cleaned_data['tile_size_latitude'] / cleaned_data['resolution_latitude']):
            self.add_error(
                'tile_size_latitude',
                "Latitude tile size must be evenly divisible by the latitude resolution. Use a precise calculator to ensure that there are no errors in your ingested data."
            )
        if (cleaned_data['tile_size_longitude'] / cleaned_data['resolution_longitude']) != int(
                cleaned_data['tile_size_longitude'] / cleaned_data['resolution_longitude']):
            self.add_error(
                'tile_size_longitude',
                "Longitude tile size must be evenly divisible by the longitude resolution. Use a precise calculator to ensure that there are no errors in your ingested data."
            )


class IngestionMeasurementForm(forms.Form):
    """Validate the ingestion configuration measurements. These differ slightly from the dataset type fields"""

    name = forms.CharField(
        label="Measurement Name",
        help_text="Please enter the name of the measurement. Spaces and special characters are not allowed.",
        widget=forms.TextInput(attrs={'placeholder': "swir1"}),
        required=True,
        validators=[validate_slug],
        error_messages={
            'required': 'Measurement name is required. Please enter a valid name in the Measurement panel.'
        })

    dtypes = ["float16", "float32", "int8", "int16", "int32", "uint8"]
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

    resampling_method_choices = ['nearest', 'cubic', 'bilinear', 'cubic_spline', 'lanczos', 'average']
    resampling_method = forms.ChoiceField(
        label="Resampling Method",
        help_text="Choose your dataset's resampling method.",
        choices=((method, method) for method in resampling_method_choices),
        initial="nearest",
        required=False)

    src_varname = forms.CharField(
        label="Source Variable Name",
        help_text="Enter the source variable name. This should correspond with the measurement from your dataset type.",
        widget=forms.TextInput(attrs={'placeholder': "sr_band1"}),
        error_messages={
            'required':
            'Source Variable Name is a required field. Please enter a valid string in the Measurement panel.'
        },
        required=True)
    long_name = forms.CharField(
        label="Long Name",
        help_text="Enter a long/descriptive name for this measurement.",
        widget=forms.TextInput(attrs={'placeholder': "Surface Reflectance 0.63-0.69 microns (Red)"}),
        required=False)
    alias = forms.CharField(
        label="Alias",
        help_text="Any any alias that exists for your dataset.",
        widget=forms.TextInput(attrs={'placeholder': "band_3"}),
        required=False)


class IngestionRequestForm(forms.Form):
    """Information required to submit an ingestion request, including start/end date and geographic bounds.

    Can be initialized as a bound form with initial data or as a readonly form

    """

    dataset_type_ref = forms.ModelChoiceField(
        queryset=None,
        label="Source Dataset Type",
        help_text="Select an existing source dataset type for this ingestion configuration.",
        error_messages={'required': 'Source Dataset Type is required.'},
        widget=forms.Select(attrs={'class': "onchange_refresh onchange_filter",
                                   'onchange': "update_forms()"}),
        required=False)

    start_date = forms.DateField(
        label='Start Date',
        error_messages={'required': 'Start date is required.'},
        widget=forms.DateInput(attrs={'class': 'datepicker field-divided onchange_filter',
                                      'placeholder': '01/01/2010'}))
    end_date = forms.DateField(
        label='End Date',
        error_messages={'required': 'End date is required.'},
        widget=forms.DateInput(attrs={'class': 'datepicker field-divided onchange_filter',
                                      'placeholder': '01/02/2010'}))

    latitude_min = forms.FloatField(
        label='Min Latitude',
        validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)],
        error_messages={'required': 'Latitude min is required.'},
        widget=forms.NumberInput(attrs={'class': 'field-divided onchange_filter',
                                        'step': "any",
                                        'min': -90,
                                        'max': 90}))
    latitude_max = forms.FloatField(
        label='Max Latitude',
        validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)],
        error_messages={'required': 'Latitude max is required.'},
        widget=forms.NumberInput(attrs={'class': 'field-divided onchange_filter',
                                        'step': "any",
                                        'min': -90,
                                        'max': 90}))
    longitude_min = forms.FloatField(
        label='Min Longitude',
        validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)],
        error_messages={'required': 'Longitude min is required.'},
        widget=forms.NumberInput(
            attrs={'class': 'field-divided onchange_filter',
                   'step': "any",
                   'min': -180,
                   'max': 180}))
    longitude_max = forms.FloatField(
        label='Max Longitude',
        validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)],
        error_messages={'required': 'Longitude max is required.'},
        widget=forms.NumberInput(
            attrs={'class': 'field-divided onchange_filter',
                   'step': "any",
                   'min': -180,
                   'max': 180}))

    def __init__(self, *args, **kwargs):
        """Initialize the ingestion request form with optional kwargs

        Args:
            initial_vals: dict with form data - sets initial rather than binding
            readonly: boolean value signifying whether or not this form should be modified.
        """
        initial_vals = kwargs.pop('initial', None)
        readonly = kwargs.pop('readonly', None)
        super(IngestionRequestForm, self).__init__(*args, **kwargs)
        self.fields['dataset_type_ref'].queryset = DatasetType.objects.using('agdc').filter(
            Q(definition__has_keys=['managed']) & Q(definition__has_keys=['measurements']))
        if initial_vals:
            for field in initial_vals:
                self.fields[field].initial = initial_vals[field]
        if readonly:
            self.fields['dataset_type_ref'].queryset = DatasetType.objects.using('agdc').filter(
                id=initial_vals['dataset_type_ref'])
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

    def clean(self):
        """Validate the ingestion form - similar to dataset form but with required fields

        Does the +- 0.01 to avoid rounding issues and checks for a max 1deg area.
        """
        cleaned_data = super(IngestionRequestForm, self).clean()

        if not self.is_valid():
            return

        # this id done to get rid of some weird rounding issues - a lot of the solid BBs end up being 3.999999999123412 rather than
        # the expected 4
        cleaned_data['latitude_min'] -= 0.01
        cleaned_data['longitude_min'] -= 0.01
        cleaned_data['latitude_max'] += 0.01
        cleaned_data['longitude_max'] += 0.01

        if cleaned_data.get('latitude_min') > cleaned_data.get('latitude_max'):
            self.add_error(
                'latitude_min',
                "Please enter a valid pair of latitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('longitude_min') > cleaned_data.get('longitude_max'):
            self.add_error(
                'longitude_min',
                "Please enter a valid pair of longitude values where the lower bound is less than the upper bound.")

        area = (cleaned_data.get('latitude_max') - cleaned_data.get('latitude_min')) * (
            cleaned_data.get('longitude_max') - cleaned_data.get('longitude_min'))

        if area > 1.05:
            self.add_error('latitude_min', 'Tasks over an area greater than one square degrees are not permitted.')

        if cleaned_data.get('start_date') > cleaned_data.get('end_date'):
            self.add_error('start_date',
                           "Please enter a valid start and end time range where the start is before the end.")

        if (cleaned_data.get('end_date') - cleaned_data.get('start_date')).days > 367:
            self.add_error('start_date', "Please enter a date range of less than one year.")

        self.cleaned_data = cleaned_data
