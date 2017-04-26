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

from apps.dc_algorithm.models import Area, Compositor, Satellite
from apps.dc_algorithm.models import Query as BaseQuery, Metadata as BaseMetadata, Result as BaseResult, ResultType as BaseResultType

import datetime


class Query(BaseQuery):
    """
    Extends base query, adds app specific elements.
    """
    query_type = models.CharField(max_length=25, default="")
    animated_product = models.CharField(max_length=25, default="None")
    compositor = models.CharField(max_length=25, default="most_recent")

    class Meta(BaseQuery.Meta):
        unique_together = (('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min',
                            'longitude_max', 'longitude_min', 'query_type', 'animated_product', 'compositor'))
        abstract = True

    # functs.
    def get_type_name(self):
        """
        Gets the ResultType.result_type attribute associated with the given Query object.

        Returns:
            result_type (string): The result type of the query.
        """
        return ResultType.objects.filter(result_id=self.query_type, satellite_id=self.platform)[0].result_type

    def get_compositor_name(self):
        """
        Gets the ResultType.result_type attribute associated with the given Query object.

        Returns:
            result_type (string): The result type of the query.
        """
        return Compositor.objects.get(compositor_id=self.compositor).compositor_name

    @classmethod
    def _get_or_create_query_from_post(cls, form_data):
        query_data = form_data
        query_data['time_start'] = datetime.datetime.strptime(form_data['time_start'], '%m/%d/%Y')
        query_data['time_end'] = datetime.datetime.strptime(form_data['time_end'], '%m/%d/%Y')

        query_data['product'] = Satellite.objects.get(
            satellite_id=query_data['platform']).product_prefix + Area.objects.get(
                area_id=query_data['area_id']).area_id
        query_data['title'] = "Base Query" if 'title' not in form_data or form_data['title'] == '' else form_data[
            'title']
        query_data['description'] = "None" if 'description' not in form_data or form_data[
            'description'] == '' else form_data['description']

        valid_query_fields = [field.name for field in cls._meta.get_fields() if field in query_data]

        query_data = {key: query_data[key] for key in valid_query_fields}

        query = cls(**query_data)

        try:
            query.save()
            return query, True
        except ValidationError:
            query = cls.objects.get(**query_data)
            return query, False


class Metadata(BaseMetadata):
    """
    Extends base metadata.
    """
    satellite_list = models.CharField(max_length=100000, default="")

    class Meta(BaseMetadata.Meta):
        abstract = True

    def satellite_list_as_list(self):
        return self.satellite_list.rstrip(',').split(',')

    def metadata_as_zip4(self):
        """
        Creates a zip file with a number of lists included as the content

        Returns:
            zip file: Zip file combining three different lists (acquisition_list_as_list(),
            clean_pixels_list_as_list(), clean_pixels_percentages_as_list())
        """
        return zip(self.acquisition_list_as_list(),
                   self.clean_pixels_list_as_list(),
                   self.clean_pixels_percentages_as_list(), self.satellite_list_as_list())


class Result(BaseResult):
    """
    Extends base result, only adds app specific fields.
    """

    # result path + other data. More to come.
    result_filled_path = models.CharField(max_length=250, default="")
    animation_path = models.CharField(max_length=250, default="None")
    data_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")

    class Meta(BaseResult.Meta):
        abstract = True


class CustomMosaicTask(Query, Metadata, Result):
    pass


class ResultType(BaseResultType):
    """
    extends base result type, adding the app specific fields.
    """

    red = models.CharField(max_length=25)
    green = models.CharField(max_length=25)
    blue = models.CharField(max_length=25)
    fill = models.CharField(max_length=25, default="red")
