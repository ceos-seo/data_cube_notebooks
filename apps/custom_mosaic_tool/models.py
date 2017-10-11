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
from utils.data_cube_utilities.dc_mosaic import (create_mosaic, create_median_mosaic, create_max_ndvi_mosaic,
                                                 create_min_ndvi_mosaic)

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


class ResultType(BaseResultType):
    """
    extends base result type, adding additional fields required by app.
    See the dc_algorithm.ResultType docstring for more information.
    """

    red = models.CharField(max_length=25)
    green = models.CharField(max_length=25)
    blue = models.CharField(max_length=25)
    fill = models.CharField(max_length=25, default="red")


class AnimationType(BaseAnimationType):
    """
    Extends the base animation type, adding additional fields as required by app.
    See the dc_algorithm.AnimationType docstring for more information.
    """

    pass


class Query(BaseQuery):
    """

    Extends base query, adds app specific elements. See the dc_algorithm.Query docstring for more information
    Defines the get_or_create_query_from_post as required, adds new fields, recreates the unique together
    field, and resets the abstract property. Functions are added to get human readable names for various properties,
    foreign keys should define __str__ for a human readable name.

    """
    query_type = models.ForeignKey(ResultType)
    animated_product = models.ForeignKey(AnimationType)
    compositor = models.ForeignKey(Compositor)

    base_result_dir = '/datacube/ui_results/custom_mosaic_tool'

    class Meta(BaseQuery.Meta):
        unique_together = (
            ('satellite', 'area_id', 'time_start', 'time_end', 'latitude_max', 'latitude_min', 'longitude_max',
             'longitude_min', 'title', 'description', 'query_type', 'animated_product', 'compositor'))
        abstract = True

    def get_fields_with_labels(self, labels, field_names):
        for idx, label in enumerate(labels):
            yield [label, getattr(self, field_names[idx])]

    def get_chunk_size(self):
        """Implements get_chunk_size as required by the base class

        See the base query class docstring for more information.

        """
        if not self.compositor.is_iterative():
            return {'time': None, 'geographic': 0.01}
        return {'time': 25, 'geographic': 0.5}

    def get_iterative(self):
        """implements get_iterative as required by the base class

        See the base query class docstring for more information.

        """
        return self.compositor.is_iterative()

    def get_reverse_time(self):
        """implements get_reverse_time as required by the base class

        See the base query class docstring for more information.

        """
        return self.compositor.id == "most_recent"

    def get_processing_method(self):
        """implements get_processing_method as required by the base class

        See the base query class docstring for more information.

        """
        processing_methods = {
            'most_recent': create_mosaic,
            'least_recent': create_mosaic,
            'max_ndvi': create_max_ndvi_mosaic,
            'min_ndvi': create_min_ndvi_mosaic,
            'median_pixel': create_median_mosaic
        }

        return processing_methods.get(self.compositor.id, create_mosaic)

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
        query_data['title'] = "Custom Mosaic Query" if 'title' not in form_data or form_data[
            'title'] == '' else form_data['title']
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
    satellite_list = models.CharField(max_length=100000, default="")
    zipped_metadata_fields = [
        'acquisition_list', 'clean_pixels_per_acquisition', 'clean_pixel_percentages_per_acquisition', 'satellite_list'
    ]

    class Meta(BaseMetadata.Meta):
        abstract = True

    def metadata_from_dataset(self, metadata, dataset, clear_mask, parameters):
        """implements metadata_from_dataset as required by the base class

        See the base metadata class docstring for more information.

        """
        for metadata_index, time in enumerate(dataset.time.values.astype('M8[ms]').tolist()):
            clean_pixels = np.sum(clear_mask[metadata_index, :, :] == True)
            if time not in metadata:
                metadata[time] = {}
                metadata[time]['clean_pixels'] = 0
                metadata[time]['satellite'] = parameters['platforms'][np.unique(
                    dataset.satellite.isel(time=metadata_index).values)[0]] if np.unique(
                        dataset.satellite.isel(time=metadata_index).values)[0] > -1 else "NODATA"
            metadata[time]['clean_pixels'] += clean_pixels
        return metadata

    def combine_metadata(self, old, new):
        """implements combine_metadata as required by the base class

        See the base metadata class docstring for more information.

        """
        for key in new:
            if key in old:
                old[key]['clean_pixels'] += new[key]['clean_pixels']
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
        self.satellite_list = ",".join([metadata_dict[date]['satellite'] for date in dates])
        self.clean_pixels_per_acquisition = ",".join([str(metadata_dict[date]['clean_pixels']) for date in dates])
        self.clean_pixel_percentages_per_acquisition = ",".join(
            [str((metadata_dict[date]['clean_pixels'] * 100) / self.pixel_count) for date in dates])
        self.save()


class Result(BaseResult):
    """
    Extends base result, adding additional fields and adding abstract=True
    See the dc_algorithm.Result docstring for more information
    """

    # result path + other data. More to come.
    result_filled_path = models.CharField(max_length=250, default="")
    plot_path = models.CharField(max_length=250, default="")
    animation_path = models.CharField(max_length=250, default="None")
    data_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")

    class Meta(BaseResult.Meta):
        abstract = True


class CustomMosaicToolTask(Query, Metadata, Result):
    """
    Combines the Query, Metadata, and Result abstract models
    """
    pass
