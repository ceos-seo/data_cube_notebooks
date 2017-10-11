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
import numpy as np

from utils.data_cube_utilities.dc_utilities import (create_cfmask_clean_mask, create_bit_mask)


class Satellite(models.Model):
    """Stores a satellite that exists in the Data Cube

    Stores a single instance of a Satellite object that contains all the information for
    Data Cube requests. This is both used to create Data Cube queries and to display forms
    on the UI.

    Attributes:
        datacube_platform: This should correspond with a Data Cube platform.
            e.g. LANDSAT_5, LANDSAT_7, SENTINEL_1A, etc. Combinations should be comma seperated with no spaces.
        name: Used to display forms to users
            e.g. Landsat 5, Landsat 7, Sentinel-1A
        product_prefix: In our Data Cube setup, we use product prefixes combined with an area.
            e.g. ls5_ledaps_{vietnam,colombia,australia}, s1a_gamma0_vietnam
            This should be the 'ls5_ledaps_' and 's1a_gamma0_' part of the above examples.
            You should be able to concat the product prefix and an area id to get a valid dataset query. In the case of
            combinations, you should have comma seperated strings with no spaces.
        date_min and date_max: Satellite valid data date range.
            e.g. If you have LS7 data from 2000-2016, you should use that as the date range.
        data_min/data_max: min/max values for your dataset. Used for scaling of pngs
        measurements: comma seperated list of measurements with all spaces omitted.
        no_data_value: No data value to be used for all outputs/masking functionality.

    """

    datacube_platform = models.CharField(
        help_text="This should correspond with a Data Cube platform. Combinations should be comma seperated with no spaces, e.g. LANDSAT_7,LANDSAT_8",
        max_length=50)
    name = models.CharField(max_length=25)
    product_prefix = models.CharField(
        max_length=250,
        help_text="Products are loaded by name with the naming convention product_prefix+area_id, e.g. ls5_ledaps_{vietnam,colombia,australia}, \
                   s1a_gamma0_vietnam. For combined products, prefixes should be comma seperated with no spaces in the order of the datacube_platform."
    )

    date_min = models.DateField('date_min', default=datetime.date.today)
    date_max = models.DateField('date_min', default=datetime.date.today)

    data_min = models.FloatField(
        help_text="Define the minimum of the valid range of this dataset. This is used for image creation/scaling.",
        default=0)
    data_max = models.FloatField(
        help_text="Define the maximum of the valid range of this dataset. This is used for image creation/scaling.",
        default=4096)

    measurements = models.CharField(
        help_text="Comma seperated list (no spaces) representing the list of measurements. e.g. 'red,green,blue,nir'",
        default="blue,green,red,nir,swir1,swir2,pixel_qa",
        max_length=250)

    no_data_value = models.FloatField(
        default=-9999, help_text='No data value to be used for all outputs/masking functionality.')

    class Meta:
        unique_together = (('datacube_platform', 'product_prefix'))

    def __str__(self):
        return self.datacube_platform

    def get_scale(self):
        return (self.data_min, self.data_max)

    def get_measurements(self):
        return self.measurements.split(",")

    def get_clean_mask_func(self):
        """Get the func required to generate a clear mask for a dataset. Defaults to returning all True

        The returned func will be specific to the measurements or product/platform and will take a single xr dataset
        argument, returning a boolean np array of the same shape as ds.
        
        """

        def return_all_true(ds):
            return np.full(ds[self.get_measurements()[0]].shape(), True)

        options = {
            'bit_mask': lambda ds: create_bit_mask(ds.pixel_qa, [1, 2]),
            'cf_mask': lambda ds: create_cfmask_clean_mask(ds.cf_mask),
            'default': lambda ds: return_all_true
        }
        key = 'bit_mask' if 'pixel_qa' in self.get_measurements() else 'cf_mask' if 'cf_mask' in self.get_measurements(
        ) else 'default'

        return options.get(key, return_all_true)

    def get_product(self, area_id):
        return self.product_prefix + area_id

    def is_combined_product(self):
        return len(self.datacube_platform.split(",")) > 1

    def get_platforms(self):
        return self.datacube_platform.split(",")

    def get_products(self, area_id):
        return [prefix + area_id for prefix in self.product_prefix.split(",")]

    def get_measurements(self):
        return self.measurements.split(",")


class Area(models.Model):
    """Stores an area corresponding to an area that has been ingested into the Data Cube.

    Areas define geographic regions that exist in a Data Cube. Attributes define the geographic range,
    imagery to use for the map view, and the satellites that we have acquired data for over the area.

    Attributes:
        id: This should correspond with a Data Cube product. The area id is combined
            with a satellite id to create a product id used to query the Data Cube for data.
            e.g. colombia, vietnam, australia will be used to create ls5_ledaps_colombia etc.
        name: Human readable name for the area
        latitude/longitude min/max: These bounds define the valid data region in the Data Cube.
            e.g. enter the bounds generated by get_datacube_metadata - this is used to create an outline on the map
            highlighting valid data.
        main_imagery: Path to an image to use as the globe imagery - it should be relatively high resolution if its a real image.
            The image at the entered path will be overlaid on the globe from [-180,180] longitude and [-90, 90] latitude.
            Defaults to black.png which is just a black background for the entire globe.
        detail_imagery: Path to an image to use as the base for our valid data region. This should be as close to the latitude/longitude
            min/max bounds as possible.
        thumbnail_imagery: path to an image to be used as a small icon on the region selection page.
        detail latitude/longitude min/max: These bounds should correspond to the actual bounds of the detail imagery. This is used to overlay
            the detail imagery on the globe just in case your detail image doesn't exactly match up with the valid data region.
        satellites: M2M field describing the satellites that we have data for over any given region. Only select satellites that the Data Cube
            has data ingested for - e.g. if we only have S1 over vietnam, we would leave colombia and australia unchecked.

    """

    id = models.CharField(max_length=250, default="", unique=True, primary_key=True)
    name = models.CharField(max_length=250, default="")

    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    thumbnail_imagery = models.CharField(max_length=250, default="")

    satellites = models.ManyToManyField(Satellite)

    def __str__(self):
        return self.id


class Application(models.Model):
    """Model containing the applications that are displayed on the UI.

    The Application model is used to control application attributes. An example of an application
    could be:
        NDVI: Computes the NDVI over any given region.
        Water Detection: Generates water detection images over a given region
        etc.

    This model is used in templates to create dropdown menus/route users to different apps.

    Attributes:
        id: Unique id used to identify apps.
        name: Human readable name for the app. Will be featured on UI pages.
        areas: M2M field outlining what areas should be displayed for each app. If we have an inland
            area with no standing water bodies, then we may not want to display water detection here
            so we would leave it unselected.
        satellites: M2M field outlining what satellties should be displayed for each tool. If water detection
            does not use SAR data, we would select only optical satellites here.
        application_group: Optional FK to a app group. Apps with no groups are displayed as single choices, otherwise
            they are in a multilevel dropdown by group.
        color_scale: path to a color scale image to be displayed in the main tool view. If no color scale is
            necessary, this should be left blank/null.

    """

    id = models.CharField(max_length=250, default="", unique=True, primary_key=True)
    name = models.CharField(max_length=250, default="")
    areas = models.ManyToManyField(Area)
    satellites = models.ManyToManyField(Satellite)

    color_scale = models.CharField(max_length=250, default="", blank=True, null=True)

    application_group = models.ForeignKey('ApplicationGroup', null=True, blank=True)

    def __str__(self):
        return self.id


class ApplicationGroup(models.Model):
    """
    Stores a grouping for applications. Optional, only field is a string.
    """
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Compositor(models.Model):
    """
    Stores a compositor including a human readable name and an id.
    The id is interpretted in each app.
    These are used to populate UI forms.
    """

    id = models.CharField(max_length=25, unique=True, primary_key=True)
    name = models.CharField(max_length=25)

    def __str__(self):
        return self.name

    def is_iterative(self):
        return self.id not in ["median_pixel", "geometric_median", "medoid"]
