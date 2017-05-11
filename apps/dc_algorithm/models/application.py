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

from django.db import models
from django.core.exceptions import ValidationError

import datetime
import uuid


class Application(models.Model):
    """Model containing the applications that are displayed on the UI.

    The Application model is used to control application attributes. An example of an application
    could be:
        NDVI: Computes the NDVI over any given region.
        Water Detection: Generates water detection images over a given region
        etc.

    This model is used in templates to create dropdown menus/route users to different apps.

    Attributes:
        id: Unique id used to identify apps.
        name: Human readable name for the app. Will be featured on UI pages.
        areas: M2M field outlining what areas should be displayed for each app. If we have an inland
            area with no standing water bodies, then we may not want to display water detection here
            so we would leave it unselected.
        satellites: M2M field outlining what satellties should be displayed for each tool. If water detection
            does not use SAR data, we would select only optical satellites here.
        color_scale: path to a color scale image to be displayed in the main tool view. If no color scale is
            necessary, this should be left blank/null.

    """

    id = models.CharField(max_length=250, default="", unique=True, primary_key=True)
    name = models.CharField(max_length=250, default="")
    areas = models.ManyToManyField(Area)
    satellites = models.ManyToManyField(Satellite)

    color_scale = models.CharField(max_length=250, default="", blank=True, null=True)

    def __str__(self):
        return self.id
