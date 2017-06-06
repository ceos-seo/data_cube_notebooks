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

from .models import AnimationType
from apps.dc_algorithm.models import Area, Compositor
from apps.dc_algorithm.forms import DataSelectionForm


class DataSelectionForm(DataSelectionForm):
    time_start = forms.ChoiceField(
        help_text='Select the date of a historic acquisition.',
        label="Beginning Year",
        choices=[(number, number) for number in range(1999, 2017)],
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    time_end = forms.ChoiceField(
        help_text='Select the date of a new acquisition',
        label="Ending Year",
        choices=[(number, number) for number in range(1999, 2017)],
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, *args, **kwargs):
        time_start = kwargs.pop('time_start', None)
        time_end = kwargs.pop('time_end', None)
        area = kwargs.pop('area', None)
        super(DataSelectionForm, self).__init__(*args, **kwargs)
        #meant to prevent this routine from running if trying to init from querydict.
        if time_start and time_end:
            self.fields['time_start'] = forms.ChoiceField(
                help_text='Select the date of a historic acquisition.',
                label="Beginning Year",
                choices=[(number, number) for number in range(1999, 2017)],
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}))
            self.fields['time_end'] = forms.ChoiceField(
                help_text='Select the date of a new acquisition',
                label="Ending Year",
                choices=[(number, number) for number in range(1999, 2017)],
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

        if area:
            self.fields['latitude_min'].widget.attrs.update({'min': area.latitude_min, 'max': area.latitude_max})
            self.fields['latitude_max'].widget.attrs.update({'min': area.latitude_min, 'max': area.latitude_max})
            self.fields['longitude_min'].widget.attrs.update({'min': area.longitude_min, 'max': area.longitude_max})
            self.fields['longitude_max'].widget.attrs.update({'min': area.longitude_min, 'max': area.longitude_max})


class AdditionalOptionsForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    Init function to initialize dynamic forms.
    """

    animated_product = forms.ModelChoiceField(
        queryset=None,
        to_field_name="id",
        empty_label=None,
        help_text='Generate a .gif containing coastal change over time.',
        label='Generate Time Series Animation',
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, *args, **kwargs):
        datacube_platform = kwargs.pop('datacube_platform', None)
        super(AdditionalOptionsForm, self).__init__(*args, **kwargs)
        self.fields["animated_product"].queryset = AnimationType.objects.all().order_by('pk')
