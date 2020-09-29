import gc
import numpy as np
import xarray as xr
from xarray.ufuncs import sign as xr_sign

from . import dc_utilities as utilities
from .dc_utilities import create_default_clean_mask
from datetime import datetime
import warnings

def _tsmi(dataset):
    out = (dataset.red + dataset.green) * 0.0001 / 2
    return out.where(out>0, 0)

def tsm(dataset_in, clean_mask=None, no_data=0):
    """
    Inputs:
        dataset_in (xarray.Dataset)
            Dataset retrieved from the Data Cube.
            Must have 'red' and 'green' data variables.
    Optional Inputs:
        clean_mask (numpy.ndarray with dtype boolean)
            True for values considered clean;
            if no clean mask is supplied, all values will be considered clean
        no_data (int/float) - no data pixel value; default: -9999
    Throws:
        ValueError - if dataset_in is an empty xarray.Dataset.
    """
    assert 'red' in dataset_in and 'green' in dataset_in, "Red and Green bands are required for the TSM analysis."
    # Default to masking nothing.
    if clean_mask is None:
        clean_mask = create_default_clean_mask(dataset_in)

    tsm = 3983 * _tsmi(dataset_in)**1.6246
    tsm = tsm.where(clean_mask, no_data)

    # Create xarray of data
    _coords = { key:dataset_in[key] for key in dataset_in.dims.keys()}
    dataset_out = xr.Dataset({'tsm': tsm}, coords=_coords)
    return dataset_out


def mask_water_quality(dataset_in, wofs):
    import scipy.ndimage.filters as conv

    wofs_criteria = wofs.where(wofs > 0.8)
    wofs_criteria.values[wofs_criteria.values > 0] = 0
    kernel = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])

    mask = conv.convolve(wofs_criteria.values, kernel, mode='constant')
    mask = mask.astype(np.float32)

    dataset_out = dataset_in.copy(deep=True)
    for var in dataset_out.data_vars:
        dataset_out[var].values += mask
    dataset_out.where(dataset_out != np.nan, 0)

    return dataset_out


def watanabe_chlorophyll(dataset_in, clean_mask=None, no_data=0):
    assert 'red' in dataset_in and 'nir' in dataset_in, "Red and NIR bands are required for the Watanabe Chlorophyll analysis."
    # Default to masking nothing.
    if clean_mask is None:
        clean_mask = create_default_clean_mask(dataset_in)

    chl_a = 925.001 * (dataset_in.nir.astype('float64') / dataset_in.red.astype('float64')) - 77.16
    chl_a.values[np.invert(clean_mask)] = no_data  # Contains data for clear pixels

    # Create xarray of data
    time = dataset_in.time
    latitude = dataset_in.latitude
    longitude = dataset_in.longitude
    dataset_out = xr.Dataset(
        {
            'watanabe_chlorophyll': chl_a
        }, coords={'time': time,
                   'latitude': latitude,
                   'longitude': longitude})
    return dataset_out


def nazeer_chlorophyll(dataset_in, clean_mask=None, no_data=0):
    # Default to masking nothing.
    if clean_mask is None:
        clean_mask = create_default_clean_mask(dataset_in)

    chl_a = (0.57 * (dataset_in.red.astype('float64') * 0.0001) /
             (dataset_in.blue.astype('float64') * 0.0001)**2) - 2.61
    chl_a.values[np.invert(clean_mask)] = no_data  # Contains data for clear pixels

    # Create xarray of data
    time = dataset_in.time
    latitude = dataset_in.latitude
    longitude = dataset_in.longitude
    dataset_out = xr.Dataset(
        {
            'nazeer_chlorophyll': chl_a
        }, coords={'time': time,
                   'latitude': latitude,
                   'longitude': longitude})
    return dataset_out
