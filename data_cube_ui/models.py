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

"""
Models file that holds all the classes representative of the database tabeles.  Allows for queries
to be created for basic CRUD operations.
"""

class Satellite(models.Model):
    """
    Stores a single instance of a Satellite object that contains all the information for requests
    submitted.
    """

    satellite_id = models.CharField(max_length=25)
    satellite_name = models.CharField(max_length=25)


class Area(models.Model):
    """
    Stores a single instance of a Area object that contains all the information for requests
    submitted.
    """

    area_id = models.CharField(max_length=250, default="")
    area_name = models.CharField(max_length=250, default="")
    area_product = models.CharField(max_length=250, default="")

    # geospatial data bounds. This is the BB for use with map, aka the map
    # will use this rect as its main view.
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    date_min = models.DateField('date_min')
    date_max = models.DateField('date_min')

    # map imagery data.
    # main imagery wraps the entire earth. This will end up looking bad, but will prevent stretching of the smaller imagery.
    # defaults to the usual -180,-101.25 -> 180,101.25 for the natgeo map.
    main_imagery = models.CharField(max_length=250, default="")
    # detail imagery will be the image that the user ends up seeing.
    detail_imagery = models.CharField(max_length=250, default="")
    # holds the bounds for the detail imagery, as this will vary based on the
    # desired area etc.
    detail_latitude_min = models.FloatField(default=0)
    detail_latitude_max = models.FloatField(default=0)
    detail_longitude_min = models.FloatField(default=0)
    detail_longitude_max = models.FloatField(default=0)

class Compositor(models.Model):
    """
    Stores a compositor including a human readable name and an id.
    """
    compositor = models.CharField(max_length=25)
    compositor_id = models.CharField(max_length=25)

class AnimationType(models.Model):
    """
    Stores a single instance of an animation type. Includes human readable, id, variable and band.
    These correspond to the datatypes and bands found in tasks.py for the water detection tool only.
    To add or remove one of these, consult tasks.py to figure out what needs to be added/removed.
    Unique to the TSM and the Water detection but still the same model.
    """
    type_id = models.CharField(max_length=25, default="None")
    app_name = models.CharField(max_length=25, default="None")
    type_name = models.CharField(max_length=25, default="None")
    data_variable = models.CharField(max_length=25, default="None")
    band_number = models.CharField(max_length=25, default="None")
