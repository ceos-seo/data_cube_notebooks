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

    baseline = models.CharField(max_length=25, default="average")
    baseline_length = models.IntegerField(default=5)

    # functs.
    def get_baseline_name(self):
        """
        Gets the ResultType.result_type attribute associated with the given Query object.

        Returns:
            result_type (string): The result type of the query.
        """
        return Baseline.objects.get(baseline_id=self.baseline).baseline_name

    def generate_query_id(self):
        """
        Creates a Query ID based on a number of different attributes including start_time, end_time
        latitude_min and max, longitude_min and max, measurements, platform, product, and query_type

        Returns:
            query_id (string): The ID of the query built up by object attributes.
        """
        query_id = self.time_start.strftime("%Y-%m-%d") + '-' + self.time_end.strftime("%Y-%m-%d") + '-' + str(self.latitude_max) + '-' + str(
            self.latitude_min) + '-' + str(self.longitude_max) + '-' + str(self.longitude_min) + '-' + self.baseline + '-' + str(
            self.baseline_length) + '-' + self.platform + '-' + self.product
        return query_id

    def generate_metadata(self, scene_count=0, pixel_count=0):
        meta = Metadata(query_id=self.query_id, scene_count=scene_count, pixel_count=pixel_count,
                        latitude_min=self.latitude_min, latitude_max=self.latitude_max, longitude_min=self.longitude_min, longitude_max=self.longitude_max)
        meta.save()
        return meta

    def generate_result(self):
        result = Result(query_id=self.query_id, result_path="", data_path="", latitude_min=self.latitude_min,
                        latitude_max=self.latitude_max, longitude_min=self.longitude_min, longitude_max=self.longitude_max, total_scenes=0, scenes_processed=0, status="WAIT")
        result.save()
        return result


class Metadata(BaseMetadata):
    """
    Stores a single instance of a Query object that contains all the information for requests
    submitted.
    """

    slip_pixels_per_acquisition = models.CharField(max_length=100000, default="")

    def slip_pixels_list_as_list(self):
        """
        Splits the list of clean pixels into a list.

        Returns:
            clean_pixels_per_acquisition (list): List representation of the acquisitions from the
            database.
        """
        return self.slip_pixels_per_acquisition.rstrip(',').split(',')

    def acquisitions_dates_with_pixels_percentages(self):
        """
        Creates a zip file with a number of lists included as the content

        Returns:
            zip file: Zip file combining three different lists (acquisition_list_as_list(),
            clean_pixels_list_as_list(), clean_pixels_percentages_as_list())
        """
        return zip(self.acquisition_list_as_list(), self.clean_pixels_list_as_list(), self.slip_pixels_list_as_list(), self.clean_pixels_percentages_as_list())

class Result(BaseResult):
    """
    Stores a single instance of a Result object that contains all the information for requests
    submitted.
    """

    # result path + other data. More to come.
    result_mosaic_path = models.CharField(max_length=250, default="")
    baseline_mosaic_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")
    data_path = models.CharField(max_length=250, default="")
