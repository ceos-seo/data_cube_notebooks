from django.conf import settings

from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import (create_mosaic, create_median_mosaic, create_max_ndvi_mosaic, create_min_ndvi_mosaic)

from .models import CustomMosaicTask

import math
from datetime import datetime
class ParameterChunker:
    time_grouping = {'year':_groupby_year, 'month': _groupby_month, 'acquisition':_chunk_acquisitions}
    geographic_grouping = {'degree':_chunk_degrees, 'pixel':_chunk_pixels}

    geographic_chunk_size = 0.5
    geographic_chunk_units = 'degree'
    time_chunk_size = 10
    time_chunk_units = 'acquisition'

    def __init__(self, **kwargs):
        """Initialize a new parameter chunking object

        Uses only kwargs - all args are optional and will default to a 0.5 degree, 10 acquisition chunk size

        Args:
            geographic_chunk_size: Area size of each geographic chunk. e.g. 0.5, 1, 0.01 etc.
            geographic_chunk_units: degree or pixels. Pixels will allow the user to specify a number of pixels to be used rather than area
            time_chunk_size: time slice length - e.g. 10, 1, etc.
            time_chunk_units: year, month, acquisition
                acquisition results in groups of n acquisitions being loaded
                year results in groups of n years being loaded
                month results in groups of n months being loaded
        """
        self.geographic_chunk_size = kwargs.get('geographic_chunk_size', self.geographic_chunk_size)
        self.geographic_chunk_units = kwargs.get('geographic_chunk_units', self.geographic_chunk_units)
        self.time_chunk_size = kwargs.get('time_chunk_size', self.time_chunk_size)
        self.time_chunk_units = kwargs.get('time_chunk_units', self.time_chunk_units)

        assert self.geographic_chunk_units in self.geographic_grouping
        assert self.time_chunk_units in self.time_grouping

    def _chunk_degrees(self, degree_range):
        """
        """


    def _chunk_pixels(self):
        """
        """

    def _chunk_acquisitions(self):
        """
        """

    def _groupby_year(self):
        """
        """

    def _groupby_month(self):
        """
        """

    def chunk_parameter_set(**kwargs):
        """Chunk a parameter set defined by latitude, longitude, and a list of acquisitions.

        Process the lat/lon/time parameters defined for loading Data Cube Data - these should be
        produced by dc.list_acquisition_dates

        Args:
            acquisitions: list of datetime instances to chunk into the desired format
            latitude: Latitude range to split
            longitude: Longitude range to split

        Returns:
            A zip formatted list of tuples containing (latitude, longitude, acquisition_list)
                for each of the chunks.

        """

        latitude = kwargs.get('latitude', None)
        longitude = kwargs.get('longitude', None)
        # latitude and longitude are required.
        assert 'latitude' is not None
        assert 'longitude' is not None
        assert self.geographic_chunk_units == "degree", "Parameter chunking works only on degrees. For a pixel stream, see create_pixel_stream."

        square_area = (latitude[1] - latitude[0]) * (longitude[1] - longitude[0])
        geographic_chunks = math.ceil(square_area / geo_chunk_size)
        if geographic_chunks == 1:
            #only one chunk.
            pass

        #we're splitting accross latitudes and not longitudes
        #this can be a fp value, no issue there.
        latitude_chunk_size = (latitude[1] - latitude[0]) / geographic_chunks
        latitude_ranges = [(latitude[0] + latitude_chunk_size*chunk_number, latitude[0] + latitude_chunk_size*(chunk_number + 1)) for chunk_number in range(geographic_chunks)]
        


        square_area =






    def create_pixel_stream(self):
        """
        """

    def combine_pixel_stream(self):
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
