from django.contrib import admin

from .models import Satellite, Area, Compositor, Application, ApplicationGroup


class SatelliteAdmin(admin.ModelAdmin):
    list_display = ('datacube_platform', 'name')


class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class CompositorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


# Register your models here.
admin.site.register(Satellite, SatelliteAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Compositor, CompositorAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationGroup)
