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
from .models import Query, Metadata, Result, ResultType
from data_cube_ui.models import Satellite, Area, Compositor

class QueryAdmin(admin.ModelAdmin):
    list_display = ('id','title','user_id','platform','time_start_display','time_end_display')

    def time_start_display(self, obj):
        return obj.time_start.strftime("%m/%d/%Y")
    time_start_display.admin_order_field = 'time_start'

    def time_end_display(self, obj):
        return obj.time_end.strftime("%m/%d/%Y")
    time_end_display.admin_order_field = 'time_end'

class MetadataAdmin(admin.ModelAdmin):
    list_display = ('query_id',)

class ResultAdmin(admin.ModelAdmin):
    list_display = ('result_path','status','latitude_min','latitude_max','longitude_min','longitude_max','latitude_max','latitude_min','longitude_max','longitude_min')

class ResultTypeAdmin(admin.ModelAdmin):
    list_display = ('satellite_id','result_id','result_type')

# Register your models here.

admin.site.register(Query, QueryAdmin)
admin.site.register(Metadata, MetadataAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(ResultType, ResultTypeAdmin)
