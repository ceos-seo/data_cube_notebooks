from django.conf import settings

from celery.task import task
from celery import chain, group, chord
from celery.utils.log import get_task_logger
from datacube.index import index_connect
from datacube.executor import get_executor
from datacube.config import LocalConfig
from datacube.scripts import ingest

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
    paths = [ingest.get_filename(ingestion_definition, task['tile_index'], task['tile'].sources) for task in tasks]
    ingest.check_existing_files(paths)

    # this actually ingests stuff
    #successful, failed = process_tasks(index, ingestion_definition, source_type, output_type, tasks, 3200,
    #                                   get_executor(None, 8))
    return 0
