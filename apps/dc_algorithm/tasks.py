from celery.task import task
from datetime import datetime, timedelta
import os
import shutil
from django.apps import apps

from .models import Application


@task(name="dc_algorithm.clear_cache")
def clear_cache():
    _apps = Application.objects.all()
    time_threshold = datetime.now() - timedelta(days=7)
    for app in _apps:
        camel_case = "".join(x.title() for x in app.pk.split('_'))
        task_model = apps.get_model(".".join([app.pk, camel_case + "Task"]))
        history_model = apps.get_model(".".join([app.pk, "UserHistory"]))
        tasks = task_model.objects.filter(execution_start__lt=time_threshold)
        for task in tasks:
            history_model.filter(task_id=task.pk).delete()
            shutil.rmtree(task.get_result_path())
            task.delete()
    print("Cache Cleared.")
