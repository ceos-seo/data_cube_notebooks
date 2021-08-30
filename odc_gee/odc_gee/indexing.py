# pylint: disable=no-member,broad-except,import-error,unused-argument
''' Indexes Google Earth Engine collections into Open Data Cube.

This module provides the necessary functions to index data into an ODC database.
It contains multiple helper methods and dataset document specifications for
different collections.
'''
from collections import namedtuple
from contextlib import redirect_stderr
from datetime import datetime
from re import sub
import io
import warnings

import numpy

from odc_gee import earthengine

IndexParams = namedtuple('IndexParams', 'asset product filters')

def add_dataset(doc, uri, index, sources_policy=None, update=None, **kwargs):
    ''' Add a dataset document to the index database.

    Args:
        doc: The dataset document.
        uri: Some URI to point to the document (this doesn't have to actually point anywhere).
        index: An instance of a datacube index.
        sources_policy (optional): The source policy to be checked.
        update: Update datasets if they already exist.
    Returns: The dataset to be indexed and any errors encountered.
    '''
    from datacube.index.hl import Doc2Dataset
    from datacube.utils import changes

    resolver = Doc2Dataset(index, **kwargs)
    dataset, err = resolver(doc, uri)
    buff = io.StringIO()
    if err is None:
        with redirect_stderr(buff):
            if update and index.datasets.get(dataset.id):
                index.datasets.update(dataset, {tuple(): changes.allow_any})
            else:
                index.datasets.add(dataset, sources_policy=sources_policy)
        val = buff.getvalue()
        if val.count('is already in the database'):
            def warning_without_trace(message, *args, **kwargs):
                return f'{message}'
            warnings.formatwarning = warning_without_trace
            warnings.warn(val)
    else:
        raise ValueError(err)
    return dataset

def make_metadata_doc(*args, **kwargs):
    """ Makes the dataset document from the parsed metadata.

    Args:
        asset (str): the asset ID of the product in the GEE catalog.
        image_data (dict): the image metadata to parse.
        product (datacube.model.DatasetType): the product information from the ODC index.
    Returns: a dictionary of the dataset document.
    """
    from odc_gee.parser import parse
    metadata = parse(*args, **kwargs)
    doc = {'id': metadata.id,
           '$schema': 'https://schemas.opendatacube.org/dataset',
           'product': {'name': metadata.product},
           'crs': 'EPSG:4326',
           'properties': {'odc:processing_datetime': metadata.creation_dt,
                          'odc:file_format': metadata.format,
                          'eo:platform': metadata.platform,
                          'eo:instrument': metadata.instrument,
                          'dtr:start_datetime': metadata.from_dt,
                          'dtr:end_datetime': metadata.to_dt,
                          'datetime': metadata.center_dt,
                          'gee:asset': metadata.asset},
           'geometry': metadata.geometry.json,
           'grids': {idx if idx else 'default': dict(shape=metadata.shapes[idx],
                                                     transform=metadata.transforms[idx])\
                     for (idx, grid) in enumerate(metadata.grids)},
           'measurements': {name: dict(grid=metadata.grids.index(band['grid']),
                                       path=metadata.path + band['id'])\
                                  if metadata.grids.index(band['grid']) else\
                                  dict(path=metadata.path + band['id'])
                            for (name, band) in metadata.bands},
           'location': metadata.path.rstrip(':'),
           'lineage': {'source_datasets': {}}}
    return doc

class Indexer:
    ''' Object for indexing GEE products into ODC.

    Attrs:
        datacube (odc_gee.earthengine.Datacube): An ODC wrapper for GEE specific uses.
    '''
    def __init__(self, app='GEE_Indexer', **kwargs):
        self.datacube = earthengine.Datacube(app=app, **kwargs)

    def __call__(self, *args, update=False, response=None, image_sum=0):
        """ Performs the parsing and indexing.

        Args:
            asset (str): the asset identifier to index.
            product (str): the product name to index.
            filters (dict): API filters to use when searching for datasets to index.
            datacube (odc_gee.earthengine.Datacube): Optional; an ODC instance.
            update (bool): will update existing datasets if set True.
            response: a Requests response from a previous API result.
            image_sum (int): the current sum of images indexed.
        Returns:
            A tuple of the Requests response from the API query
            and the recursive sum of datasets found.
        """
        index_params = IndexParams(*args)

        if index_params.product is None\
           or not self.datacube.list_products().name.isin([index_params.product]).any():
            raise ValueError("Missing product.")

        product = self.datacube.index.products.get_by_name(index_params.product)
        product_bands = list(product.measurements.keys())

        for image in self.datacube.get_images(index_params.filters):
            bands = [band['id'] for band in image['bands']]
            band_length = len(list(filter(lambda x: x in product_bands, bands)))
            if band_length == len(product.measurements):
                doc = make_metadata_doc(index_params.asset, image, product)
                add_dataset(doc, f'EEDAI:{image["name"]}',
                            self.datacube.index, products=[index_params.product], update=update)
            image_sum += 1
        return image_sum

    def generate_product(self, **kwargs):
        ''' Generates product definitions from supplied inputs.

        Args:
            datacube (odc_ge.earthengine.Datacube): The extended Earth Engine Datacube object.

        Returns: A datacube.model.DatasetType object.
        '''
        kwargs.update(resolution=(float(x) for x in sub(r'[\(\)\[\] ]', '',
                                                        kwargs['resolution']).split(','))
                      if isinstance(kwargs['resolution'], str) else kwargs.get('resolution'))
        if bool(kwargs['resolution']) ^ bool(kwargs['output_crs']):
            raise ValueError('Both resolution and output_crs must be supplied together.')
        product = self.datacube.generate_product(name=kwargs.get('product'), **kwargs)
        return self.datacube.index.products.add(product, allow_table_lock=True)

    def parse_time_parameter(self, **kwargs):
        ''' Parses the time parameter into a tuple of datetimes.

        Args:
            datacube (odc_gee.earthengine.Datacube): The extended Earth Engine Datacube object.

        Returns: A tuple of datetime.datetime objects.
        '''
        asset_info = self.datacube.ee.data.getAsset(kwargs['asset'])
        if kwargs.get('time'):
            time = (sub(r'[\(\)\[\] ]', '', kwargs['time']).split(','))\
                   if isinstance(kwargs['time'], str) else kwargs.get('time')
        else:
            if kwargs['rolling_update']:
                start_time = numpy.max(list(self.datacube.index.datasets.search_returning(
                    {'time'},
                    product=kwargs['product']))).lower.replace(tzinfo=None).isoformat()
                end_time = datetime.utcnow().isoformat()
            else:
                start_time, end_time = [numpy.datetime64(date, 'ms').item().isoformat()\
                                        for date in asset_info['properties']['date_range']]
            time = (start_time, end_time)
        return time
