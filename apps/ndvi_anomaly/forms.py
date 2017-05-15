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

from apps.dc_algorithm.models import Area, Compositor
from apps.dc_algorithm.forms import DataSelectionForm as DataSelectionFormBase


class DataSelectionForm(DataSelectionFormBase):
    time_start = None
    time_end = None

    def __init__(self, *args, acquisition_list=None, **kwargs):
        super(DataSelectionForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        if cleaned_data.get('latitude_min') > cleaned_data.get('latitude_max'):
            self.add_error(
                'latitude_min',
                "Please enter a valid pair of latitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('longitude_min') > cleaned_data.get('longitude_max'):
            self.add_error(
                'longitude_min',
                "Please enter a valid pair of longitude values where the lower bound is less than the upper bound.")


class AdditionalOptionsForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    Init function to initialize dynamic forms.
    """

    scene_selection = forms.CharField(
        help_text='Select a scene to perform NDVI differencing on.',
        label="Scene Selection:",
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    months = [
        "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
        "December"
    ]
    #index+1 so jan==1
    months_sel = [(index + 1, month) for index, month in enumerate(months)]
    baseline_selection = forms.MultipleChoiceField(
        help_text='Select the month(s) that will be used to create the baseline. Scenes from the selected months that occur before the selected scene will be used to form a baseline.',
        label="Baseline Period:",
        choices=months_sel,
        widget=forms.SelectMultiple(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, *args, acquisition_list=None, **kwargs):
        datacube_platform = kwargs.pop('datacube_platform', None)
        super(AdditionalOptionsForm, self).__init__(*args, **kwargs)
        if acquisition_list is not None:
            scene_sel = [(date.strftime("%Y-%m-%d"), date.strftime("%Y/%m/%d"))
                         for index, date in enumerate(sorted(acquisition_list))]
            self.fields['scene_selection'] = forms.CharField(
                help_text='Select a scene to perform NDVI differencing on.',
                label="Scene Selection:",
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}, choices=scene_sel))
