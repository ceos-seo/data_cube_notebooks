from django.contrib import admin

from .models import Satellite, Area, Compositor, Application, Baseline, ToolInfo


class SatelliteAdmin(admin.ModelAdmin):
    list_display = ('datacube_platform', 'name')


class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class CompositorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class BaselineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class ToolInfoAdmin(admin.ModelAdmin):
    list_display = ('get_application', 'image_title', 'image_description')

    def get_application(self, obj):
        return obj.application.application_id


# Register your models here.
admin.site.register(Satellite, SatelliteAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Compositor, CompositorAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Baseline, BaselineAdmin)
admin.site.register(ToolInfo, ToolInfoAdmin)
