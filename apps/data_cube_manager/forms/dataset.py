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


class DatasetFilterForm(forms.Form):
    """Filter datasets based on the dataset type and metadata attributes on the eo metadata type"""

    dataset_type_ref = forms.ModelMultipleChoiceField(
        queryset=None,
        label="Products",
        widget=forms.SelectMultiple(attrs={'class': "onchange_filter"}),
        required=False)

    latitude_min = forms.FloatField(
        label='Min Latitude',
        validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)],
        required=False,
        widget=forms.NumberInput(attrs={'class': 'field-divided onchange_filter',
                                        'step': "any",
                                        'min': -90,
                                        'max': 90}))
    latitude_max = forms.FloatField(
        label='Max Latitude',
        validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)],
        required=False,
        widget=forms.NumberInput(attrs={'class': 'field-divided onchange_filter',
                                        'step': "any",
                                        'min': -90,
                                        'max': 90}))
    longitude_min = forms.FloatField(
        label='Min Longitude',
        validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)],
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'field-divided onchange_filter',
                   'step': "any",
                   'min': -180,
                   'max': 180}))
    longitude_max = forms.FloatField(
        label='Max Longitude',
        validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)],
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'field-divided onchange_filter',
                   'step': "any",
                   'min': -180,
                   'max': 180}))
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'class': 'datepicker field-divided onchange_filter',
                                      'placeholder': '01/01/2010'}))
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'class': 'datepicker field-divided onchange_filter',
                                      'placeholder': '01/02/2010'}))

    def __init__(self, *args, **kwargs):
        """Initialize the dataset filtering form. If a dataset type id is provided, set the default"""
        dataset_type_ref = kwargs.pop('dataset_type_id', None)
        super(DatasetFilterForm, self).__init__(*args, **kwargs)
        self.fields['dataset_type_ref'].queryset = DatasetType.objects.using('agdc').all()
        if dataset_type_ref is not None:
            self.fields['dataset_type_ref'].initial = [dataset_type_ref]

    def clean(self):
        """Clean the dataset filter form

        This uses manually set defaults to allow for 'blank' inputs while still having values.
        Does some weird boolean conversion since there's no way to do a drop down boolean field.

        Adds a small padding to the lat/lon bounds to ensure that there are no silly rounding issues
        """
        cleaned_data = {
            'latitude_min': -90,
            'latitude_max': 90,
            'longitude_min': -180,
            'longitude_max': 180,
            'start_date': datetime.date(1900, 1, 1),
            'end_date': datetime.date.today()
        }
        cleaned_data.update({key: val for key, val in super(DatasetFilterForm, self).clean().items() if val})

        if cleaned_data.get('latitude_min') > cleaned_data.get('latitude_max'):
            self.add_error(
                'latitude_min',
                "Please enter a valid pair of latitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('longitude_min') > cleaned_data.get('longitude_max'):
            self.add_error(
                'longitude_min',
                "Please enter a valid pair of longitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('start_date') >= cleaned_data.get('end_date'):
            self.add_error('start_date',
                           "Please enter a valid start and end time range where the start is before the end.")

        # this id done to get rid of some weird rounding issues - a lot of the solid BBs end up being 3.999999999123412 rather than
        # the expected 4
        cleaned_data['latitude_min'] -= 0.01
        cleaned_data['longitude_min'] -= 0.01
        cleaned_data['latitude_max'] += 0.01
        cleaned_data['longitude_max'] += 0.01

        self.cleaned_data = cleaned_data
