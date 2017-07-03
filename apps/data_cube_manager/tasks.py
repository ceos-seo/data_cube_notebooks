from django.conf import settings
from django.db import connections
from django.forms.models import model_to_dict

from celery.task import task
from celery import chain, group, chord
from celery.utils.log import get_task_logger
from datacube.index import index_connect
from datacube.executor import get_executor
from datacube.config import LocalConfig
from datacube.scripts import ingest

import os
import configparser

from apps.data_cube_manager.models import Dataset, DatasetType, DatasetSource, DatasetLocation, IngestionRequest

logger = get_task_logger(__name__)


@task(name="data_cube_manager.run_ingestion")
def run_ingestion(ingestion_definition):
    conf_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    index = index_connect(local_config=LocalConfig.find([conf_path]))

    source_type, output_type = ingest.make_output_type(index, ingestion_definition)
    ingestion_work.delay(index, output_type, source_type, ingestion_definition)

    return output_type.id


@task(name="data_cube_manager.ingestion_work")
def ingestion_work(index, output_type, source_type, ingestion_definition):
    tasks = ingest.create_task_list(index, output_type, None, source_type, ingestion_definition)

    # this is a dry run
    # paths = [ingest.get_filename(ingestion_definition, task['tile_index'], task['tile'].sources) for task in tasks]
    # ingest.check_existing_files(paths)

    # this actually ingests stuff
    successful, failed = ingest.process_tasks(index, ingestion_definition, source_type, output_type, tasks, 3200,
                                              get_executor(None, None))
    return 0


@task(name="data_cube_manager.ingestion_on_demand")
def ingestion_on_demand(ingestion_request_id, search_fields=None):
    """
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    cmd = "createdb -U dc_user {}".format(ingestion_request.user)
    os.system(cmd)

    config = configparser.ConfigParser()
    config['datacube'] = {
        'db_password': 'dcuser1',
        'db_connection_timeout': '60',
        'db_username': 'dc_user',
        'db_database': ingestion_request.user,
        'db_hostname': settings.MASTER_NODE
    }

    config = LocalConfig(config)
    index = index_connect(local_config=config, validate_connection=False)
    """conf_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    index = index_connect(local_config=LocalConfig.find([conf_path]))"""

    ingestion_request.update_status("WAIT", "Creating base Data Cube database...")

    ingestion_pipeline = (
        init_db.si(index=index) |
        add_source_datasets.si(ingestion_request_id=ingestion_request_id, search_fields=search_fields, index=index) |
        ingest_subset.si(index=index, ingestion_request_id=ingestion_request_id) |
        prepare_output.si(index=index, ingestion_request_id=ingestion_request_id))()


@task(name="data_cube_manager.init_db")
def init_db(index=None):
    """
    """

    index.init_db(with_default_types=True, with_permissions=True)
    index.metadata_types.check_field_indexes(allow_table_lock=False, rebuild_indexes=False, rebuild_views=True)


@task(name="data_cube_manager.add_source_datasets")
def add_source_datasets(ingestion_request_id=None, search_fields=None, index=None):
    """
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    ingestion_request.update_status("WAIT", "Populating database with source datasets...")

    dataset_type = DatasetType.objects.using('agdc').get(id=ingestion_request.source_type)
    datasets = list(Dataset.filter_datasets(search_fields))

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


@task(name="data_cube_manager.ingest_subset")
def ingest_subset(index=None, ingestion_request_id=None):
    """
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)

    # Thisis done because of something that the agdc guys do in ingest: https://github.com/opendatacube/datacube-core/blob/develop/datacube/scripts/ingest.py#L168
    ingestion_request.ingestion_definition['filename'] = "ceos_data_cube_sample.yaml"

    source_type, output_type = ingest.make_output_type(index, ingestion_request.ingestion_definition)
    tasks = list(ingest.create_task_list(index, output_type, None, source_type, ingestion_request.ingestion_definition))

    ingestion_request.total_storage_units = len(tasks)
    ingestion_request.update_status("WAIT", "Starting the ingestion process...")

    successful, failed = ingest.process_tasks(index, ingestion_request.ingestion_definition, source_type, output_type,
                                              tasks, 3200, get_executor(None, None))


@task(name="data_cube_manager.prepare_output")
def prepare_output(index=None, ingestion_request_id=None):
    """
    """

    ingestion_request = IngestionRequest.objects.get(pk=ingestion_request_id)
    ingestion_request.update_status("WAIT", "Creating output products...")

    cmd = "pg_dump -U dc_user -n agdc {} > {}/datacube_dump".format(ingestion_request.user,
                                                                    ingestion_request.ingestion_definition['location'])
    os.system(cmd)

    index.close()

    cmd = "dropdb -U dc_user {}".format(ingestion_request.user)
    os.system(cmd)


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
