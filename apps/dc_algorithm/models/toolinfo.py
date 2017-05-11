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

from django.db import models
from django.core.exceptions import ValidationError

import datetime
import uuid


class ToolInfo(models.Model):
    """Model used to handle the region selection page information and images.

    Stores images and information for the region selection page for each tool. Information includes
    the descriptions seen on the page as well as their respective images. For instance, if we want
    three images to scroll across the carousel, we would create three ToolInfo instances each with
    an image and description.

    Attributes:
        image_path: path to the banner image that is to be shown on the top of the page
        image_title: title describing the image - will be displayed on page.
        image_description: description text for the image. Will be displayed on page.

    """

    image_path = models.CharField(max_length=100)
    image_title = models.CharField(max_length=50)
    image_description = models.CharField(max_length=500)

    application = models.ForeignKey(Application)
