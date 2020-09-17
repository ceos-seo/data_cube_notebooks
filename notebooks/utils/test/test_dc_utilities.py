import unittest

import numpy as np
import xarray as xr
from datetime import datetime

from data_cube_utilities import dc_utilities


class TestDCUtilities(unittest.TestCase):

    def setUp(self):
        # yapf: disable

        self.times = [
            datetime(1999, 5, 6),
            datetime(2006, 1, 2),
            datetime(2006, 1, 16),
            datetime(2015, 12, 31),
            datetime(2016, 1, 1),
        ]

        self.latitudes = [1, 2]
        self.longitudes = [1, 2]

        self.sample_data = np.array([[[1, 1], [1, 1]],
                                     [[2, 2], [2, 2]],
                                     [[3, 3], [3, 3]],
                                     [[0, 0], [0, 0]],
                                     [[5, 5], [5, 5]]])
        # yapf: enable

    def tearDown(self):
        pass

    def test_create_cfmask_clean_mask(self):
        dataset = xr.Dataset(
            {
                'cf_mask': (('time', 'latitude', 'longitude'), self.sample_data)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        cf_mask = dc_utilities.create_cfmask_clean_mask(dataset.cf_mask)

        self.assertTrue((cf_mask == np.array([[[True, True], [True, True]], [[False, False], [False, False]],
                                              [[False, False], [False, False]], [[True, True], [True, True]],
                                              [[False, False], [False, False]]])).all())

    def test_perform_timeseries_analysis(self):
        pass

    # def test_nan_to_num(self):
    #     dataset = xr.Dataset(
    #         {
    #             'data': (('time', 'latitude', 'longitude'), self.sample_data)
    #         },
    #         coords={'time': self.times,
    #                 'latitude': self.latitudes,
    #                 'longitude': self.longitudes})

    #     dataset_nan = dataset.where(dataset.data > 2)

    #     dc_utilities.nan_to_num(dataset_nan, -9999)

    #     self.assertTrue((dataset_nan.data.values == np.array(
    #         [[[-9999, -9999], [-9999, -9999]], [[-9999, -9999], [-9999, -9999]], [[3, 3], [3, 3]],
    #          [[-9999, -9999], [-9999, -9999]], [[5, 5], [5, 5]]])).all())

    def test_clear_attrs(self):
        dataset = xr.Dataset(
            {
                'data': (('time', 'latitude', 'longitude'), self.sample_data)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes},
            attrs={'temp_attrs': 5})

        dc_utilities.clear_attrs(dataset)

        self.assertTrue(not dataset.attrs)

    def test_create_bit_mask(self):
        pass

    def test_add_timestamp_data_to_xr(self):
        pass

    def test_write_geotiff_from_xr(self):
        pass

    def test_write_png_from_xr(self):
        pass

    def test_write_single_band_png_from_xr(self):
        pass

    def test_get_transform_from_xr(self):
        pass

    def test_chunks(self):
        pass
