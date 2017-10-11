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
from apps.dc_algorithm.models import (Query as BaseQuery, Metadata as BaseMetadata, Result as BaseResult, ResultType as
                                      BaseResultType, UserHistory as BaseUserHistory, AnimationType as
                                      BaseAnimationType, ToolInfo as BaseToolInfo)

from utils.data_cube_utilities.dc_mosaic import (create_mosaic, create_mean_mosaic)

import datetime
import numpy as np


class UserHistory(BaseUserHistory):
    """
    Extends the base user history adding additional fields
    See the dc_algorithm.UserHistory docstring for more information
    """
    pass


class ToolInfo(BaseToolInfo):
    """
    Extends the base ToolInfo adding additional fields
    See the dc_algorithm.ToolInfo docstring for more information
    """
    pass


class BaselineMethod(models.Model):
    """
    acts like result type, but for baseline selection.
    """

    id = models.CharField(unique=True, primary_key=True, max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Query(BaseQuery):
    """

    Extends base query, adds app specific elements. See the dc_algorithm.Query docstring for more information
    Defines the get_or_create_query_from_post as required, adds new fields, recreates the unique together
    field, and resets the abstract property. Functions are added to get human readable names for various properties,
    foreign keys should define __str__ for a human readable name.

    """

    baseline_method = models.ForeignKey(BaselineMethod)
    baseline_length = models.IntegerField(default=10)

    base_result_dir = '/datacube/ui_results/slip'

    class Meta(BaseQuery.Meta):
        unique_together = (
            ('satellite', 'area_id', 'time_start', 'time_end', 'latitude_max', 'latitude_min', 'longitude_max',
             'longitude_min', 'title', 'description', 'baseline_method', 'baseline_length'))
        abstract = True

    def get_fields_with_labels(self, labels, field_names):
        for idx, label in enumerate(labels):
            yield [label, getattr(self, field_names[idx])]

    def get_chunk_size(self):
        """Implements get_chunk_size as required by the base class

        See the base query class docstring for more information.

        """
        return {'time': None, 'geographic': 0.005}

    def get_iterative(self):
        """implements get_iterative as required by the base class

        See the base query class docstring for more information.

        """
        return False

    def get_reverse_time(self):
        """implements get_reverse_time as required by the base class

        See the base query class docstring for more information.

        """
        return True

    def get_processing_method(self):
        """implements get_processing_method as required by the base class

        See the base query class docstring for more information.

        """
        processing_methods = {'composite': create_mosaic, 'average': create_mean_mosaic}

        return processing_methods.get(self.baseline_method.id, create_mosaic)

    @classmethod
    def get_or_create_query_from_post(cls, form_data, pixel_drill=False):
        """Implements the get_or_create_query_from_post func required by base class

        See the get_or_create_query_from_post docstring for more information.
        Parses out the time start/end, creates the product, and formats the title/description

        Args:
            form_data: python dict containing either a single obj or a list formatted with post_data_to_dict

        Returns:
            Tuple containing the query model and a boolean value signifying if it was created or loaded.

        """
        query_data = form_data
        query_data['title'] = "SLIP Query" if 'title' not in form_data or form_data['title'] == '' else form_data[
            'title']
        query_data['description'] = "None" if 'description' not in form_data or form_data[
            'description'] == '' else form_data['description']

        valid_query_fields = [field.name for field in cls._meta.get_fields()]
        query_data = {key: query_data[key] for key in valid_query_fields if key in query_data}

        try:
            query = cls.objects.get(pixel_drill_task=pixel_drill, **query_data)
            return query, False
        except cls.DoesNotExist:
            query = cls(pixel_drill_task=pixel_drill, **query_data)
            query.save()
            return query, True


class Metadata(BaseMetadata):
    """
    Extends base metadata, adding additional fields and adding abstract=True.

    zipped_metadata_fields is required.

    See the dc_algorithm.Metadata docstring for more information
    """

    slip_pixels_per_acquisition = models.CharField(max_length=100000, default="")
    zipped_metadata_fields = [
        'acquisition_list', 'clean_pixels_per_acquisition', 'clean_pixel_percentages_per_acquisition',
        'slip_pixels_per_acquisition'
    ]

    class Meta(BaseMetadata.Meta):
        abstract = True

    def metadata_from_dataset(self, metadata, dataset, clear_mask, parameters, time):
        """implements metadata_from_dataset as required by the base class

        See the base metadata class docstring for more information.

        """
        clean_pixels = np.sum(clear_mask == True)
        slip_slice = dataset.slip.values
        if time not in metadata:
            metadata[time] = {}
            metadata[time]['clean_pixels'] = 0
            metadata[time]['slip_pixels'] = 0
        metadata[time]['clean_pixels'] += clean_pixels
        metadata[time]['slip_pixels'] += len(slip_slice[slip_slice > 0])
        return metadata

    def combine_metadata(self, old, new):
        """implements combine_metadata as required by the base class

        See the base metadata class docstring for more information.

        """
        for key in new:
            if key in old:
                old[key]['clean_pixels'] += new[key]['clean_pixels']
                old[key]['slip_pixels'] += new[key]['slip_pixels']
                continue
            old[key] = new[key]
        return old

    def final_metadata_from_dataset(self, dataset):
        """implements final_metadata_from_dataset as required by the base class

        See the base metadata class docstring for more information.

        """
        self.pixel_count = len(dataset.latitude) * len(dataset.longitude)
        self.clean_pixel_count = np.sum(dataset[list(dataset.data_vars)[0]].values != -9999)
        self.percentage_clean_pixels = (self.clean_pixel_count / self.pixel_count) * 100
        self.save()

    def metadata_from_dict(self, metadata_dict):
        """implements metadata_from_dict as required by the base class

        See the base metadata class docstring for more information.

        """
        dates = list(metadata_dict.keys())
        dates.sort(reverse=True)
        self.total_scenes = len(dates)
        self.scenes_processed = len(dates)
        self.acquisition_list = ",".join([date.strftime("%m/%d/%Y") for date in dates])
        self.slip_pixels_per_acquisition = ",".join([str(metadata_dict[date]['slip_pixels']) for date in dates])
        self.clean_pixels_per_acquisition = ",".join([str(metadata_dict[date]['clean_pixels']) for date in dates])
        self.clean_pixel_percentages_per_acquisition = ",".join(
            [str((metadata_dict[date]['clean_pixels'] * 100) / self.pixel_count) for date in dates])
        self.save()


class Result(BaseResult):
    """
    Extends base result, adding additional fields and adding abstract=True
    See the dc_algorithm.Result docstring for more information
    """

    result_mosaic_path = models.CharField(max_length=250, default="")
    plot_path = models.CharField(max_length=250, default="")
    data_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")

    class Meta(BaseResult.Meta):
        abstract = True


class SlipTask(Query, Metadata, Result):
    """
    Combines the Query, Metadata, and Result abstract models
    """
    pass
