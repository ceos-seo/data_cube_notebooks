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

import datetime

from .models import ResultType
from apps.dc_algorithm.models import Area


class DataSelectionForm(forms.Form):

    two_column_format = True

    title = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'hidden_form_title'}))
    description = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'hidden_form_description'}))
    platform = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'hidden_form_platform'}))
    area_id = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'hidden_form_id'}))

    latitude = forms.FloatField(
        label='Latitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))

    longitude = forms.FloatField(
        label='Longitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))
    time_start = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(
            attrs={'class': 'datepicker field-divided',
                   'placeholder': '01/01/2010',
                   'required': 'required'}))
    time_end = forms.DateField(
        label='End Date',
        widget=forms.DateInput(
            attrs={'class': 'datepicker field-divided',
                   'placeholder': '01/02/2010',
                   'required': 'required'}))

    def __init__(self, *args, **kwargs):
        time_start = kwargs.pop('time_start', None)
        time_end = kwargs.pop('time_end', None)
        area = kwargs.pop('area', None)
        super(DataSelectionForm, self).__init__(*args, **kwargs)
        #meant to prevent this routine from running if trying to init from querydict.
        if time_start and time_end:
            self.fields['time_start'] = forms.DateField(
                initial=time_start.strftime("%m/%d/%Y"),
                label='Start Date',
                widget=forms.DateInput(attrs={'class': 'datepicker field-divided',
                                              'required': 'required'}))
            self.fields['time_end'] = forms.DateField(
                initial=time_end.strftime("%m/%d/%Y"),
                label='End Date',
                widget=forms.DateInput(attrs={'class': 'datepicker field-divided',
                                              'required': 'required'}))
        if area:
            self.fields['latitude'].widget.attrs.update({'min': area.latitude_min, 'max': area.latitude_max})
            self.fields['longitude'].widget.attrs.update({'min': area.longitude_min, 'max': area.longitude_max})


class AdditionalOptionsForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    Init function to initialize dynamic forms.
    """

    #these are done in the init funct.
    query_type = forms.ModelChoiceField(
        queryset=None,
        to_field_name="result_id",
        empty_label=None,
        help_text='Select the type of plot that will be generated.',
        label='Plot Variables:',
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, *args, **kwargs):
        datacube_platform = kwargs.pop('datacube_platform', None)
        super(AdditionalOptionsForm, self).__init__(*args, **kwargs)
        self.fields["query_type"].queryset = ResultType.objects.all()
