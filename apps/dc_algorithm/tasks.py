from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datetime import datetime, timedelta
import os
import shutil
from django.apps import apps

from .models import Application


@periodic_task(
    name="dc_algorithm.clear_cache",
    #run_every=(30.0),
    run_every=(crontab(hour=0, minute=0)),
    ignore_result=True)
def clear_cache():
    _apps = Application.objects.all()
    time_threshold = datetime.now() - timedelta(days=2)
    for app in _apps:
        camel_case = "".join(x.title() for x in app.pk.split('_'))
        task_model = apps.get_model(".".join([app.pk, camel_case + "Task"]))
        history_model = apps.get_model(".".join([app.pk, "UserHistory"]))
        tasks = task_model.objects.filter(execution_start__lt=time_threshold)
        for task in tasks:
            history_model.objects.filter(task_id=task.pk).delete()
            shutil.rmtree(task.get_result_path())
            task.delete()
    print("Cache Cleared.")
