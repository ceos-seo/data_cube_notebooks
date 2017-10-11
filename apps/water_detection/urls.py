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

from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^region_selection', views.RegionSelection.as_view(), name='region_selection'),
    url(r'^submit$', views.SubmitNewRequest.as_view(), name='submit_new_request'),
    url(r'^submit_pixel_drill_request$', views.SubmitPixelDrillRequest.as_view(), name='submit_pixel_drill_request'),
    url(r'^submit_single$', views.SubmitNewSubsetRequest.as_view(), name='submit_new_single_request'),
    url(r'^cancel$', views.CancelRequest.as_view(), name='cancel_request'),
    url(r'^result$', views.GetTaskResult.as_view(), name='get_result'),
    url(r'^task_details/(?P<uuid>[^/]+)', views.TaskDetails.as_view(), name='get_task_details'),
    url(r'^(?P<area_id>[\w\-]+)/task_history$', views.UserHistory.as_view(), name='get_task_history'),
    url(r'^(?P<area_id>[\w\-]+)/results_list$', views.ResultList.as_view(), name='get_results_list'),
    url(r'^(?P<area_id>[\w\-]+)/output_list$', views.OutputList.as_view(), name='get_output_list'),
    url(r'^(?P<area_id>[\w\-]+)/$', views.WaterDetectionTool.as_view(), name='water_detection')
]
