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

    def update_status(self, status, message):
        self.status = status
        self.message = message
        self.save()

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


class Metadata(models.Model):
    """Base Metadata model meant to be inherited by a TaskClass

    Serves as the base of all algorithm metadata, containing basic fields such as scene
    count, pixel count, clean pixel statistics. Comma seperated fields are also used here
    and zipped/fetched using the get_field_as_list function.

    Constraints:
        All fields excluding primary key are unique together.
        all fields are optional and will be replaced with valid values when they
            are generated by the task.

    Usage:
        In each app, subclass Metadata and add all fields (if desired).
        Subclass Meta as well to ensure the class remains abstract e.g.
            class AppMetadata(Metadata):
                sample_field = models.CharField(max_length=100)

                class Meta(Metadata.Meta):
                    pass

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

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

    zipped_metadata_fields = None

    class Meta:
        abstract = True

    def _get_field_as_list(self, field_name):
        """Convert comma seperated strings into lists

        Certain metadata fields are stored as comma seperated lists of properties.
        Use this function to get the string, split on comma, and return the result.

        Args:
            field_name: field name as a string that should be converted

        Returns:
            List of attributes
        """
        return getattr(self, field_name).rstrip(',').split(',')

    def get_zipped_fields_as_list(self):
        """Creates a zipped iterable comprised of all the fields in self.zipped_metadata_fields

        Using _get_field_as_list converts the comma seperated fields in fields
        and zips them to iterate. Used to display grouped metadata, generally by
        acquisition date.

        Args:
            fields: iterable of comma seperated fields that should be grouped.

        Returns:
            zipped iterable containing grouped fields generated using _get_field_as_list
        """
        if self.zipped_metadata_fields is None:
            raise NotImplementedError("You must define zipped_metadata_fields in all classes that extend Metadata.")
        fields_as_lists = [self._get_field_as_list(field) for field in self.zipped_metadata_fields]
        return zip(*fields_as_lists)


class Result(models.Model):
    """Base Result model meant to be inherited by a TaskClass

    Serves as the base of all algorithm resluts, containing a status, number of scenes
    processed and total scenes (to generate progress bar), and a result path.
    The result path is required and is the path to the result that should be the
    *Default* result shown on the UI map. Other results can be added in subclasses.

    Constraints:
        result_path is required and must lead to an image that serves as the default result
            to be displayed to the user.

    Usage:
        In each app, subclass Result and add all fields (if desired).
        Subclass Meta as well to ensure the class remains abstract e.g.
            class AppResult(Result):
                sample_field = models.CharField(max_length=100)

                class Meta(Result.Meta):
                    pass

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    #either OK or ERROR or WAIT
    status = models.CharField(max_length=100, default="")
    #used to pass messages to the user.
    message = models.CharField(max_length=100, default="")

    scenes_processed = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)
    #default display result.
    result_path = models.CharField(max_length=250, default="")

    class Meta:
        abstract = True

    def get_progress(self):
        """Quantify the progress of a result's processing in terms of its own attributes

        Meant to return a representation of progress based on attributes set in a task.
        Should be overwritten in the task if scenes processed and total scenes aren't
        a useful representation

        Returns:
            An integer between 0 and 100

        """
        total_scenes = self.total_scenes if self.total_scenes > 0 else 1
        percent_complete = self.scenes_processed / total_scenes
        rounded_int = round(percent_complete * 100)
        clamped_int = max(0, min(rounded_int, 100))
        return


class GenericTask(Query, Metadata, Result):
    """Serves as the model for an algorithm task containing a Query, Metadata, and Result

    The generic task should be implemented by each application. Each app should subclass
    Query, Result, and Metadata, adding all desired fields according to docstrings. The
    app should then include a AppTask implementation that ties them all together:
        CustomMosaicTask(CustomMosaicQuery, CustomMosaicMetadata, CustomMosaicResult):
            pass

    This Generic task should not be subclassed and should be used only as a model for how
    things should be tied together at the app level.

    Constraints:
        Should subclass Query, Metadata, and Result (or a subclass of each)
        Should be used for all processing and be passed using a uuid pk
        Attributes should NOT be added to this class - add them to the inherited classes

    """

    pass

    class Meta:
        abstract = True


class ResultType(models.Model):
    """Stores a result type for an app that relates to options in the celery tasks

    Contains a satellite id, result id, and result type for differentiating between different
    result types. the result type should be displayed on the UI, passing the id as form data.
    The id should be handled directly in the celery task execution. This should be inherited at the
    app level without inheriting meta - the resulting class should not be abstract.

    Constraints:
        None yet.

    """
    result_id = models.CharField(max_length=25)
    datacube_platform = models.CharField(max_length=25)
    name = models.CharField(max_length=25)

    class Meta:
        unique_together = (('result_id', 'datacube_platform'))
        abstract = True

    def __str__(self):
        return self.name


class UserHistory(models.Model):
    """Contains the task history for a given user.

    This shoud act as a linking table between a user and their tasks.
    When a new task is submitted, a row should be created linking the user
    to the task by id.

    Constraints:
        user_id should map to a user's id.
        task_id should map to the pk of a task

    """

    user_id = models.IntegerField()
    task_id = models.UUIDField()

    class Meta:
        abstract = True
