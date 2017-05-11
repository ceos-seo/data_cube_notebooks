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


class GenericTask(Query, Metadata, Result):
    """Serves as the model for an algorithm task containing a Query, Metadata, and Result

    The generic task should be implemented by each application. Each app should subclass
    Query, Result, and Metadata, adding all desired fields according to docstrings. The
    app should then include a AppTask implementation that ties them all together:
        CustomMosaicTask(CustomMosaicQuery, CustomMosaicMetadata, CustomMosaicResult):
            pass

    This Generic task should not be subclassed and should be used only as a model for how
    things should be tied together at the app level.

    Constraints:
        Should subclass Query, Metadata, and Result (or a subclass of each)
        Should be used for all processing and be passed using a uuid pk
        Attributes should NOT be added to this class - add them to the inherited classes

    """

    pass

    class Meta:
        abstract = True
