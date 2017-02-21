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

# Author: AHDS
# Creation date: 2016-06-23
# Modified by: MAP
# Last modified date:

class Query(models.Model):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted.
    """

    #meta
    query_id = models.CharField(max_length=1000, default="")
    area_id = models.CharField(max_length=100, default="")
    title = models.CharField(max_length=100, default="")
    description = models.CharField(max_length=10000, default="")

    #app specific
    user_id = models.CharField(max_length=25, default="")
    query_start = models.DateTimeField('query_start')
    query_end = models.DateTimeField('query_end')
    query_type = models.CharField(max_length=25, default="")

    #query info for dc data.
    platform = models.CharField(max_length=25, default="")
    product = models.CharField(max_length=25, default="")
    product_type = models.CharField(max_length=25, default="")
    measurements = models.CharField(max_length=100, default="")
    time_start = models.DateTimeField('time_start')
    time_end = models.DateTimeField('time_end')
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    #false by default, only change is false-> true
    complete = models.BooleanField(default=False)

    id = models.AutoField(primary_key=True)

class Metadata(models.Model):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted.
    """

    #meta
    query_id = models.CharField(max_length=1000, default="")

    #geospatial bounds.
    latitude_max = models.FloatField(default=0)
    latitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)

    #meta attributes
    scene_count = models.IntegerField(default=0)
    pixel_count = models.IntegerField(default=0)
    clean_pixel_count = models.IntegerField(default=0)
    percentage_clean_pixels = models.FloatField(default=0)
    # comma seperated dates representing individual acquisitions
    # followed by comma seperated numbers representing pixels per scene.
    acquisition_list = models.CharField(max_length=100000, default="")
    clean_pixels_per_acquisition = models.CharField(max_length=100000, default="")
    clean_pixel_percentages_per_acquisition = models.CharField(max_length=100000, default="")
    #more to come?

    def acquisition_list_as_list(self):
        """
        Splits the list of acquisitions into a list.

        Returns:
            acquisition_list (list): List representation of the acquisitions from the database.
        """
        return self.acquisition_list.rstrip(',').split(',')

    def clean_pixels_list_as_list(self):
        """
        Splits the list of clean pixels into a list.

        Returns:
            clean_pixels_per_acquisition (list): List representation of the acquisitions from the
            database.
        """
        return self.clean_pixels_per_acquisition.rstrip(',').split(',')

    def clean_pixels_percentages_as_list(self):
        """
        Splits the list of clean pixels with percentages into a list.

        Returns:
            clean_pixel_percentages_per_acquisition_list (list): List representation of the
            acquisitions from the database.
        """
        return self.clean_pixel_percentages_per_acquisition.rstrip(',').split(',')

    def acquisitions_dates_with_pixels_percentages(self):
        """
        Creates a zip file with a number of lists included as the content

        Returns:
            zip file: Zip file combining three different lists (acquisition_list_as_list(),
            clean_pixels_list_as_list(), clean_pixels_percentages_as_list())
        """
        return zip(self.acquisition_list_as_list(), self.clean_pixels_list_as_list(), self.clean_pixels_percentages_as_list())

class Result(models.Model):
    """
    Stores a single instance of a Result object that contains all the information for requests
    submitted.
    """

    #meta
    query_id = models.CharField(max_length=1000, default="")
    #either OK or ERROR or WAIT
    status = models.CharField(max_length=100, default="")

    scenes_processed = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)

    #geospatial bounds.
    latitude_max = models.FloatField(default=0)
    latitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)

    #result path + other data. More to come.
    result_path = models.CharField(max_length=250, default="")
    result_filled_path = models.CharField(max_length=250, default="")
    data_path = models.CharField(max_length=250, default="")

class Area(models.Model):
    """
    Stores a single instance of a Area object that contains all the information for requests
    submitted.
    """

    area_id = models.CharField(max_length=250, default="")
    area_name = models.CharField(max_length=250, default="")
    area_product = models.CharField(max_length=250, default="")

    #geospatial data bounds. This is the BB for use with map, aka the map will use this rect as its main view.
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    #map imagery data.
    #main imagery wraps the entire earth. This will end up looking bad, but will prevent stretching of the smaller imagery.
    #defaults to the usual -180,-101.25 -> 180,101.25 for the natgeo map.
    main_imagery = models.CharField(max_length=250, default="")
    #detail imagery will be the image that the user ends up seeing.
    detail_imagery = models.CharField(max_length=250, default="")
    #holds the bounds for the detail imagery, as this will vary based on the desired area etc.
    detail_latitude_min = models.FloatField(default=0)
    detail_latitude_max = models.FloatField(default=0)
    detail_longitude_min = models.FloatField(default=0)
    detail_longitude_max = models.FloatField(default=0)

class SampleModel(models.Model):
    """
    A sample model for building the form.
    """

    satellite_id = models.CharField(max_length=25)
    sample_model_id = models.CharField(max_length=25)
    sample_model_text = models.CharField(max_length=25)
