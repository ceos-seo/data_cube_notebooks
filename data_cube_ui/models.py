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

import datetime
"""
Holds models and base classes common to applications.
Satellites, Areas, etc. are used in every app,
while queries, metadatas, results etc are extended
by apps.
"""


class Satellite(models.Model):
    """
    Stores a single instance of a Satellite object that contains all the information for requests
    submitted.
    Product prefix is added to area product to get the datacube selector.
    These are used to populate UI forms.
    """

    satellite_id = models.CharField(max_length=25, unique=True)
    satellite_name = models.CharField(max_length=25)
    product_prefix = models.CharField(max_length=25)

    date_min = models.DateField('date_min', default=datetime.date.today)
    date_max = models.DateField('date_min', default=datetime.date.today)

    def __str__(self):
        return self.satellite_id


class Area(models.Model):
    """
    Contains an id, a name, valid data bounds (incl. dates), and imagery for the globe.
    fields with "detail" are the bounds for the detail imagery, e.g. as close to valid data bounds
    as possible.
    These are used to populate the main drop down menus in the taskbar.
    """

    area_id = models.CharField(max_length=250, default="", unique=True)
    area_name = models.CharField(max_length=250, default="")

    # geospatial data bounds. This is the BB for use with map, aka the map
    # will use this rect as its main view.
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    # map imagery data.
    # main imagery wraps the entire earth. This will end up looking bad, but will prevent stretching of the smaller imagery.
    # defaults to the usual -180,-101.25 -> 180,101.25 for the natgeo map.
    main_imagery = models.CharField(max_length=250, default="")
    # detail imagery will be the image that the user ends up seeing.
    detail_imagery = models.CharField(max_length=250, default="")
    #holds the thumbnail view for the region selection page.
    thumbnail_imagery = models.CharField(max_length=250, default="")
    # holds the bounds for the detail imagery, as this will vary based on the
    # desired area etc.
    detail_latitude_min = models.FloatField(default=0)
    detail_latitude_max = models.FloatField(default=0)
    detail_longitude_min = models.FloatField(default=0)
    detail_longitude_max = models.FloatField(default=0)

    satellites = models.ManyToManyField(Satellite)

    def __str__(self):
        return self.area_id


class Compositor(models.Model):
    """
    Stores a compositor including a human readable name and an id.
    The id is interpretted in each app.
    These are used to populate UI forms.
    """

    compositor_id = models.CharField(max_length=25, unique=True)
    compositor_name = models.CharField(max_length=25)


class Baseline(models.Model):
    """
    stores a baseline type. E.g. mean, composite, etc. Used for change
    detection applications.
    """

    baseline_id = models.CharField(max_length=25, unique=True)
    baseline_name = models.CharField(max_length=25)


class AnimationType(models.Model):
    """
    Stores a single instance of an animation type. Includes human readable, id, variable and band.
    These correspond to the datatypes and bands found in tasks.py for the animation enabled apps.
    Used to populate UI forms.
    Band number and data variable are interpretted at the app level in tasks.py.
    """
    type_id = models.CharField(max_length=25, default="None", unique=True)
    app_name = models.CharField(max_length=25, default="None")
    type_name = models.CharField(max_length=25, default="None")
    data_variable = models.CharField(max_length=25, default="None")
    band_number = models.CharField(max_length=25, default="None")


class Application(models.Model):
    """
    Database representation of the Application table that holds all of the UI Applications.
    """

    application_id = models.CharField(max_length=250, default="")
    application_name = models.CharField(max_length=250, default="")
    areas = models.ManyToManyField(Area)
    satellites = models.ManyToManyField(Satellite)

    color_scale = models.CharField(max_length=250, default="", blank=True, null=True)

    def __str__(self):
        return self.application_id


class ToolInfo(models.Model):
    """
    Stores images and information for the region selection page for each tool.  Information includes
    the descriptions seen on the page as well as their respective images.
    """

    image_path = models.CharField(max_length=100)
    image_title = models.CharField(max_length=50)
    image_description = models.CharField(max_length=500)

    application = models.ForeignKey(Application)


##############################################################################################################
# Begin base classes for apps - Query, metadata, results, result types. Extends only in the case of app
# specific elements.
##############################################################################################################
class Query(models.Model):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted. Requires any app specific elements implemented elsewhere, along with the generate
    query id function.
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

    #query info for dc data.
    platform = models.CharField(max_length=25, default="")
    product = models.CharField(max_length=50, default="")

    time_start = models.DateTimeField('time_start')
    time_end = models.DateTimeField('time_end')
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    #false by default, only change is false-> true
    complete = models.BooleanField(default=False)

    class Meta:
        abstract = True

    # Default behavior, may or may not be overriden by apps.
    def generate_query_id(self):
        """
        Creates a Query ID based on a number of different attributes including start_time, end_time
        latitude_min and max, longitude_min and max, measurements, platform, product, and query_type

        Returns:
            query_id (string): The ID of the query built up by object attributes.
        """
        query_id = self.time_start.strftime("%Y-%m-%d") + '-' + self.time_end.strftime("%Y-%m-%d") + '-' + str(
            self.latitude_max) + '-' + str(self.latitude_min) + '-' + str(self.longitude_max) + '-' + str(
                self.longitude_min) + '-' + self.platform + '-' + self.product
        return query_id

    def _is_cached(self, result_class):
        return result_class.objects.filter(query_id=self.query_id).exists()

    @classmethod
    def _fetch_query_object(cls, query_id, user_id):
        try:
            return cls.objects.get(query_id=query_id, user_id=user_id)
        except:
            return None


class Metadata(models.Model):
    """
    Stores a single instance of a Metadata object that contains all the information for requests
    submitted. Functions are used for template display. Currently using comma seperated
    values for easy splitting/formatting.
    """

    #meta
    query_id = models.CharField(max_length=1000, default="", unique=True)

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

    class Meta:
        abstract = True

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
        return zip(self.acquisition_list_as_list(),
                   self.clean_pixels_list_as_list(), self.clean_pixels_percentages_as_list())


class Result(models.Model):
    """
    Stores a single instance of a Result object that contains all the information for requests
    submitted. This is also used to transmit information (status, progress) to the client
    """

    #meta
    query_id = models.CharField(max_length=1000, default="", unique=True)
    #either OK or ERROR or WAIT
    status = models.CharField(max_length=100, default="")

    scenes_processed = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)

    #geospatial bounds.
    latitude_max = models.FloatField(default=0)
    latitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)

    #default display result.
    result_path = models.CharField(max_length=250, default="")

    class Meta:
        abstract = True


class ResultType(models.Model):
    """
    Stores a single instance of a ResultType object that contains all the information for requests
    submitted. This is extended by different apps when other result type data is required.
    """

    satellite_id = models.CharField(max_length=25)
    result_id = models.CharField(max_length=25)
    result_type = models.CharField(max_length=25)

    class Meta:
        abstract = True
