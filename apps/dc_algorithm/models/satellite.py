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


class Satellite(models.Model):
    """Stores a satellite that exists in the Data Cube

    Stores a single instance of a Satellite object that contains all the information for
    Data Cube requests. This is both used to create Data Cube queries and to display forms
    on the UI.

    Attributes:
        datacube_platform: This should correspond with a Data Cube platform.
            e.g. LANDSAT_5, LANDSAT_7, SENTINEL_1A, etc.
        name: Used to display forms to users
            e.g. Landsat 5, Landsat 7, Sentinel-1A
        product_prefix: In our Data Cube setup, we use product prefixes combined with an area.
            e.g. ls5_ledaps_{vietnam,colombia,australia}, s1a_gamma0_vietnam
            This should be the 'ls5_ledaps_' and 's1a_gamma0_' part of the above examples.
            You should be able to concat the product prefix and an area id to get a valid dataset query.
        date_min and date_max: Satellite valid data date range.
            e.g. If you have LS7 data from 2000-2016, you should use that as the date range.

    """

    datacube_platform = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=25)
    product_prefix = models.CharField(max_length=25)

    date_min = models.DateField('date_min', default=datetime.date.today)
    date_max = models.DateField('date_min', default=datetime.date.today)

    def __str__(self):
        return self.datacube_platform
