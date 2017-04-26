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
from data_cube_ui.models import Area, Compositor, AnimationType
"""
File designed to house the different forms for taking in user input in the web application.  Forms
allow for input validation and passing of data.  Includes forms for creating Queries to be ran.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:


class DataSelectForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    Init function to initialize dynamic forms.
    """

    #these are done in the init funct.
    query_type = forms.ChoiceField(
        label='Result Type (Map view/png):', widget=forms.Select(attrs={'class': 'field-long'}))

    title = forms.CharField(widget=forms.HiddenInput())
    description = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, satellite_id=None, *args, **kwargs):
        super(DataSelectForm, self).__init__(*args, **kwargs)
        if satellite_id is not None:
            #populate the results list and recreate the form element.
            result_types = ResultType.objects.filter(satellite_id=satellite_id)

            results_list = [(result.result_id, result.result_name) for result in result_types]
            self.fields["query_type"] = forms.ChoiceField(
                help_text='Select the type of image you would like displayed.',
                label='Result Type (Map view/png):',
                choices=results_list,
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

            compositor_list = [(compositor.compositor_id, compositor.compositor_name)
                               for compositor in Compositor.objects.all()]
            self.fields["compositor"] = forms.ChoiceField(
                help_text='Select the method by which the "best" pixel will be chosen.',
                label="Compositing Method:",
                choices=compositor_list,
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

            animation_list = [(animation_type.type_id, animation_type.type_name)
                              for animation_type in AnimationType.objects.filter(
                                  app_name__in=["custom_mosaic_tool", "all"]).order_by('app_name', 'type_id')]
            self.fields["animated_product"] = forms.ChoiceField(
                label='Generate Time Series Animation',
                widget=forms.Select(attrs={'class': 'field-long tooltipped'}),
                choices=animation_list,
                help_text='Generate a .gif containing either scene data or the cumulative mosaic over time. This is not compatible with median pixel mosaics.'
            )
