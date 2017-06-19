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
import re

from .utils import logical_xor

####
#modeled after
#https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/dataset-type-schema.yaml
#TODO: replace help text with descriptions from above. Potentially figure out how to make this more dynamic
####

comma_separated_float_list_re = re.compile('^([-+]?\d*\.?\d+[,\s]*)+$')
validate_comma_separated_float_list = RegexValidator(
    comma_separated_float_list_re,
    'Enter only floats separated by commas and ensure there are no leading or trailing commas.', 'invalid')


class DatasetTypeMetadataForm(forms.Form):
    """
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
    storage_driver = forms.CharField(
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
        initial="EPSG:4326",
        required=False)
    tile_size_longitude = forms.FloatField(
        label="Tile Size (Longitude)",
        help_text="Tile size of the dataset in pixels - this is set during ingestion and is otherwise unecessary.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
        required=False)
    tile_size_latitude = forms.FloatField(
        label="Tile Size (Latitude)",
        help_text="Tile size of the dataset in pixels - this is set during ingestion and is otherwise unecessary.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
        required=False)
    chunking_time = forms.IntegerField(
        label="Time Chunk Size",
        help_text="Internal chunk size of the dataset in pixels - this is set during ingestion and is otherwise unecessary.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
        required=False)
    chunking_longitude = forms.IntegerField(
        label="Longitude Chunk Size",
        help_text="Internal chunk size of the dataset in pixels - this is set during ingestion and is otherwise unecessary.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
        required=False)
    chunking_latitude = forms.IntegerField(
        label="Latitude Chunk Size",
        help_text="Internal chunk size of the dataset in pixels - this is set during ingestion and is otherwise unecessary.",
        widget=forms.TextInput(attrs={'readonly': "readonly"}),
        initial="",
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

        if logical_xor(cleaned_data['tile_size_latitude'], cleaned_data['tile_size_longitude']):
            self.add_error(
                'tile_size_latitude',
                'Please enter a value for both tile size attributes. If one latitude/longitude attribute is set, the other must be as well.'
            )

        if cleaned_data['resolution_latitude'] and cleaned_data['resolution_longitude'] and not cleaned_data['crs']:
            self.add_error('crs', 'If you specify the latitude and longitude resolution you must also supply a crs.')


class DatasetTypeMeasurementsForm(forms.Form):
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

    #if spectral response is true, then wavelength+response must be provided
    spectral_definition = forms.BooleanField(
        label="Spectral Response",
        help_text="Do you want to enter values for spectral response?",
        initial=False,
        widget=forms.CheckboxInput(attrs={'onchange': "toggle_spectral_definition(this)"}),
        required=False)

    #if mask is true then bits, description, and values must be provided
    flags_definition = forms.BooleanField(
        label="Flags Definition",
        help_text="Do you want to enter mask attributes for this measurement?",
        widget=forms.CheckboxInput(attrs={'onchange': "toggle_flags_definition(this)"}),
        initial=False,
        required=False)

    def __init__(self, *args, **kwargs):
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeMeasurementsForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True


class DatasetTypeSpectralDefinitionForm(forms.Form):
    """
    measurements:
        - name: 'blue'
          aliases: [band_1, blue]
          dtype: int16
          nodata: -9999
          units: '1'
          spectral_definition:
              wavelength: [410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552]
              response: [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0007,0.0008,0.0008,0.0009,0.0009,0.001,0.0013,0.0016,0.002,0.0023,0.0027,0.0042,0.006,0.0086,0.0113,0.0141,0.017,0.0216,0.0268,0.0321,0.037,0.042,0.0471,0.0524,0.0577,0.0633,0.0746,0.1097,0.1564,0.2483,0.3391,0.4058,0.4741,0.5366,0.5856,0.6667,0.688,0.6993,0.7095,0.7165,0.72,0.7326,0.7475,0.7583,0.7714,0.7847,0.7924,0.8002,0.808,0.8156,0.8206,0.8257,0.8308,0.8359,0.8421,0.8526,0.8642,0.8724,0.8824,0.8925,0.9026,0.9069,0.9111,0.9154,0.9196,0.9238,0.9285,0.9332,0.9379,0.9425,0.9472,0.9548,0.9623,0.9698,0.9761,0.9775,0.9788,0.9802,0.9815,0.9837,0.9891,0.9935,0.9978,1.0,0.9952,0.9828,0.9524,0.9219,0.8914,0.8607,0.8293,0.8021,0.7877,0.7732,0.7565,0.7339,0.6859,0.5784,0.4813,0.4002,0.3187,0.2367,0.1324,0.1018,0.0911,0.0804,0.0696,0.0588,0.0532,0.0498,0.0465,0.0431,0.0397,0.0364,0.033,0.0296,0.0261,0.0227,0.0205,0.0184,0.0162,0.014,0.0119,0.0105,0.0093,0.0081,0.0069,0.0058,0.0056,0.0054,0.0052,0.0,0.0]
    """
    wavelength = forms.CharField(
        label="Wavelength",
        help_text="Please enter a list of comma seperated floating point values that define the wavelengths of the spectral response.",
        widget=forms.TextInput(attrs={
            'placeholder':
            "410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552"
        }),
        required=False,
        validators=[validate_comma_separated_float_list])
    response = forms.CharField(
        label="Response",
        help_text="Please enter a list of comma seperated responses that correspond with the wavelength entries. There must be an equal number of wavelength and spectral response entries.",
        widget=forms.TextInput(attrs={
            'placeholder':
            "0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0007,0.0008,0.0008,0.0009,0.0009,0.001,0.0013,0.0016,0.002,0.0023,0.0027,0.0042,0.006,0.0086,0.0113,0.0141,0.017,0.0216,0.0268,0.0321,0.037,0.042,0.0471,0.0524,0.0577,0.0633,0.0746,0.1097,0.1564,0.2483,0.3391,0.4058,0.4741,0.5366,0.5856,0.6667,0.688,0.6993,0.7095,0.7165,0.72,0.7326,0.7475,0.7583,0.7714,0.7847,0.7924,0.8002,0.808,0.8156,0.8206,0.8257,0.8308,0.8359,0.8421,0.8526,0.8642,0.8724,0.8824,0.8925,0.9026,0.9069,0.9111,0.9154,0.9196,0.9238,0.9285,0.9332,0.9379,0.9425,0.9472,0.9548,0.9623,0.9698,0.9761,0.9775,0.9788,0.9802,0.9815,0.9837,0.9891,0.9935,0.9978,1.0,0.9952,0.9828,0.9524,0.9219,0.8914,0.8607,0.8293,0.8021,0.7877,0.7732,0.7565,0.7339,0.6859,0.5784,0.4813,0.4002,0.3187,0.2367,0.1324,0.1018,0.0911,0.0804,0.0696,0.0588,0.0532,0.0498,0.0465,0.0431,0.0397,0.0364,0.033,0.0296,0.0261,0.0227,0.0205,0.0184,0.0162,0.014,0.0119,0.0105,0.0093,0.0081,0.0069,0.0058,0.0056,0.0054,0.0052,0.0,0.0"
        }),
        required=False,
        validators=[validate_comma_separated_float_list])

    def __init__(self, *args, **kwargs):
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeSpectralDefinitionForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DatasetTypeSpectralDefinitionForm, self).clean()
        response = cleaned_data.get('response')
        wavelength = cleaned_data.get('wavelength')

        if not response or not wavelength:
            self.add_error('response', "All spectral response fields are required when spectral response is enabled.")
            return
        if len(response.split(",")) != len(wavelength.split(",")):
            self.add_error('response', "Wavelength and response must have an equivalent number of entries.")


class DatasetTypeFlagsDefinitionForm(forms.Form):
    """
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
        existing_metadata = kwargs.pop('existing_dataset_type', None)
        super(DatasetTypeFlagsDefinitionForm, self).__init__(*args, **kwargs)
        if existing_metadata:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True

    def clean_values(self):
        return self.cleaned_data['values'].strip(",")

    def clean(self):
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
