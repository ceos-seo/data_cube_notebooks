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

from django.conf.urls import url

from . import views

# Author: AHDS
# Creation date: 2016-06-23
# Modified by:
# Last modified date:

urlpatterns = [
    url(r'^submit$', views.submit_new_request, name='submit_new_request'),
    url(r'^submit_single$', views.submit_new_single_request, name='submit_new_single_request'),
    url(r'^cancel$', views.cancel_request, name='cancel_request'),
    url(r'^result$', views.get_result, name='get_result'),
    url(r'^(?P<area_id>[\w\-]+)/query_history$', views.get_query_history, name='get_query_history'),
    url(r'^(?P<area_id>[\w\-]+)/results_list$', views.get_results_list, name='get_results_list'),
    url(r'^(?P<area_id>[\w\-]+)/output_list$', views.get_output_list, name='get_output_list'),
    url(r'^(?P<area_id>[\w\-]+)/$', views.tsm, name='tsm')
]
