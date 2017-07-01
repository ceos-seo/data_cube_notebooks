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

from apps.data_cube_manager.models import Dataset, DatasetType, DatasetSource, DatasetLocation

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
def ingestion_on_demand(search_fields=None, user=None, ingestion_def=None):
    """
    """

    cmd = "createdb -U dc_user {}".format(user)
    os.system(cmd)

    config = configparser.ConfigParser()
    config['datacube'] = {
        'db_password': 'dcuser1',
        'db_connection_timeout': '60',
        'db_username': 'dc_user',
        'db_database': user,
        'db_hostname': settings.MASTER_NODE
    }

    config = LocalConfig(config)
    index = index_connect(local_config=config, validate_connection=False)
    """conf_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    index = index_connect(local_config=LocalConfig.find([conf_path]))"""

    ingestion_pipeline = (
        init_db.si(index=index) |
        add_source_datasets.si(user=user, ingestion_def=ingestion_def, search_fields=search_fields, index=index) |
        ingest_subset.si(index=index, user=user, ingestion_def=ingestion_def) |
        prepare_output.si(index=index, user=user, ingestion_def=ingestion_def))()


@task(name="data_cube_manager.init_db")
def init_db(index=None):
    """
    """

    index.init_db(with_default_types=True, with_permissions=True)
    index.metadata_types.check_field_indexes(allow_table_lock=False, rebuild_indexes=False, rebuild_views=True)


@task(name="data_cube_manager.add_source_datasets")
def add_source_datasets(user=None, ingestion_def=None, search_fields=None, index=None):
    """
    """

    dataset_type = DatasetType.objects.using('agdc').get(name=ingestion_def['source_type'])
    datasets = list(Dataset.filter_datasets(search_fields))

    dataset_locations = DatasetLocation.objects.using('agdc').filter(dataset_ref__in=datasets)
    dataset_sources = DatasetSource.objects.using('agdc').filter(dataset_ref__in=datasets)

    connections.databases[user] = {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'options': '-c search_path=agdc'
        },
        'NAME': user,
        'USER': 'dc_user',
        'PASSWORD': 'dcuser1',
        'HOST': settings.MASTER_NODE
    }

    dataset_type.id = 0
    dataset_type.save(using=user)

    for dataset in datasets:
        dataset.dataset_type_ref_id = 0

    Dataset.objects.using(user).bulk_create(datasets)
    DatasetLocation.objects.using(user).bulk_create(dataset_locations)
    DatasetSource.objects.using(user).bulk_create(dataset_sources)

    connections.databases.pop(user)


@task(name="data_cube_manager.ingest_subset")
def ingest_subset(index=None, user=None, ingestion_def=None):
    """
    """

    source_type, output_type = ingest.make_output_type(index, ingestion_def)
    tasks = ingest.create_task_list(index, output_type, None, source_type, ingestion_def)
    successful, failed = ingest.process_tasks(index, ingestion_def, source_type, output_type, tasks, 3200,
                                              get_executor(None, None))


@task(name="data_cube_manager.prepare_output")
def prepare_output(index=None, user=None, ingestion_def=None):
    """
    """
    pass
