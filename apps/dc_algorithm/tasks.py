import celery
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datetime import datetime, timedelta
import os
import shutil
from django.apps import apps

from .models import Application


class DCAlgorithmBase(celery.Task):
    """Serves as a base class for all DC algorithm celery tasks"""
    app_name = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Onfailure call for celery tasks

        all tasks should have a kwarg 'task_id' that can be used to 'get' the model
        from the app.

        """
        task_id = kwargs.get('task_id')
        camel_case = "".join(x.title() for x in self._get_app_name().split('_'))
        task_model = apps.get_model(".".join([self._get_app_name(), camel_case + "Task"]))
        history_model = apps.get_model(".".join([self._get_app_name(), "UserHistory"]))
        try:
            task = task_model.objects.get(pk=task_id)
            if task.complete:
                return
            task.complete = True
            task.update_status("ERROR", "There was an unhandled exception during the processing of your task.")
            history_model.objects.filter(task_id=task.pk).delete()
        except task_model.DoesNotExist:
            pass

    def _get_app_name(self):
        """Get the app name of the task - raise an error if None"""
        if self.app_name is None:
            raise NotImplementedError(
                "You must specify an app_name in classes that inherit DCAlgorithmBase. See the DCAlgorithmBase docstring for more details."
            )
        return self.app_name


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
