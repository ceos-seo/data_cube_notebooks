# Copyright 2016 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. All Rights Reserved.
#
# Portion of this code is Copyright Geoscience Australia, Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.contrib import admin
from .models import Query, Metadata, Result
from data_cube_ui.models import Satellite, Area, Compositor


class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user_id', 'platform', 'time_start')


class MetadataAdmin(admin.ModelAdmin):
    list_display = ('query_id',)


class ResultAdmin(admin.ModelAdmin):
    list_display = ('result_path', 'status', 'latitude_min', 'latitude_max', 'longitude_min', 'longitude_max',
                    'latitude_max', 'latitude_min', 'longitude_max', 'longitude_min')


class SatelliteAdmin(admin.ModelAdmin):
    list_display = ('satellite_id', 'satellite_name')


class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_id', 'area_name')


class CompositorAdmin(admin.ModelAdmin):
    list_display = ('compositor_id', 'compositor')


# Register your models here.
admin.site.register(Query, QueryAdmin)
admin.site.register(Metadata, MetadataAdmin)
admin.site.register(Result, ResultAdmin)
