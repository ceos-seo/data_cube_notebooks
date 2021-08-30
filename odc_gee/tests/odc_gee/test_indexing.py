from pathlib import Path
import unittest

from datacube.model import DatasetType

from odc_gee import indexing

DATACUBE_CONFIG = f'{Path(__file__).parent.parent.absolute()}/datacube.conf'

class IndexerTestCase(unittest.TestCase):
    def test_init(self):
        indexer = indexing.Indexer(app='IndexerTest', config=DATACUBE_CONFIG)
        self.assertIsInstance(indexer, indexing.Indexer,
                              'Failed to init Indexer')
        return indexer

    def test_product_generation(self):
        indexer = self.test_init()
        # Possible check to skip tests if product already exists in DB
        #if indexer.datacube.index.products.get_by_name('ls8_test'):
        #    self.skipTest('Product already exists in database')
        params = dict(asset='LANDSAT/LC08/C01/T1_SR',
                      product='ls8_test',
                      resolution=(-2.69493352e-4, 2.69493352e-4),
                      output_crs='EPSG:4326')
        product = indexer.generate_product(**params)
        self.assertIsInstance(product, DatasetType,
                              'Product does not match datacube.model.DatasetType')
        self.assertEqual(indexer.datacube.index.products.get_by_name('ls8_test'),
                         product,
                         'Could not find product in database')

    def test_parse_time(self):
        indexer = self.test_init()
        asset = 'LANDSAT/LC08/C01/T1_SR'
        times = [('2020', ['2020']),
                 ('(2020, 2021)', ['2020', '2021']),
                 ('(2020-01, 2020-12-31)', ['2020-01', '2020-12-31']),
                 ('(2020-01-01, 2020-02-01)', ['2020-01-01', '2020-02-01'])]
        for time, expected in times:
            parsed_time = indexer.parse_time_parameter(asset=asset, time=time)
            self.assertEqual(parsed_time, expected)

if __name__ == '__main__':
    unittest.main()
