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
"""data_cube_ui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^custom_mosaic_tool/', include('apps.custom_mosaic_tool.urls')),
    url(r'^water_detection/', include('apps.water_detection.urls')),
    url(r'^tsm/', include('apps.tsm.urls')),
    url(r'^fractional_cover/', include('apps.fractional_cover.urls')),
    url(r'^slip/', include('apps.slip.urls')),
    url(r'^coastal_change/', include('apps.coastal_change.urls')),
    url(r'^ndvi_anomaly/', include('apps.ndvi_anomaly.urls')),
    url(r'^spectral_indices/', include('apps.spectral_indices.urls')),
    url(r'^cloud_coverage/', include('apps.cloud_coverage.urls')),
    url(r'^urbanization/', include('apps.urbanization.urls')),
    url(r'^task_manager/', include('apps.task_manager.urls')),
    url(r'^data_cube_manager/', include('apps.data_cube_manager.urls')),
    url(r'^accounts/', include('apps.accounts.urls')),
    url(r'^', include('apps.pages.urls')),
] + static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT)
