import unittest

from datetime import datetime
import numpy as np
import xarray as xr

from data_cube_utilities.dc_mosaic import (create_mosaic, create_mean_mosaic, create_median_mosaic,

                                           create_max_ndvi_mosaic, create_min_ndvi_mosaic,
                                           create_hdmedians_multiple_band_mosaic)

class TestMosaic(unittest.TestCase):

    def setUp(self):
        self.times = [
            datetime(1999, 5, 6),
            datetime(2006, 1, 2),
            datetime(2006, 1, 16),
            datetime(2015, 12, 31),
            datetime(2016, 1, 1),
        ]

        self.latitudes = [1, 2]
        self.longitudes = [1, 2]

        # yapf: disable
        self.sample_clean_mask = np.array([[[True, True], [False, False]],
                                           [[True, False], [True, False]],
                                           [[False, False], [True, False]],
                                           [[False, True], [True, False]],
                                           [[True, True], [False, False]]])

        self.sample_data = np.array([[[1, 1], [1, 1]],
                                     [[2, 2], [2, 2]],
                                     [[3, 3], [3, 3]],
                                     [[4, 4], [4, 4]],
                                     [[5, 5], [5, 5]]])

        self.nir = np.array([[[0, 1], [0, 80]],
                             [[1, 4], [1, 60]],
                             [[0, 0], [2, 0]],
                             [[1, 5], [1, 20]],
                             [[2, 1], [1, 0]]])

        self.red = np.array([[[15, 1], [5, 1]],
                             [[1, 1], [1, 1]],
                             [[1, 5], [1, 1]],
                             [[1, 1], [1, 1]],
                             [[1, 1], [1, 4]]])

        self.blue = np.array([[[62, 15], [31,  0]],
                              [[42, 91], [ 3, 18]],
                              [[44, 53], [45, 23]],
                              [[72, 53], [88, 32]],
                              [[28, 91], [86, 67]]])

        self.green = np.array([[[58, 92], [61, 64]],
                               [[86, 41], [70, 99]],
                               [[14, 70], [27, 14]],
                               [[54,  2], [30, 45]],
                               [[18,  6], [16, 44]]])

        self.swir1 = np.array([[[53,  0], [48, 12]],
                               [[58, 53], [45, 70]],
                               [[ 4, 81], [58, 79]],
                               [[22, 68], [47, 26]],
                               [[40, 75], [39, 58]]])

        self.swir2 = np.array([[[55, 88], [88, 40]],
                               [[70, 38], [84, 98]],
                               [[77, 17], [ 8, 30]],
                               [[19, 42], [ 0, 27]],
                               [[ 6, 56], [ 5, 99]]])
 # yapf: enable

    def tearDown(self):
        pass

    def test_create_mosaic(self):

        dataset = xr.Dataset(
            {
                'test_data': (('time', 'latitude', 'longitude'), self.sample_data)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        mosaic_dataset = create_mosaic(dataset, clean_mask=self.sample_clean_mask, no_data=-9999)
        mosaic_dataset_reversed = create_mosaic(
            dataset, clean_mask=self.sample_clean_mask, no_data=-9999, reverse_time=True)

        self.assertTrue((mosaic_dataset.test_data.values == np.array([[1, 1], [2, -9999]])).all())
        self.assertTrue((mosaic_dataset_reversed.test_data.values == np.array([[5, 5], [4, -9999]])).all())

        self.assertTrue('time' not in mosaic_dataset)

        mosaic_dataset_iterated = create_mosaic(
            dataset,
            intermediate_product=mosaic_dataset,
            clean_mask=np.full(self.sample_clean_mask.shape, True),
            no_data=-9999)

        self.assertTrue((mosaic_dataset_iterated.test_data.values == np.array([[1, 1], [2, 1]])).all())

    def test_create_mean_mosaic(self):

        dataset = xr.Dataset(
            {
                'test_data': (('time', 'latitude', 'longitude'), self.sample_data)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        mosaic_dataset = create_mean_mosaic(dataset, clean_mask=self.sample_clean_mask, no_data=-9999)

        self.assertTrue((mosaic_dataset.test_data.values == np.array([[2, 3], [3, -9999]])).all())

        self.assertTrue('time' not in mosaic_dataset)

    def test_create_median_mosaic(self):
        dataset = xr.Dataset(
            {
                'test_data': (('time', 'latitude', 'longitude'), self.sample_data)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        mosaic_dataset = create_median_mosaic(dataset, clean_mask=self.sample_clean_mask, no_data=-9999)

        self.assertTrue((mosaic_dataset.test_data.values == np.array([[2, 4], [3, -9999]])).all())

        self.assertTrue('time' not in mosaic_dataset)

    def test_create_max_ndvi_mosaic(self):
        dataset = xr.Dataset(
            {
                'test_data': (('time', 'latitude', 'longitude'), self.sample_data),
                'red': (('time', 'latitude', 'longitude'), self.red),
                'nir': (('time', 'latitude', 'longitude'), self.nir)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        mosaic_dataset = create_max_ndvi_mosaic(
            dataset, clean_mask=np.full(self.sample_clean_mask.shape, True), no_data=-9999)

        self.assertTrue((mosaic_dataset.test_data.values == np.array([[5, 4], [3, 1]])).all())
        self.assertTrue('time' not in mosaic_dataset)

        dataset_mins = dataset.copy(deep=True)
        dataset_mins.nir.values = np.array([[[0, 1], [0, 80]], [[1, 4], [1, 60]], [[100, 100], [100, 100]],
                                            [[1, 5], [1, 20]], [[2, 1], [1, 0]]])

        mosaic_dataset_iterated = create_max_ndvi_mosaic(
            dataset_mins,
            intermediate_product=mosaic_dataset,
            clean_mask=np.full(self.sample_clean_mask.shape, True),
            no_data=-9999)

        self.assertTrue((mosaic_dataset_iterated.test_data.values == np.array([[3, 3], [3, 3]])).all())

    def test_create_min_ndvi_mosaic(self):
        dataset = xr.Dataset(
            {
                'test_data': (('time', 'latitude', 'longitude'), self.sample_data),
                'red': (('time', 'latitude', 'longitude'), self.red),
                'nir': (('time', 'latitude', 'longitude'), self.nir)
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        mosaic_dataset = create_min_ndvi_mosaic(
            dataset, clean_mask=np.full(self.sample_clean_mask.shape, True), no_data=-9999)

        self.assertTrue((mosaic_dataset.test_data.values == np.array([[1, 3], [1, 3]])).all())
        self.assertTrue('time' not in mosaic_dataset)

        dataset_mins = dataset.copy(deep=True)
        dataset_mins.nir.values = np.array([[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-100, -100], [-100, -100]],
                                            [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]]])
        dataset_mins.red.values = np.array([[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[100, 100], [100, 100]],
                                            [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]]])

        mosaic_dataset_iterated = create_min_ndvi_mosaic(
            dataset_mins,
            intermediate_product=mosaic_dataset,
            clean_mask=np.full(self.sample_clean_mask.shape, True),
            no_data=-9999)
        print(mosaic_dataset_iterated, mosaic_dataset)
        self.assertTrue((mosaic_dataset_iterated.test_data.values == np.array([[3, 3], [3, 3]])).all())

    def test_create_geo_median_multiple_band_mosaic(self):
        dataset = xr.Dataset(
            {
                'red': (('time', 'latitude', 'longitude'), self.red),
                'blue': (('time', 'latitude', 'longitude'), self.blue),
                'green': (('time', 'latitude', 'longitude'), self.green),
                'nir': (('time', 'latitude', 'longitude'), self.nir),
                'swir1': (('time', 'latitude', 'longitude'), self.swir1),
                'swir2': (('time', 'latitude', 'longitude'), self.swir2),
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        test_mosaic = create_hdmedians_multiple_band_mosaic(dataset, self.sample_clean_mask, operation="median")
        dataset_swir1 = np.array([[52.795282, 64.96945], [57.762149, -9999]])
        dataset_swir2 = np.array([[53.79578, 48.799493], [8.378129, -9999]])
        dataset_nir = np.array([[0.230488, 3.703346], [1.97955, -9999]])
        dataset_red = np.array([[12.599269, 1.], [1., -9999]])
        dataset_green = np.array([[58.789003, 9.373638], [27.319318, -9999]])
        dataset_blue = np.array([[57.744289, 59.947858], [45.331181, -9999]])

        print(test_mosaic)

        self.assertTrue(np.isclose(test_mosaic.swir1, dataset_swir1, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.swir2, dataset_swir2, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.nir, dataset_nir, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.blue, dataset_blue, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.red, dataset_red, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.green, dataset_green, equal_nan=True).all())

    def test_create_medoid_multiple_band_mosaic(self):
        dataset = xr.Dataset(
            {
                'red': (('time', 'latitude', 'longitude'), self.red),
                'blue': (('time', 'latitude', 'longitude'), self.blue),
                'green': (('time', 'latitude', 'longitude'), self.green),
                'nir': (('time', 'latitude', 'longitude'), self.nir),
                'swir1': (('time', 'latitude', 'longitude'), self.swir1),
                'swir2': (('time', 'latitude', 'longitude'), self.swir2),
            },
            coords={'time': self.times,
                    'latitude': self.latitudes,
                    'longitude': self.longitudes})

        test_mosaic = create_hdmedians_multiple_band_mosaic(dataset, self.sample_clean_mask, operation="medoid")
        dataset_swir1 = np.array([[53., 68.], [58., -9999]])
        dataset_swir2 = np.array([[55., 42.], [8., -9999]])
        dataset_nir = np.array([[0., 5.], [2., -9999]])
        dataset_red = np.array([[15., 1.], [1., -9999]])
        dataset_green = np.array([[58., 2.], [27., -9999]])
        dataset_blue = np.array([[62., 53.], [45., -9999]])

        self.assertTrue(np.isclose(test_mosaic.swir1, dataset_swir1, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.swir2, dataset_swir2, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.nir, dataset_nir, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.blue, dataset_blue, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.red, dataset_red, equal_nan=True).all())
        self.assertTrue(np.isclose(test_mosaic.green, dataset_green, equal_nan=True).all())
