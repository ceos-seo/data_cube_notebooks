from django.conf import settings
from django.db import connections
from django.forms.models import model_to_dict
from django.db.models import Q

import celery
from celery.task import task
from celery import chain, group, chord
from celery.utils.log import get_task_logger
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datacube.index import index_connect
from datacube.executor import get_executor
from datacube.config import LocalConfig
from datacube.scripts import ingest

import os
import configparser
from glob import glob
import shutil

from apps.data_cube_manager.models import (Dataset, DatasetType, DatasetSource, DatasetLocation, IngestionRequest,
                                           IngestionDetails)
from apps.data_cube_manager.templates.bulk_downloader import base_downloader_script, static_script
from utils.data_access_api import DataAccessApi

logger = get_task_logger(__name__)


class IngestionBase(celery.Task):
    """Serves as a base class for ingestion tasks"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Onfailure call for celery tasks

        all tasks should have a kwarg 'ingestion_request_id' that can be used to 'get' the model
        from the app.

        """
        request_id = kwargs.get('ingestion_request_id')
        try:
            request = IngestionRequest.objects.get(pk=request_id)
            request.update_status(
                "ERROR",
                "There was an unhandled exception during ingestion. Did you change the src_varname of any measurement?")
        except IngestionRequest.DoesNotExist:
            pass


@periodic_task(
    name="data_cube_manager.get_data_cube_details",
    run_every=(30.0),
    #run_every=(crontab(hour=0, minute=0)),
    ignore_result=True)
def update_data_cube_details(ingested_only=True):
    dataset_types = DatasetType.objects.using('agdc').filter(
        Q(definition__has_keys=['managed']) & Q(definition__has_keys=['measurements']))

    dc = DataAccessApi(config='/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf')

    for dataset_type in dataset_types:
        ingestion_details, created = IngestionDetails.objects.get_or_create(
            datase_type_ref=dataset_type.id,
            product=dataset_type.name,
            platform=dataset_type.metadata['platform']['code'])
        ingestion_details.update_with_query_metadata(dc.get_datacube_metadata(dataset_type.name))


@task(name="data_cube_manager.run_ingestion")
def run_ingestion(ingestion_definition):
    """Kick off the standard system database ingestion process using a user defined configuration

    Args:
        ingestion_definition: dict representing a Data Cube ingestion def produced using the utils func.

    Returns:
        The primary key of the new dataset type.
    """
    conf_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    index = index_connect(local_config=LocalConfig.find([conf_path]))

    source_type, output_type = ingest.make_output_type(index, ingestion_definition)
    ingestion_work.delay(output_type, source_type, ingestion_definition)

    index.close()
    return output_type.id


@task(name="data_cube_manager.ingestion_work")
def ingestion_work(output_type, source_type, ingestion_definition):
    """Run the ingestion process for a user defined configuration

    Args:
        output_type, source_type: types produced by ingest.make_output_type
        ingestion_definition: dict representing a Data Cube ingestion def produced using the utils func.
    """
    conf_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    index = index_connect(local_config=LocalConfig.find([conf_path]))

    tasks = ingest.create_task_list(index, output_type, None, source_type, ingestion_definition)

    # this is a dry run
    # paths = [ingest.get_filename(ingestion_definition, task['tile_index'], task['tile'].sources) for task in tasks]
    # ingest.check_existing_files(paths)

    # this actually ingests stuff
    successful, failed = ingest.process_tasks(index, ingestion_definition, source_type, output_type, tasks, 3200,
                                              get_executor(None, None))

    index.close()
    return 0


@task(name="data_cube_manager.ingestion_on_demand", base=IngestionBase)
def ingestion_on_demand(ingestion_request_id=None):
    """Kick off the ingestion on demand/active subset process

    Creates a Celery canvas that handles the full ingestion process.

    Args:
        ingestion_request_id: pk of a models.IngestionRequest obj.
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    ingestion_request.update_status("WAIT", "Creating base Data Cube database...")

    ingestion_pipeline = (init_db.si(ingestion_request_id=ingestion_request_id) |
                          add_source_datasets.si(ingestion_request_id=ingestion_request_id) |
                          ingest_subset.si(ingestion_request_id=ingestion_request_id) |
                          prepare_output.si(ingestion_request_id=ingestion_request_id))()


@task(name="data_cube_manager.init_db", base=IngestionBase)
def init_db(ingestion_request_id=None):
    """Creates a new database and initializes it with the standard agdc schema

    Creates a new database named the user using a psql call and uses the agdc api
    to initalize the schema.

    """
    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    cmd = "createdb -U dc_user {}".format(ingestion_request.user)
    os.system(cmd)

    config = get_config(ingestion_request.user)
    index = index_connect(local_config=config, validate_connection=False)

    index.init_db(with_default_types=True, with_permissions=True)
    index.metadata_types.check_field_indexes(allow_table_lock=False, rebuild_indexes=False, rebuild_views=True)
    index.close()


@task(name="data_cube_manager.add_source_datasets", base=IngestionBase)
def add_source_datasets(ingestion_request_id=None):
    """Populate the newly created database with source datasets that match the criteria

    Searches for datasets using the search criteria found on the IngestionRequest model and populates
    the newly created database with the new data. The dataset type's id is reset to 0 to prevent collisions in
    the agdc script.

    A dataset type, datasets, dataset_locations, and dataset_sources are added to the new database.
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)
    ingestion_request.update_status("WAIT", "Populating database with source datasets...")

    config = get_config(ingestion_request.user)
    index = index_connect(local_config=config, validate_connection=False)

    dataset_type = DatasetType.objects.using('agdc').get(id=ingestion_request.dataset_type_ref)
    filtering_options = {
        key: getattr(ingestion_request, key)
        for key in [
            'dataset_type_ref', 'start_date', 'end_date', 'latitude_min', 'latitude_max', 'longitude_min',
            'longitude_max'
        ]
    }
    datasets = list(Dataset.filter_datasets(filtering_options))

    dataset_locations = DatasetLocation.objects.using('agdc').filter(dataset_ref__in=datasets)
    dataset_sources = DatasetSource.objects.using('agdc').filter(dataset_ref__in=datasets)

    create_db(ingestion_request.user)

    dataset_type.id = 0
    dataset_type.save(using=ingestion_request.user)

    for dataset in datasets:
        dataset.dataset_type_ref_id = 0

    Dataset.objects.using(ingestion_request.user).bulk_create(datasets)
    DatasetLocation.objects.using(ingestion_request.user).bulk_create(dataset_locations)
    DatasetSource.objects.using(ingestion_request.user).bulk_create(dataset_sources)

    close_db(ingestion_request.user)
    index.close()


@task(name="data_cube_manager.ingest_subset", base=IngestionBase)
def ingest_subset(ingestion_request_id=None):
    """Run the ingestion process on the new database

    Open a connection to the new database and run ingestion based on the
    ingestion configuration found on the IngestionRequest model.

    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    config = get_config(ingestion_request.user)
    index = index_connect(local_config=config, validate_connection=False)

    # Thisis done because of something that the agdc guys do in ingest: https://github.com/opendatacube/datacube-core/blob/develop/datacube/scripts/ingest.py#L168
    ingestion_request.ingestion_definition['filename'] = "ceos_data_cube_sample.yaml"

    try:
        source_type, output_type = ingest.make_output_type(index, ingestion_request.ingestion_definition)
        tasks = list(
            ingest.create_task_list(index, output_type, None, source_type, ingestion_request.ingestion_definition))

        ingestion_request.total_storage_units = len(tasks)
        ingestion_request.update_status("WAIT", "Starting the ingestion process...")

        successful, failed = ingest.process_tasks(index, ingestion_request.ingestion_definition, source_type,
                                                  output_type, tasks, 3200, get_executor(None, None))
    except:
        index.close()
        raise

    index.close()


@task(name="data_cube_manager.prepare_output", base=IngestionBase)
def prepare_output(ingestion_request_id=None):
    """Dump the database and perform cleanup functions

    Drops the database, create the bulk download script, and dumps the database.

    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)
    ingestion_request.update_status("WAIT", "Creating output products...")

    config = get_config(ingestion_request.user)
    index = index_connect(local_config=config, validate_connection=False)

    cmd = "pg_dump -U dc_user -n agdc {} > {}".format(ingestion_request.user,
                                                      ingestion_request.get_database_dump_path())
    os.system(cmd)
    index.close()
    cmd = "dropdb -U dc_user {}".format(ingestion_request.user)
    os.system(cmd)

    ingestion_request.download_script_path = ingestion_request.get_base_data_path() + "/bulk_downloader.py"

    with open(ingestion_request.download_script_path, "w+") as downloader:
        file_list = ",".join('"{}"'.format(path) for path in glob(ingestion_request.get_base_data_path() + '/*.nc'))
        download_script = base_downloader_script.format(
            file_list=file_list,
            database_dump_file=ingestion_request.get_database_dump_path(),
            base_host=settings.BASE_HOST,
            base_data_path=ingestion_request.get_base_data_path()) + static_script
        downloader.write(download_script)

    ingestion_request.update_status("OK", "Please follow the directions on the right side panel to download your cube.")


@task(name="data_cube_manager.delete_ingestion_request", base=IngestionBase)
def delete_ingestion_request(ingestion_request_id=None):
    """Delete an existing ingestion request before proceeding with a new one"""
    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)
    try:
        shutil.rmtree(ingestion_request.get_base_data_path())
    except:
        pass


def get_config(username):
    config = configparser.ConfigParser()
    config['datacube'] = {
        'db_password': 'dcuser1',
        'db_connection_timeout': '60',
        'db_username': 'dc_user',
        'db_database': username,
        'db_hostname': settings.MASTER_NODE
    }

    return LocalConfig(config)


def create_db(username):
    connections.databases[username] = {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'options': '-c search_path=agdc'
        },
        'NAME': username,
        'USER': 'dc_user',
        'PASSWORD': 'dcuser1',
        'HOST': settings.MASTER_NODE
    }


def close_db(username):
    connections[username].close()
    connections.databases.pop(username)
