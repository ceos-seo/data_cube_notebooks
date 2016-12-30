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

# pulled from peterbe.com since there were benchmarks listed.
# removes duplicates from python lists.
def uniquify_list(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def update_model_bounds_with_dataset(model_list, dataset):
    for model in model_list:
        model.latitude_max = dataset.latitude.values[0]
        model.latitude_min = dataset.latitude.values[-1]
        model.longitude_max = dataset.longitude.values[-1]
        model.longitude_min = dataset.longitude.values[0]
        model.save()

def map_ranges(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    import numpy as np
    # Convert the left range into a 0-1 range (float)
    valueScaled = (value.astype(np.float64) - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)
