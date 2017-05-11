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


class Result(models.Model):
    """Base Result model meant to be inherited by a TaskClass

    Serves as the base of all algorithm resluts, containing a status, number of scenes
    processed and total scenes (to generate progress bar), and a result path.
    The result path is required and is the path to the result that should be the
    *Default* result shown on the UI map. Other results can be added in subclasses.

    Constraints:
        result_path is required and must lead to an image that serves as the default result
            to be displayed to the user.

    Usage:
        In each app, subclass Result and add all fields (if desired).
        Subclass Meta as well to ensure the class remains abstract e.g.
            class AppResult(Result):
                sample_field = models.CharField(max_length=100)

                class Meta(Result.Meta):
                    pass

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    #either OK or ERROR or WAIT
    status = models.CharField(max_length=100, default="")
    #used to pass messages to the user.
    message = models.CharField(max_length=100, default="")

    scenes_processed = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)
    #default display result.
    result_path = models.CharField(max_length=250, default="")

    class Meta:
        abstract = True

    def get_progress(self):
        """Quantify the progress of a result's processing in terms of its own attributes

        Meant to return a representation of progress based on attributes set in a task.
        Should be overwritten in the task if scenes processed and total scenes aren't
        a useful representation

        Returns:
            An integer between 0 and 100

        """
        total_scenes = self.total_scenes if self.total_scenes > 0 else 1
        percent_complete = self.scenes_processed / total_scenes
        rounded_int = round(percent_complete * 100)
        clamped_int = max(0, min(rounded_int, 100))
        return
