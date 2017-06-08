from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.apps import apps

# This is pretty horrible.
from apps import *
from apps.dc_algorithm.models import Application


class Command(BaseCommand):
    help = 'Run test cases based on uncompleted tasks that exist in the database. Use loaddata to load in some test cases before running this script.'

    def handle(self, *args, **options):
        _apps = Application.objects.all()
        for app in _apps:
            self.stdout.write(self.style.SUCCESS("Running test cases for " + app.pk))
            camel_case = "".join(x.title() for x in app.pk.split('_'))
            task_model = apps.get_model(".".join([app.pk, camel_case + "Task"]))
            tasks = task_model.objects.filter(complete=False)
            run_func = globals()[app.pk].tasks.run
            for task in tasks:
                run_func.delay(task_id=task.pk)
