from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings

import os
import shutil

from apps.dc_algorithm.models import Application, Area, Satellite


class Command(BaseCommand):
    help = 'Create a new band-math only application that creates a mosaic and applys your bandmath.'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str)

    def handle(self, *args, **options):
        app_name = options.get('app_name')
        components = app_name.split('_')
        camel_case = "".join(x.title() for x in components)
        name = " ".join(x.title() for x in components)
        self.stdout.write(self.style.SUCCESS("Creating app " + camel_case))

        app_path = os.path.join(settings.BASE_DIR, 'apps', app_name)

        shutil.copytree(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'band_math_app'), app_path)
        templates_path = os.path.join(app_path, 'templates', 'band_math_app')
        os.rename(templates_path, os.path.join(app_path, 'templates', app_name))
        self.stdout.write(self.style.SUCCESS("Copied files..."))
        #string replacement for constants.
        commands = [
            "find " + app_path + " -type f -exec sed -i 's/band_math_app/" + app_name + "/g' {} +",
            "find " + app_path + " -type f -exec sed -i 's/BandMathApp/" + camel_case + "/g' {} +",
            "find " + app_path + " -type f -exec sed -i 's/BandMathTask/" + camel_case + "Task" + "/g' {} +"
        ]
        for command in commands:
            os.system(command)
        self.stdout.write(self.style.SUCCESS("Renamed constants..."))

        app = Application(id=app_name, name=name)
        app.save()
        #can't init with satellite values, have to save first...
        app.satellites = Satellite.objects.filter(datacube_platform__in=['LANDSAT_5', 'LANDSAT_7', 'LANDSAT_8'])
        app.areas = Area.objects.all()
        app.save()

        self.stdout.write(self.style.SUCCESS("Initialized base models..."))
        self.stdout.write(self.style.SUCCESS("Done! Follow the instructions below to finish your new apps creation."))

        self.stdout.write("Add the string: "
                          "url(r'^" + app_name + "/', include('apps." + app_name + ".urls')) to data_cube_ui/urls.py")
        self.stdout.write("Add the string: "
                          "'apps." + app_name + "', to data_cube_ui/settings.py in the INSTALLED_APPS list.")
        self.stdout.write("Create a GDAL Dem compatible color scale in utils/color_scales/ named " + app_name)
        self.stdout.write(
            "A default red-> green color scale will be used until you create your color scale. Change the path to the color scale in your new models.py - Query"
        )
        self.stdout.write("Run 'makemigrations' and 'migrate'")
        self.stdout.write("Run 'python manage.py loaddata apps/" + app_name + "/fixtures/init.json'")
