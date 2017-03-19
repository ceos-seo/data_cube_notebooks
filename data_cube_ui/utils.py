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
import os
import shutil
import datetime


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


def n64_to_datetime(n64):
    b = n64.astype(object)
    return datetime.datetime.fromtimestamp(int(b / 1000000000))


#combines metadata with common indices and keys. Params: current meta, desired additions (list/iterable)
#returns: updated meta
def combine_metadata(metadata, additions):
    for addition in additions:
        for acquisition_date in addition:
            if acquisition_date in metadata:
                for key in metadata[acquisition_date]:
                    if isinstance(metadata[acquisition_date][key], str):
                        metadata[acquisition_date][key] = addition[acquisition_date][key]
                    else:
                        metadata[acquisition_date][key] += addition[acquisition_date][key]
            else:
                metadata[acquisition_date] = addition[acquisition_date]
    return metadata


def cancel_task(query, result, base_path):
    print("Cancelled task.")
    try:
        shutil.rmtree(base_path + query.query_id)
    except:
        pass
    query.delete()
    result.delete()


def error_with_message(result, message, base_path):
    """
    Errors out under specific circumstances, used to pass error msgs to user. Uses the result path as
    a message container: TODO? Change this.

    Args:
        result (Result): The current result of the query being ran.
        message (string): The message to be stored in the result object.

    Returns:
        Nothing is returned as the method is ran asynchronously.
    """
    print("Task error.")
    try:
        pass
        #shutil.rmtree(base_path + result.query_id)
    except:
        pass
    result.status = "ERROR"
    result.result_path = message
    result.save()
    return
