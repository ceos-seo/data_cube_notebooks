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

from data_cube_ui.models import Baseline

from data_cube_ui.forms import GeospatialForm as GeospatialFormBase

"""
File designed to house the different forms for taking in user input in the web application.  Forms
allow for input validation and passing of data.  Includes forms for creating Queries to be ran.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:

years_range = list(range(1990, datetime.datetime.now().year+1))

class DataSelectForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    """

    title = forms.CharField(widget=forms.HiddenInput())
    description = forms.CharField(widget=forms.HiddenInput())

    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    #index+1 so jan==1
    months_sel = [(index+1, month) for index, month in enumerate(months)]
    baseline_selection = forms.MultipleChoiceField(help_text='Select the month(s) that will be used to create the baseline. Scenes from the selected months that occur before the selected scene will be used to form a baseline.', label="Baseline Period:", choices=months_sel, widget=forms.SelectMultiple(attrs={'class': 'field-long tooltipped'}))

class GeospatialForm(GeospatialFormBase):
    def __init__(self, acquisition_list=None, *args, **kwargs):
        super(GeospatialForm, self).__init__(*args, **kwargs)
        self.fields.pop('time_start')
        self.fields.pop('time_end')
        scene_sel = reversed([(str(index)+"-"+date.strftime("%Y/%m/%d %H:%M UTC"), date.strftime("%Y/%m/%d %H:%M UTC")) for index, date in enumerate(acquisition_list)])
        self.fields['scene_selection'] = forms.ChoiceField(help_text='Select a scene to perform NDVI differencing on.', label="Scene Selection:", choices=scene_sel, widget=forms.Select(attrs={'class': 'field-long tooltipped'}))
