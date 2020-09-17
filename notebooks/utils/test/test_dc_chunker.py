import unittest

from datetime import datetime
from data_cube_utilities import dc_chunker
import xarray as xr
import numpy as np


class TestChunker(unittest.TestCase):

    def setUp(self):
        self.negative_to_positive = (-1, 1)
        self.positive_to_negative = (1, -1)
        self.dates = [
            datetime(2005, 1, 1), datetime(2006, 1, 1), datetime(2007, 5, 3), datetime(2014, 2, 1), datetime(2000, 1, 1)
        ]

    def tearDown(self):
        pass

    def test_create_geographic_chunks(self):
        with self.assertRaises(AssertionError):
            dc_chunker.create_geographic_chunks(longitude=self.positive_to_negative, latitude=self.positive_to_negative)
        with self.assertRaises(AssertionError):
            dc_chunker.create_geographic_chunks(longitude=(0, 1, 2), latitude=self.negative_to_positive)

        geographic_chunk_data = dc_chunker.create_geographic_chunks(
            longitude=self.negative_to_positive, latitude=self.negative_to_positive, geographic_chunk_size=0.1)

        self.assertTrue(len(geographic_chunk_data) == 40)
        for geographic_chunk in geographic_chunk_data:
            self.assertTrue(geographic_chunk['longitude'] == self.negative_to_positive)
            self.assertTrue(geographic_chunk['latitude'][0] >= self.negative_to_positive[0])
            self.assertTrue(geographic_chunk['latitude'][1] <= self.negative_to_positive[1])

        self.assertTrue(geographic_chunk_data[0]['latitude'][0] == self.negative_to_positive[0])
        self.assertTrue(geographic_chunk_data[-1]['latitude'][1] == self.negative_to_positive[1])

    def test_combine_geographic_chunks(self):
        longitude_values = list(range(0, 10, 1))
        latitude_ranges = [list(range(x * 10, x * 10 + 11, 1)) for x in range(10)]

        dataset_chunks = [
            xr.Dataset(
                {
                    'test_data': (('latitude', 'longitude'), np.ones((len(latitude_values), len(longitude_values))))
                },
                coords={'latitude': latitude_values,
                        'longitude': longitude_values}) for latitude_values in latitude_ranges
        ]

        combined_data = dc_chunker.combine_geographic_chunks(dataset_chunks)

        self.assertTrue(len(combined_data.latitude) == 101)
        self.assertTrue(len(combined_data.longitude) == 10)
        self.assertTrue(combined_data.test_data.values.shape == (101, 10))

    def test_create_time_chunks(self):
        date_groups = dc_chunker.create_time_chunks(self.dates, time_chunk_size=2)
        self.assertTrue(len(date_groups) == 3)
        self.assertTrue(date_groups[0][0] == min(self.dates))
        self.assertTrue(date_groups[-1][-1] == max(self.dates))

        date_groups = dc_chunker.create_time_chunks(self.dates, time_chunk_size=10)
        self.assertTrue(len(date_groups) == 1)

        date_groups = dc_chunker.create_time_chunks(self.dates, _reversed=True, time_chunk_size=2)
        self.assertTrue(date_groups[0][0] == max(self.dates))
        self.assertTrue(date_groups[-1][-1] == min(self.dates))

    def test_group_datetimes_by_year(self):
        date_groups = dc_chunker.group_datetimes_by_year(self.dates)
        self.assertTrue(len(date_groups.keys()) == 5)

        for key in date_groups:
            self.assertTrue(len(date_groups[key]) == 1)

    def test_group_datetimes_by_month(self):
        date_groups = dc_chunker.group_datetimes_by_month(self.dates)
        self.assertTrue(len(date_groups.keys()) == 3)
        self.assertTrue(len(date_groups[1]) == 3)

        date_groups = dc_chunker.group_datetimes_by_month(self.dates, months=[2, 5])
        self.assertTrue(len(date_groups.keys()) == 2)

        date_groups = dc_chunker.group_datetimes_by_month(self.dates, months=[])
        self.assertFalse(date_groups)

    def test_generate_baseline(self):
        baseline_iterable = sorted(self.dates)

        baseline = dc_chunker.generate_baseline(baseline_iterable, window_length=10)
        self.assertTrue(len(baseline) == 1)
        self.assertTrue(len(baseline[0]) == 5)

        baseline = dc_chunker.generate_baseline(baseline_iterable, window_length=2)
        self.assertTrue(len(baseline) == 3)
        self.assertTrue(len(baseline[0]) == 3)
