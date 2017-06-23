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
    dataset_type = forms.ModelChoiceField(
        queryset=None,
        label="Source Dataset Type",
        help_text="Select an existing source dataset type for this ingestion configuration.",
        error_messages={'required': 'Source Dataset Type is required.'},
        widget=forms.Select(attrs={'class': "onchange_refresh",
                                   'onchange': "update_forms()"}),
        required=False)

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

    instrument = forms.CharField(
        label="Instrument",
        help_text="Enter this dataset's instrument. This should correspond with the source dataset type.",
        error_messages={'required': 'Instrument is required.'},
        widget=forms.TextInput(attrs={'placeholder': "ETM"}))

    keywords = forms.CharField(
        label="Keywords",
        help_text="Enter keywords that can be used to identify your dataset.",
        error_messages={'required': 'Keywords is required.'},
        initial="AU/GA,NASA/GSFC/SED/ESD/LANDSAT,REFLECTANCE,ETM+,TM,OLI,EARTH SCIENCE",
        widget=forms.TextInput(
            attrs={'placeholder': "AU/GA,NASA/GSFC/SED/ESD/LANDSAT,REFLECTANCE,ETM+,TM,OLI,EARTH SCIENCE"}))

    platform = forms.CharField(
        label="Platform",
        help_text="Enter your dataset's platform. This should correspond with the source dataset type.",
        error_messages={'required': 'Platform is required.'},
        widget=forms.TextInput(attrs={'placeholder': "LANDSAT_7"}))

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

    product_suite = forms.CharField(
        label="Product Suite",
        help_text="Enter the product suite of your dataset.",
        error_messages={'required': 'Product Suite is required.'},
        widget=forms.TextInput(attrs={'placeholder': "USGS Landsat Collection 1"}))

    project = forms.CharField(
        label="Project",
        help_text="Enter your/your dataset's project.",
        error_messages={'required': 'Project is required.'},
        initial="CEOS",
        widget=forms.TextInput(attrs={'placeholder': "CEOS"}))

    coverage_content_type = forms.CharField(
        label="Coverage Content Type",
        help_text="Enter the coverage content type for your dataset.",
        error_messages={'required': 'Coverage Content Type is required.'},
        initial="physicalMeasurement",
        widget=forms.TextInput(attrs={'placeholder': "physicalMeasurement"}))

    references = forms.CharField(
        label="References",
        help_text="Enter any reference links for your dataset.",
        error_messages={'required': 'References is required.'},
        widget=forms.TextInput(attrs={'placeholder': "http://dx.doi.org/10.3334/ORNLDAAC/1146"}))

    license = forms.CharField(
        label="License",
        help_text="Enter a link to or name of your dataset's license.",
        error_messages={'required': 'License is required.'},
        widget=forms.TextInput(attrs={'placeholder': "https://creativecommons.org/licenses/by/4.0/"}))

    naming_authority = forms.CharField(
        label="Naming Authority",
        help_text="Enter the naming authority for your dataset.",
        error_messages={'required': 'Naming Authority is required.'},
        widget=forms.TextInput(attrs={'placeholder': "gov.usgs"}))

    acknowledgement = forms.CharField(
        label="Acknowledgement",
        help_text="Enter any required acknowledgement for your dataset.",
        widget=forms.TextInput(
            attrs={'placeholder': "Landsat data is provided by the United States Geological Survey (USGS)."}),
        error_messages={'required': 'Acknowledgement is required.'})

    def __init__(self, *args, **kwargs):
        super(IngestionMetadataForm, self).__init__(*args, **kwargs)
        self.fields['dataset_type'].queryset = DatasetType.objects.using('agdc').filter(~Q(
            definition__has_keys=['managed']) & Q(definition__has_keys=['measurements']))


class IngestionStorageForm(forms.Form):

    crs = forms.CharField(
        label="CRS",
        help_text="Please enter the EPSG code of your desired CRS.",
        widget=forms.TextInput(attrs={'placeholder': "EPSG:4326"}),
        initial="EPSG:4326",
        required=True,
        validators=[validate_slug],
        error_messages={'required': 'CRS is required. Please enter a valid EPSG code in the metadata panel.'})

    units = ["degrees", "meters"]
    crs_units = forms.ChoiceField(
        label="CRS Units",
        help_text="Select the units of your chosen CRS. For Mercator projections this will be meters, while projections like EPSG:4326 will be degrees.",
        choices=((unit, unit) for unit in units),
        initial="degrees",
        required=True)

    tile_size_longitude = forms.FloatField(
        label="Longitude Tile Size",
        help_text="Enter your desired tile size in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution.",
        required=True,
        initial=0.943231048326,
        error_messages={'required': 'Tile size is required. Please enter a valid number in the Metadata panel.'})
    tile_size_latitude = forms.FloatField(
        label="Latitude Tile Size",
        help_text="Enter your desired tile size in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution.",
        required=True,
        initial=0.943231048326,
        error_messages={'required': 'Tile size is required. Please enter a valid number in the Metadata panel.'})

    resolution_longitude = forms.FloatField(
        label="Latitude Resolution",
        help_text="Enter your desired resolution in the units of your CRS. This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution",
        required=True,
        initial=0.000269494585236,
        error_messages={
            'required': 'Resoultion values are required. Please enter a valid number in the Metadata panel.'
        })
    resolution_latitude = forms.FloatField(
        label="Longitude Resolution",
        help_text="Enter your desired resolution in the units of your CRS. The latitude resolution must be less than zero (negative). This can be a floating point number, but please ensure that your tile size is evenly divisible by the resolution",
        required=True,
        initial=-0.000269494585236,
        error_messages={
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


class IngestionMeasurementsForm(forms.Form):
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
