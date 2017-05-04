from django.conf import settings

from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import (create_mosaic, create_median_mosaic, create_max_ndvi_mosaic, create_min_ndvi_mosaic)

from .models import CustomMosaicTask

import math
from datetime import datetime
from itertools import groupby


class ParameterChunker:
    time_grouping = {'year': _groupby_year, 'month': _groupby_month, 'acquisition': _chunk_iterable}

    geographic_chunk_size = 0.5
    time_chunk_size = 10
    time_chunk_units = 'acquisition'

    def __init__(self, **kwargs):
        """Initialize a new parameter chunking object

        Uses only kwargs - all args are optional and will default to a 0.5 degree, 10 acquisition chunk size

        Args:
            geographic_chunk_size: Area size of each geographic chunk. e.g. 0.5, 1, 0.01 etc.
            time_chunk_size: time slice length - e.g. 10, 1, etc.
            time_chunk_units: year, month, acquisition
                acquisition results in groups of n acquisitions being loaded
                year results in groups of n years being loaded
                month results in groups of n months being loaded
        """
        self.geographic_chunk_size = kwargs.get('geographic_chunk_size', self.geographic_chunk_size)
        self.time_chunk_size = kwargs.get('time_chunk_size', self.time_chunk_size)
        self.time_chunk_units = kwargs.get('time_chunk_units', self.time_chunk_units)

        assert self.time_chunk_units in self.time_grouping

    def create_geographic_chunks(self, latitude, longitude):
        """Chunk a parameter set defined by latitude, longitude, and a list of acquisitions.

        Process the lat/lon/time parameters defined for loading Data Cube Data - these should be
        produced by dc.list_acquisition_dates

        Args:
            latitude: Latitude range to split
            longitude: Longitude range to split

        Returns:
            A zip formatted list of tuples containing (longitude, latitude) for each of the chunks

        """

        square_area = (latitude[1] - latitude[0]) * (longitude[1] - longitude[0])
        geographic_chunks = math.ceil(square_area / self.geographic_chunk_size)

        #we're splitting accross latitudes and not longitudes
        #this can be a fp value, no issue there.
        latitude_chunk_size = (latitude[1] - latitude[0]) / geographic_chunks
        latitude_ranges = [(latitude[0] + latitude_chunk_size * chunk_number,
                            latitude[0] + latitude_chunk_size * (chunk_number + 1))
                           for chunk_number in range(geographic_chunks)]
        longitude_ranges = [longitude for __ in latitude_ranges]

        return zip(longitude_ranges, latitude_ranges)

    def create_time_chunks(self, datetime_list, **kwargs):
        """Create an iterable containing groups of acquisition dates using class attributes

        Seperate a list of datetimes into chunks by acquisition, year, month, etc.
        Uses self.time_chunk_size and units - Gets the correct chunking funct based on self.time_chunk_units
        and calls it with a sorted list and

        example: months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], _reversed=False

        Args:
            datetime_list: List or iterable of datetimes to chunk
            kwargs:
                months (optional): List of months that should be used - defaults to all of them.
                _reversed (optional): boolean signifying that the acquisitions should be sorted least recent -> most recent (default)
                    or most recent -> least recent

        Returns:
            iterable of time chunks
        """

        datetimes_sorted = sorted(datetime_list, reverse=_reversed)

        assert len(datetimes_sorted) >= self.time_chunk_size

        chunking_func = self.time_grouping.get(self.time_chunk_units, _chunk_iterable)

        return chunking_func(datetimes_sorted, self.time_chunk_size, **kwargs)

    @staticmethod
    def _chunks(l, n):
        """"""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @staticmethod
    def _chunk_iterable(_iterable, chunk_size, **kwargs):
        """
        """
        chunks = list(chunks(_iterable, chunk_size))
        return chunks

    @staticmethod
    def _groupby_year(_iterable, chunk_size, **kwargs):
        """
        """
        return list(groupby(_iterable, lambda x: x.year))

    @staticmethod
    def _groupby_month(_iterable, chunk_size, **kwargs):
        """
        """
        month_filtered = filter(lambda x: x.month in kwargs.get('months', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
                                _iterable)
        return list(groupby(_iterable, lambda x: x.month))

    def _generate_baseline(month_filtered, window_length, **kwargs):
        """
        """


class Algorithm:
    """Base class for a Data Cube algorithm"""

    task_id = None
    config_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']

    def __init__(self, _id):
        self.task_id = _id

    def run(self):
        """
        """
        chain(parse_parameters_from_task.s(self), validate_parameters.s(self))()
        return True


@task(name="custom_mosaic_tool.parse_parameters_from_task")
def parse_parameters_from_task(algorithm):
    """
    """
    task = CustomMosaicTask.objects.get(pk=algorithm.task_id)

    parameters = {
        'product': task.product,
        'platform': task.platform,
        'time': (task.time_start, task.time_end),
        'longitude': (task.longitude_min, task.longitude_max),
        'latitude': (task.latitude_min, task.latitude_max)
    }

    # Get other parameters here - compositor, result type, everything else.
    algorithm.chunk_settings = ChunkingSettings()

    return parameters


@task(name="custom_mosaic_tool.validate_parameters")
def validate_parameters(parameters, algorithm):
    """
    """

    dc = DataAccessApi(config=algorithm.config_path)
    task = CustomMosaicTask.objects.get(pk=algorithm.task_id)

    #validate for any number of criteria here - num acquisitions, etc.
    acquisitions = dc.list_acquisition_dates(**parameters)
    if len(acquisitions) < 1:
        task.update_status("ERROR", "There are no acquistions for this parameter set.")
        return None

    dc.close()
    return parameters


@task(name="custom_mosaic_tool.perform_task_chunking")
def perform_task_chunking(parameter_set):
    """
    """
    pass


@task(name="custom_mosaic_tool.recombine_chunks_and_update_task")
def recombine_chunks_and_update_task(chunks):
    """
    """
    pass


"""
Processing pipeline definitions
"""


@task(name="custom_mosaic_tool.load_and_mask_data")
def load_and_mask_data(**kwargs):
    """
    """
    pass


@task(name="custom_mosaic_tool.mosaic_data")
def create_mosaic(dataset):
    """
    """
    pass
