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


class Query(models.Model):
    """Base Query model meant to be inherited by a TaskClass

    Serves as the base of all algorithm query, containing some basic metadata
    such as title, description, and self timing functionality.

    Additionally, basic time, latitude, and longitude ranges are provided
    along with platform/product used for querying the Data Cube.

    Constraints:
        All fields excluding primary key are unique together.
        No fields are optional - defaults are provided only in specific fields

    Usage:
        In each app, subclass Query and add all fields (if desired).
        Subclass Meta and add the newly added fields (if any) to the list of
        unique_together fields in the meta class. e.g.
            class AppQuery(Query):
                sample_field = models.CharField(max_length=100)

                class Meta(Query.Meta):
                    unique_together = (('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min',
                                        'longitude_max', 'longitude_min', 'sample_field'))


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)

    execution_start = models.DateTimeField('execution_start', default=datetime.datetime.now)
    execution_end = models.DateTimeField('execution_end', default=datetime.datetime.now)

    area_id = models.CharField(max_length=100)

    platform = models.CharField(max_length=25)
    product = models.CharField(max_length=50)

    time_start = models.DateField('time_start')
    time_end = models.DateField('time_end')
    latitude_min = models.FloatField()
    latitude_max = models.FloatField()
    longitude_min = models.FloatField()
    longitude_max = models.FloatField()

    #false by default, only change is false-> true
    complete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        unique_together = (('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min',
                            'longitude_max', 'longitude_min', 'title', 'description'))

    @classmethod
    def get_queryset_from_history(cls, user_history, **kwargs):
        """Get a QuerySet of Query objects using the a user history queryset

        User history is defined in this class and must contain task_id and should be filtered already.
        The list of task ids are generated and used in a filter function on Query. Kwargs are passed directly
        in to the query filter function as kwargs.

        Args:
            user_history: Pre filtered UserHistory queryset - must contain attr task_id
            **kwargs: Any valid queryset key word arguments - common uses include complete=False, etc.

        Returns:
            Queryset of queries that fit the criteria and belong to the user.

        """
        queryset_pks = [user_history_entry.task_id for user_history_entry in user_history]
        return cls.objects.filter(pk__in=queryset_pks, **kwargs)

    @classmethod
    def get_or_create_query_from_post(cls, form_data):
        """Get or create a query obj from post form data

        Using a python dict formatted with post_data_to_dict, form a set of query parameters.
        Any formatting of parameters should be done here - including strings to datetime.datetime,
        list to strings, etc. The dict is then filtered for 'valid fields' by comparing it to
        a list of fields on this model. The query is saved in a try catch - if there is a validation error
        then the query exists and should be grabbed with 'get'.

        Args:
            form_data: python dict containing either a single obj or a list formatted with post_data_to_dict

        Returns:
            Tuple containing the query model and a boolean value signifying if it was created or loaded.

        """
        """
        def get_or_create_query_from_post(cls, form_data):
            query_data = form_data

            query_data['product'] = Satellite.objects.get(
                datacube_platform=query_data['platform']).product_prefix + Area.objects.get(
                    id=query_data['id']).id
            query_data['title'] = "Base Query" if 'title' not in form_data or form_data['title'] == '' else form_data[
                'title']
            query_data['description'] = "None" if 'description' not in form_data or form_data[
                'description'] == '' else form_data['description']

            valid_query_fields = [field.name for field in cls._meta.get_fields()]
            query_data = {key: query_data[key] for key in valid_query_fields if key in query_data}
            query = cls(**query_data)

            try:
                query = cls.objects.get(**query_data)
                return query, False
            except cls.DoesNotExist:
                query = cls(**query_data)
                query.save()
                return query, True
        """
        raise NotImplementedError(
            "You must define the classmethod 'get_or_create_query_from_post' in the inheriting class.")
