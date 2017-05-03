from django.conf import settings

from celery.task import task
from celery import chain, group, chord

from utils.data_access_api import DataAccessApi
from utils.dc_mosaic import (create_mosaic, create_median_mosaic, create_max_ndvi_mosaic, create_min_ndvi_mosaic)

from .models import CustomMosaicTask


class ParameterChunker:
    time_grouping = ['year', 'month', 'acquisitions']

    geographic = 0.5
    time = 10
    time_units = 'acquisition'

    def __init__(self, geographic, time, time_units):
        self.geographic = geographic


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
