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
    # visualization tool related functionality
    url(r'^visualization$', views.DataCubeVisualization.as_view(), name='visualization'),
    url(r'^get_ingested_areas$', views.GetIngestedAreas.as_view(), name='get_ingested_areas'),
    # dataset type related functionality - view list, view single, create new, delete
    url(r'^dataset_types$', views.DatasetTypeListView.as_view(), name='dataset_types'),
    url(r'^dataset_types/view/(?P<dataset_type_id>[\w\-]+)$', views.DatasetTypeView.as_view(), name='dataset_type'),
    url(r'^dataset_types/create$', views.CreateDatasetType.as_view(), name='create_dataset_type'),
    url(r'^dataset_types/create/(?P<dataset_type_id>[\w\-]+)$',
        views.CreateDatasetType.as_view(),
        name='create_dataset_type_from_base'),
    url(r'^dataset_types/validate_measurement$',
        views.ValidateMeasurement.as_view(),
        name='validate_dataset_type_measurement'),
    url(r'^dataset_types/add$', views.DatasetTypeView.as_view(), name='add_dataset_type'),
    url(r'^dataset_types/export$', views.DatasetYamlExport.as_view(), name='export_dataset_type'),
    url(r'^dataset_types/delete/(?P<dataset_type_id>[\w\-]+)$',
        views.DeleteDatasetType.as_view(),
        name='delete_dataset_type'),
    # Dataset related functionality - list all for dataset type, view single, download, delete
    url(r'^dataset_types/(?P<dataset_type_id>[\w\-]+)/datasets$',
        views.DatasetListView.as_view(),
        name='view_dataset_type_datasets'),
    url(r'^datasets$', views.DatasetListView.as_view(), name='datasets'),
    url(r'^datasets/delete$', views.DeleteDataset.as_view(), name='delete_datasets'),
    # Ingestion related functionality
    url(r'^ingestion$', views.CreateIngestionConfigurationView.as_view(), name='ingestion_configuration'),
    url(r'^ingestion/export$', views.CreateIngestionConfigurationView.as_view(), name='export_ingestion'),
    url(r'^ingestion/validate_measurement$',
        views.IngestionMeasurement.as_view(),
        name='validate_ingestion_measurement'),
    url(r'^ingestion/get_existing_measurements$',
        views.IngestionMeasurement.as_view(),
        name='get_existing_measurements'),
    url(r'^ingestion/run$', views.SubmitIngestion.as_view(), name='run_ingestion'),
    url(r'^ingestion/subset$', views.CreateDataCubeSubset.as_view(), name='create_ingestion_subset'),
    url(r'^ingestion/subset/check/(?P<ingestion_request_id>[\w\-]+)$',
        views.CheckIngestionRequestStatus.as_view(),
        name='check_ingestion_subset'),
]
