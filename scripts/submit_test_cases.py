from django.apps import apps

# This is pretty horrible.
from apps import *
from apps.coastal_change import tasks
from apps.custom_mosaic_tool import tasks
from apps.fractional_cover import tasks
from apps.ndvi_anomaly import tasks
from apps.slip import tasks
from apps.tsm import tasks
from apps.water_detection import tasks
from apps.dc_algorithm.models import Application

_apps = Application.objects.all()
for app in _apps:
    camel_case = "".join(x.title() for x in app.pk.split('_'))
    task_model = apps.get_model(".".join([app.pk, camel_case + "Task"]))
    tasks = task_model.objects.filter(complete=False)
    run_func = globals()[app.pk].tasks.run
    for task in tasks:
        run_func.delay(task_id=task.pk)
