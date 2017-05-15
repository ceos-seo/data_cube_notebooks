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
from data_cube_ui.models import Area, Compositor, Baseline
from data_cube_ui.models import Query as BaseQuery, Metadata as BaseMetadata, Result as BaseResult, ResultType as BaseResultType
"""
Models file that holds all the classes representative of the database tabeles.  Allows for queries
to be created for basic CRUD operations.
"""

# Author: AHDS
# Creation date: 2016-06-23
# Modified by: MAP
# Last modified date:


class Query(BaseQuery):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted.
    """

    #baseline is a comma seperated list of months, indexed starting from 1.
    baseline_method = models.CharField(max_length=50, default="median")
    baseline = models.CharField(max_length=50, default="1,2,3,4,5,6,7,8,9,10,11,12")
    #comma seperated index values for scene dates.
    #overriding the base class start/end times. Only start time is used,
    #end time included only for consistency.
    time_start = models.CharField(max_length=5000, default="0")
    time_end = models.CharField(max_length=5000, default="0")

    def get_baseline_name(self):
        months = [
            "January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December"
        ]
        baseline_str = ""
        for baseline in [int(month) for month in self.baseline.split(',')]:
            baseline_str += months[baseline - 1] + ", "
        return baseline_str

    def generate_query_id(self):
        """
        Creates a Query ID based on a number of different attributes including start_time, end_time
        latitude_min and max, longitude_min and max, measurements, platform, product, and query_type

        Returns:
            query_id (string): The ID of the query built up by object attributes.
        """

        query_id = '{start}-{lat_max}-{lat_min}-{lon_min}-{lon_max}-{baseline}-{baseline_method}-{platform}-{product}'
        return query_id.format(
            start=self.time_start,
            lat_max=self.latitude_max,
            lat_min=self.latitude_min,
            lon_max=self.longitude_max,
            lon_min=self.longitude_min,
            baseline=self.baseline,
            baseline_method=self.baseline_method,
            platform=self.platform,
            product=self.product)

    def generate_metadata(self, scene_count=0, pixel_count=0):
        meta = Metadata(
            query_id=self.query_id,
            scene_count=scene_count,
            pixel_count=pixel_count,
            latitude_min=self.latitude_min,
            latitude_max=self.latitude_max,
            longitude_min=self.longitude_min,
            longitude_max=self.longitude_max)
        meta.save()
        return meta

    def generate_result(self):
        result = Result(
            query_id=self.query_id,
            result_path="",
            data_path="",
            latitude_min=self.latitude_min,
            latitude_max=self.latitude_max,
            longitude_min=self.longitude_min,
            longitude_max=self.longitude_max,
            total_scenes=0,
            scenes_processed=0,
            status="WAIT")
        result.save()
        return result


class Metadata(BaseMetadata):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted.
    """

    def acquisitions_dates_with_pixels_percentages(self):
        """
        Creates a zip file with a number of lists included as the content

        Returns:
            zip file: Zip file combining three different lists (acquisition_list_as_list(),
            clean_pixels_list_as_list(), clean_pixels_percentages_as_list())
        """
        return zip(self.acquisition_list_as_list(),
                   self.clean_pixels_list_as_list(), self.clean_pixels_percentages_as_list())


class Result(BaseResult):
    """
    Stores a single instance of a Result object that contains all the information for requests
    submitted.
    """

    # result path + other data. More to come.
    scene_ndvi_path = models.CharField(max_length=250, default="")
    baseline_ndvi_path = models.CharField(max_length=250, default="")
    ndvi_percentage_change_path = models.CharField(max_length=250, default="")
    result_mosaic_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")
    data_path = models.CharField(max_length=250, default="")
