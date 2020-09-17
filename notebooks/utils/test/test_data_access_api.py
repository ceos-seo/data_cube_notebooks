import unittest
from data_cube_utilities.data_access_api import DataAccessApi

from datetime import datetime
import xarray as xr
import numpy as np


class TestDataAccessApi(unittest.TestCase):

    def setUp(self):
        self.dc_api = DataAccessApi(config="/home/localuser/Datacube/data_cube_ui/config/.datacube.conf")

    def tearDown(self):
        self.dc_api.close()

    def test_get_dataset_by_extent(self):
        product = 'ls7_ledaps_meta_river'
        fake_product = 'fake1'
        kwargs = {
            'time': (datetime(2015, 1, 1), datetime(2015, 3, 1)),
            'longitude': (-71.6, -71.5),
            'latitude': (4.5, 4.6),
            'measurements': ['red', 'green', 'blue']
        }
        data = self.dc_api.get_dataset_by_extent(product, **kwargs)
        fake_data = self.dc_api.get_dataset_by_extent(fake_product, **kwargs)

        self.assertTrue(type(data) == xr.Dataset)
        self.assertFalse(fake_data)
        self.assertIn('red', data)

    def test_get_stacked_datasets_by_extent(self):
        products = ['ls7_ledaps_meta_river', 'ls8_ledaps_meta_river']
        fake_products = ['fake1', 'fake2']
        kwargs = {
            'time': (datetime(2015, 1, 1), datetime(2015, 3, 1)),
            'longitude': (-71.6, -71.5),
            'latitude': (4.5, 4.6),
            'measurements': ['red', 'green', 'blue']
        }
        data = self.dc_api.get_stacked_datasets_by_extent(products, **kwargs)
        fake_data = self.dc_api.get_stacked_datasets_by_extent(fake_products, **kwargs)

        self.assertIsNone(fake_data)
        self.assertIn('red', data)
        self.assertIn('satellite', data)
        self.assertTrue(type(data) == xr.Dataset)

    def test_get_query_metadata(self):
        faked_data = self.dc_api.get_datacube_metadata('ls7_collections_sr_scene_fake')
        self.assertTrue(faked_data['scene_count'] == 0)

        datacube_data = self.dc_api.get_datacube_metadata('ls7_ledaps_ghana')
        expected_contents = ['time_extents', 'lat_extents', 'lon_extents', 'tile_count', 'pixel_count']
        for var in expected_contents:
            self.assertIn(var, datacube_data)

        self.assertTrue(type(datacube_data['time_extents'][0]) == datetime)
        self.assertTrue(type(datacube_data['lat_extents'][0]) == float)

    def test_list_acquisition_dates(self):
        faked_dates = self.dc_api.list_acquisition_dates('fake1')
        self.assertFalse(faked_dates)

        ghana_dates = self.dc_api.list_acquisition_dates('ls7_ledaps_ghana')
        self.assertTrue(len(ghana_dates) > 0)
        self.assertTrue(type(ghana_dates[0]) == datetime)

    def test_list_combined_acquisition_dates(self):
        faked_dates = self.dc_api.list_combined_acquisition_dates(['fake1', 'fake2'])
        self.assertFalse(faked_dates)

        ghana_dates = self.dc_api.list_combined_acquisition_dates(['ls7_ledaps_ghana'])
        tonga_dates = self.dc_api.list_combined_acquisition_dates(['ls7_ledaps_tonga'])
        combined_date_list = self.dc_api.list_combined_acquisition_dates(['ls7_ledaps_tonga', 'ls7_ledaps_ghana'])
        combined_date_list_with_fake = self.dc_api.list_combined_acquisition_dates(
            ['ls7_ledaps_tonga', 'ls7_ledaps_ghana', 'fake1'])

        self.assertTrue(len(ghana_dates) > 0)
        self.assertTrue(type(ghana_dates[0]) == datetime)
        self.assertTrue(len(ghana_dates) + len(tonga_dates) == len(combined_date_list))
        self.assertTrue(len(combined_date_list) == len(combined_date_list_with_fake))

    def test_get_full_dataset_extent(self):
        faked_data = self.dc_api.get_full_dataset_extent('ls7_collections_sr_scene_fake')
        self.assertTrue(len(faked_data) == 0)

        datacube_data = self.dc_api.get_full_dataset_extent('ls7_ledaps_ghana')
        expected_contents = ['time', 'latitude', 'longitude']
        for var in expected_contents:
            self.assertIn(var, datacube_data)
            self.assertTrue(type(datacube_data[var]) == xr.DataArray)

    def test_get_datacube_metadata(self):
        faked_data = self.dc_api.get_datacube_metadata('ls7_collections_sr_scene_fake')
        self.assertTrue(faked_data['scene_count'] == 0)

        datacube_data = self.dc_api.get_datacube_metadata('ls7_ledaps_ghana')
        expected_contents = ['time_extents', 'lat_extents', 'lon_extents', 'tile_count', 'pixel_count']
        for var in expected_contents:
            self.assertIn(var, datacube_data)

        self.assertTrue(type(datacube_data['time_extents'][0]) == datetime)
        self.assertTrue(type(datacube_data['lat_extents'][0]) == float)

    def test_validate_measurements(self):
        self.assertTrue(
            self.dc_api.validate_measurements('ls7_collections_sr_scene', ['sr_band1', 'sr_band2', 'sr_band3']))
        self.assertFalse(
            self.dc_api.validate_measurements('ls7_collections_sr_scene', ['not', 'valid', 'measurements']))
        self.assertFalse(
            self.dc_api.validate_measurements('ls7_collections_sr_scene_fake', ['sr_band1', 'sr_band2', 'sr_band3']))
