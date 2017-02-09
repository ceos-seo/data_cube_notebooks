from celery.decorators import task
from celery.signals import worker_process_init, worker_process_shutdown

import xarray as xr
import datetime
import os

from utils.data_access_api import DataAccessApi

# Datacube instance to be initialized.
# A seperate DC instance is created for each worker.
dc = None

@task(name="generate_chunk")
def generate_chunk(time_num, chunk_num, processing_options=None, query=None, measurements=None, acquisition_list=None, lat_range=None, lon_range=None):

    #if the path has been removed, the task is cancelled and this is only running due to the prefetch.
    if not os.path.exists(processing_options['base_path'] + query.query_id):
        return None

    # signifies progress through the acquisition list.
    time_index = 0

    # holds the actual data product. all data vars are stacked here.
    data = None
    # holds all metadata. Generally passed into functions and is updated
    # rather than recreated.
    metadata = {}

    while time_index < len(acquisition_list):
        start = acquisition_list[time_index] + datetime.timedelta(
            seconds=1) if processing_options['reverse_time'] else acquisition_list[time_index]
        if processing_options['time_slices_per_iteration'] is not None and (time_index + processing_options['time_slices_per_iteration'] - 1) < len(acquisition_list):
            end = acquisition_list[
                time_index + processing_options['time_slices_per_iteration'] - 1]
        else:
            end = acquisition_list[-1] if processing_options[
                'reverse_time'] else acquisition_list[-1] + datetime.timedelta(seconds=1)
        time_range = (end, start) if processing_options[
            'reverse_time'] else (start, end)

        raw_data = None

        if query.platform == "LANDSAT_ALL":
            datasets_in = []
            for index in range(len(products)):
                dataset = dc.get_dataset_by_extent(products[index] + query.area_id, product_type=None, platform=platforms[
                                                   index], time=time_range, longitude=lon_range, latitude=lat_range, measurements=measurements)
                if 'time' in dataset:
                    datasets_in.append(dataset.copy(deep=True))
                dataset = None
            if len(datasets_in) > 0:
                raw_data = xr.concat(datasets_in, 'time')
        else:
            raw_data = dc.get_dataset_by_extent(query.product, product_type=None, platform=query.platform,
                                                time=time_range, longitude=lon_range, latitude=lat_range, measurements=measurements)

        # if cf_mask isn't present, there isn't any data so skip this
        # iteration.
        if raw_data is None or "cf_mask" not in raw_data:
            time_index = time_index + (processing_options['time_slices_per_iteration'] if processing_options[
                                       'time_slices_per_iteration'] else len(acquisition_list))
            continue

        animation_data = {'type': query.animated_product,
                          'path': processing_options['base_path'] + query.query_id + '/' + str(time_num) + '/',
                          'chunk_num': chunk_num,
                          'time_offset': time_index} if hasattr(query, 'animated_product') and query.animated_product != "None" else None

        # process the task and generate the metadata.
        data, metadata = processing_options['processing_method'](raw_data,
                                                                 intermediate_product=data,
                                                                 reverse_time=processing_options[
                                                                     'reverse_time'],
                                                                 animation_data=animation_data,
                                                                 metadata=metadata)

        time_index = time_index + (processing_options['time_slices_per_iteration'] if processing_options[
                                   'time_slices_per_iteration'] else len(acquisition_list))

    # merge all the data generated in this process and save it out to disk.
    chunk_data = xr.merge(data) if isinstance(data, list) else data
    data_netcdf_path = processing_options['base_path'] + query.query_id + "/chunk_" + \
        str(time_num) + "_" + str(chunk_num) + ".nc"
    # cf mask should be in every dataset. if it isn't then error.
    if chunk_data is None or "cf_mask" not in chunk_data or not os.path.exists(processing_options['base_path'] + query.query_id):
        return None
    chunk_data.to_netcdf(data_netcdf_path)
    return [data_netcdf_path, metadata]


# Init/shutdown functions for handling dc instances.
# this is done to prevent synchronization/conflicts between workers when
# accessing DC resources.
@worker_process_init.connect
def init_worker(**kwargs):
    """
    Creates an instance of the DataAccessApi worker.
    """

    print("Creating DC instance for worker.")
    global dc
    dc = DataAccessApi()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """
    Deletes the instance of the DataAccessApi worker.
    """

    print('Closing DC instance for worker.')
    global dc
    dc = None
