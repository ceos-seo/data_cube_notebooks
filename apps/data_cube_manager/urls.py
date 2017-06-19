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

urlpatterns = [
    # dataset type related functionality - view list, view single, create new, delete
    url(r'^dataset_types$', views.DatasetTypeListView.as_view(), name=''),
    url(r'^dataset_types/view/(?P<dataset_type_id>[\w\-]+)$', views.DatasetTypeView.as_view(), name=''),
    url(r'^dataset_types/create$', views.CreateDatasetType.as_view(), name=''),
    url(r'^dataset_types/create/(?P<dataset_type_id>[\w\-]+)$', views.CreateDatasetType.as_view(), name=''),
    url(r'^validate_measurement$', views.ValidateMeasurement.as_view(), name=''),
    url(r'^dataset_types/add$', views.DatasetTypeView.as_view(), name=''),
    url(r'^dataset_types/export$', views.DatasetYamlExport.as_view(), name=''),
    url(r'^dataset_types/delete/(?P<dataset_type_id>[\w\-]+)$', views.DeleteDatasetType.as_view(), name=''),
    # Dataset related functionality - list all for dataset type, view single, download, delete
    url(r'^dataset_types/(?P<dataset_type_id>[\w\-]+)/datasets$', views.DatasetListView.as_view(), name=''),
    url(r'^dataset_types/(?P<dataset_type_id>[\w\-]+)/datasets/download/(?P<dataset_id>regex)$',
        views.DatasetListView.as_view(),
        name=''),
    url(r'^dataset_types/(?P<dataset_type_id>[\w\-]+)/datasets/delete$', views.DeleteDataset.as_view(), name=''),
]
