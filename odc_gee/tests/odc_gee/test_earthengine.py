import os
import unittest
from pathlib import Path

from tests.odc_gee.test_indexing import IndexerTestCase
from xarray import Dataset

from odc_gee import earthengine

DATACUBE_CONFIG = f'{Path(__file__).parent.parent.absolute()}/datacube.conf'
HOME = os.getenv('HOME')
CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS',
                        f'{HOME}/.config/odc-gee/credentials.json')

class DatacubeTestCase(unittest.TestCase):
    def test_init(self):
        datacube = earthengine.Datacube(config=DATACUBE_CONFIG, credentials=CREDENTIALS)
        self.assertIsInstance(datacube, earthengine.Datacube,
                              'Cannot init earthengine.Datacube')
        return datacube

    def test_singleton(self):
        dc1 = self.test_init()
        dc2 = self.test_init()
        self.assertEqual(id(dc1), id(dc2),
                         'There can only be one earthengine.Datacube instance')

    def test_destruction(self):
        self.assertNotIn('EEDA_BEARER', os.environ,
                         'Credentials not being removed from environment')

    def test_normal_load(self):
        IndexerTestCase().test_product_generation()
        datacube = self.test_init()
        params = dict(product='ls8_test',
                      latitude=(-4.15, -3.90),
                      longitude=(39.50, 39.75),
                      time='2020-01',
                      measurements=['B3'])
        dataset = datacube.load(**params)
        self.assertIsInstance(dataset, Dataset,
                              'Did to load as an xarray.Dataset')
        self.assertIn('time', dataset,
                      'Expected time coordinate in Dataset')

    def test_asset_load(self):
        IndexerTestCase().test_product_generation()
        datacube = self.test_init()
        params = dict(asset='LANDSAT/LC08/C01/T1_SR',
                      resolution=(-2.69493352e-4, 2.69493352e-4),
                      output_crs='EPSG:4326',
                      latitude=(-4.15, -3.90),
                      longitude=(39.50, 39.75),
                      time='2020-01',
                      measurements=['B3'])
        dataset = datacube.load(**params)
        self.assertIsInstance(dataset, Dataset,
                              'Failed to load as an xarray.Dataset')
        self.assertIn('time', dataset,
                      'Expected time coordinate in Dataset')

if __name__ == '__main__':
    unittest.main()
