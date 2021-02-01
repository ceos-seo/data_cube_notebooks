import numpy as np
import xarray as xr

from .dc_utilities import get_range

## Utils ##

def xarray_values_in(data, values, data_vars=None):
    """
    Returns a mask for an xarray Dataset or DataArray, with `True` wherever the value is in values.

    Parameters
    ----------
    data: xarray.Dataset or xarray.DataArray
        The data to check for value matches.
    values: list-like
        The values to check for.
    data_vars: list-like
        The names of the data variables to check.

    Returns
    -------
    mask: np.ndarray
        A NumPy array shaped like ``data``. The mask can be used to mask ``data``.
        That is, ``data.where(mask)`` is an intended use.
    """
    data_vars_to_check = data_vars if data_vars is not None else list(data.data_vars.keys())
    if isinstance(data, xr.Dataset):
        mask = np.full_like(data[data_vars_to_check[0]].values, False, dtype=np.bool)
        for data_arr in data[data_vars_to_check].values():
            for value in values:
                mask = mask | (data_arr.values == value)
    elif isinstance(data, xr.DataArray):
        mask = np.full_like(data, False, dtype=np.bool)
        for value in values:
            mask = mask | (data.values == value)
    return mask

## End Utils ##

## Misc ##

def create_circular_mask(h, w, center=None, radius=None):
    """
    Creates a NumPy array mask with a circle.
    Credit goes to https://stackoverflow.com/a/44874588/5449970.

    Parameters
    ----------
    h, w: int
        The height and width of the data to mask, respectively.
    center: 2-tuple of int
        The center of the circle, specified as a 2-tuple of the x and y indices.
        By default, the center will be the center of the image.
    radius: numeric
        The radius of the circle.
        Be default, the radius will be the smallest distance between
        the center and the image walls.

    Returns
    -------
    mask: np.ndarray
        A boolean 2D NumPy array.
    """
    if center is None: # use the middle of the image
        center = [int(w/2), int(h/2)]
    if radius is None: # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w-center[0], h-center[1])

    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)

    mask = dist_from_center <= radius
    return mask

## End Misc ##

## Landsat ##

def landsat_clean_mask_invalid(dataset, platform, collection, level):
    """
    Masks out invalid data according to the LANDSAT
    surface reflectance specifications. See this document:
    https://landsat.usgs.gov/sites/default/files/documents/ledaps_product_guide.pdf pages 19-20.

    Parameters
    ----------
    dataset: xarray.Dataset
        An `xarray.Dataset` containing bands such as 'red', 'green', or 'blue'.
    platform: str
        A string denoting the platform to be used. Can be 
        "LANDSAT_5", "LANDSAT_7", or "LANDSAT_8".
    collection: string
        The Landsat collection of the data. 
        Can be any of ['c1', 'c2'] for Collection 1 or 2, respectively.
    level: string
        The processing level of the Landsat data. 
        Currently only 'l2' (Level 2) is supported.

    Returns
    -------
    invalid_mask: xarray.DataArray
        An `xarray.DataArray` with the same number and order of coordinates as in `dataset`.
        The `True` values specify what pixels are valid.
    """
    invalid_mask = None
    data_arr_names = [arr_name for arr_name in list(dataset.data_vars)
                      if arr_name not in ['pixel_qa', 'radsat_qa', 'cloud_qa']]
    rng = get_range(platform, collection, level)
    if rng is None:
        raise ValueError(
            f'The range is not recorded '\
            f'(platform: {platform}, collection: {collection}, level: {level}).')
    # Only keep data where all bands are in their valid ranges.
    for i, data_arr_name in enumerate(rng.keys()):
        rng_cur = rng[data_arr_name]
        invalid_mask_arr = (rng_cur[0] < dataset[data_arr_name]) & (dataset[data_arr_name] < rng_cur[1])
        invalid_mask = invalid_mask_arr if i == 0 else (invalid_mask & invalid_mask_arr)
    return invalid_mask


def landsat_qa_clean_mask(dataset, platform, cover_types=['clear', 'water'], 
                          collection=None, level=None):
    """
    Returns a clean_mask for `dataset` that masks out various types of terrain cover using the
    Landsat pixel_qa band. Note that Landsat masks specify what to keep, not what to remove.
    This means that using `cover_types=['clear', 'water']` should keep only clear land and water.

    See "pixel_qa band" here: https://landsat.usgs.gov/landsat-surface-reflectance-quality-assessment
    and Section 7 here: https://landsat.usgs.gov/sites/default/files/documents/lasrc_product_guide.pdf.

    Parameters
    ----------
    dataset: xarray.Dataset
        An xarray (usually produced by `datacube.load()`) that contains a `pixel_qa` data
        variable.
    platform: str
        A string denoting the platform to be used. Can be 
        "LANDSAT_5", "LANDSAT_7", or "LANDSAT_8".
    cover_types: list
        A list of the cover types to include. 
        Adding a cover type allows it to remain in the masked data.
        
        Here are a list of cover types, of which each combination of 
        satellite, collection, and level supports only some:
        'fill': Removes "no_data" values, which indicates an absense of data.
                This value is -9999 for Landsat platforms.
        'cloud': Allows only clouds, but note that it may only select cloud boundaries.
        'cld_shd': Allows only cloud shadows.
        'snow': Allows only snow.
        'clear': Allows only clear terrain. 
        'water': Allows only water. 
        'cld_conf_low':  Low cloud coverage confidence. Useful on its own for only removing clouds, 
                         however, 'clear' is usually better suited for this.
        'cld_conf_med':  Medium cloud coverage confidence. Useful in combination with 'low_conf_cl' 
                         to allow slightly heavier cloud coverage.
                         Note that 'med_conf_cl' and 'cloud' are very similar.
        'cld_conf_high': High cloud coverage confidence. Useful in combination with both 'low_conf_cl' 
                         and 'med_conf_cl'.
        'cld_shd_conf_low':  Low cloud shadow confidence.
        'cld_shd_conf_med':  Medium cloud shadow confidence.
        'cld_shd_conf_high': High cloud shadow confidence.
        'snw_ice_conf_low':  Low snow/ice confidence.
        'snw_ice_conf_high': High snow/ice confidence.
        'cir_conf_low':  Low cirrus confidence.
        'cir_conf_med':  Medium cirrus confidence.
        'cir_conf_high': High cirrus confidence.
        'terrain_occ': Allows only occluded terrain.
        'dilated_cloud': Allows dilated clouds.
        
        Cover types for Landsat 5 and 7 Collection 1 Level 2 include:
        ['fill', 'cloud', 'cld_shd', 'snow', 'clear', 'water', 'cld_conf_low', 'cld_conf_med', 
         'cld_conf_high'].

        Cover types for Landsat 8 Collection 1 Level 2 include: 
        ['fill', 'cloud', 'cld_shd', 'snow', 'clear', 'water', 'cld_conf_low', 'cld_conf_med',
         'cld_conf_high', 'cir_conf_low', 'cir_conf_med', 'cir_conf_high', 'terrain_occ']

        Cover types for Landsat 8 Collection 2 Level 2 include: 
        ['fill', 'cloud', 'cld_shd', 'snow', 'clear', 'water', 'cld_conf_low', 'cld_conf_med', 
         'cld_conf_high', 'cld_shd_conf_low', 'cld_shd_conf_high', 'snw_ice_conf_low', 
         'snw_ice_conf_high', 'cir_conf_low', 'cir_conf_high'].
        
    collection: string
        The Landsat collection of the data. 
        Can be any of ['c1', 'c2'] for Collection 1 or 2, respectively.
    level: string
        The processing level of the Landsat data. 
        Currently only 'l2' (Level 2) is supported.

    Returns
    -------
    clean_mask: xarray.DataArray
        An xarray DataArray with the same number and order of coordinates as in `dataset`.
    """
    def ls_unpack_qa(data_array, cover_type, platform, collection, level):
        # A map of 3-tuples of (platform, collection, level).
        # The `platform` value can be any of ['LANDSAT_5','LANDSAT_7','LANDSAT_8'].
        # The `collection` value can be any of ['c1', 'c2'].
        # The `level` value can be any of ['l1', 'l2'].
        landsat_qa_cover_types_map = {
            ('LANDSAT_5', 'c1', 'l2'): 
                dict(fill      = 1,   # 2**0 
                     clear     = 2,   # 2**1 
                     water     = 4,   # 2**2 
                     cld_shd   = 8,   # 2**3 
                     snow      = 16,  # 2**4 
                     cloud     = 32,  # 2**5 
                     low_conf  = 64,  # 2**6 
                     med_conf  = 128, # 2**7 
                     high_conf = 192  # 2**6 + 2**7
                    ),
            ('LANDSAT_7', 'c1', 'l2'): # Same as LS 5 C1 L2. 
                dict(fill      = 1, # 2**0 
                     clear     = 2, # 2**1 
                     water     = 4, # 2**2 
                     cld_shd   = 8, # 2**3 
                     snow      = 16, # 2**4 
                     cloud     = 32, # 2**5 
                     low_conf  = 64, # 2**6 
                     med_conf  = 128, # 2**7 
                     high_conf = 192 # 2**6 + 2**7 
                    ),
            ('LANDSAT_8', 'c1', 'l2'):
                dict(fill               = 1,   # 2**0
                     clear              = 2,   # 2**1
                     water              = 4,   # 2**2
                     cld_shd            = 8,   # 2**3
                     snow               = 16,  # 2**4
                     cloud              = 32,  # 2**5
                     cld_conf_low       = 64,  # 2**6
                     cld_conf_med       = 128, # 2**7
                     cld_conf_high      = 192, # 2**6 + 2**7
                     cir_conf_low       = 256, # 2**8
                     cir_conf_med       = 512, # 2**9
                     cir_conf_high      = 768, # 2**8 + 2**9
                     terrain_occ        = 1024 # 2**10
                    ),
            ('LANDSAT_8', 'c2', 'l2'):
                dict(fill               = 1,     # 2**0
                     dilated_cloud      = 2,     # 2**1
                     cirrus             = 4,     # 2**2
                     cloud              = 8,     # 2**3
                     cld_shd            = 16, # Should be same as cld_shd_conf_high.
                     snow               = 32,    # 2**5
                     clear              = 64,    # 2**6
                     water              = 128,   # 2**7
                     cld_conf_low       = 256,   # 2**8
                     cld_conf_med       = 512,   # 2**9
                     cld_conf_high      = 768,   # 2**8 + 2**9
                     cld_shd_conf_low   = 1024,  # 2**10
                     cld_shd_conf_high  = 3072,  # 2**10 + 2**11
                     snw_ice_conf_low   = 4096,  # 2**12
                     snw_ice_conf_high  = 12288, # 2**12 + 2**13
                     cir_conf_low       = 16384, # 2**14
                     cir_conf_high      = 49152  # 2**14 + 2**15
                    )
        }
        cover_type_encoding = landsat_qa_cover_types_map.get((platform, collection, level))
        if cover_type_encoding is None:
            raise ValueError('The platform, collection, level combination '\
                             f'{(platform, collection, level)} is not supported.\n'\
                             f'The supported combinations are: {list(landsat_qa_cover_types_map.keys())}')
        return (data_array & cover_type_encoding[cover_type]).astype(bool).rename(cover_type + "_mask")

    if collection is None:
        warnings.warn('Please specify a value for `collection`. Assuming data is collection 1.')
        collection = 'c1'
    assert collection in ['c1', 'c2'], "The `collection` parameter must be one of ['c1', 'c2']."
    
    if level is None:
        warnings.warn('Please specify a value for `level`. Assuming data is level 2.')
        level = 'l2'
    assert level in ['l2'], "The `level` parameter must be one of ['l2']."
    
    clean_mask = None
    # Keep all specified cover types (e.g. 'clear', 'water'), so logically or the separate masks.
    for i, cover_type in enumerate(cover_types):
        cover_type_clean_mask = ls_unpack_qa(dataset.pixel_qa, cover_type, 
                                             platform, collection, level)
        clean_mask = cover_type_clean_mask if i == 0 else (clean_mask | cover_type_clean_mask)
    return clean_mask

## End Landsat ##

## Sentinel 2 ##

def sentinel2_fmask_clean_mask(dataset, cover_types=['valid', 'water']):
    """
    Returns a clean_mask for `dataset` that masks out various types of terrain cover using the
    Sentinel 2 fmask band. Note that clean masks specify what to keep, not what to remove.
    This means that using `cover_types=['valid', 'water']` should keep only clear land and water.

    See "Classification Mask Generation" here:
    https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm

    Parameters
    ----------
    dataset: xarray.Dataset
        An xarray (usually produced by `datacube.load()`) that contains a `fmask` data
        variable.
    cover_types: list
        A list of the cover types to include. Adding a cover type allows it to remain in the masked data.
        Cover types for all Landsat platforms include:
        ['null', 'valid', 'cloud', 'cloud_shadow', 'snow', 'water'].

        'null' removes null values, which indicates an absense of data.
        'valid' allows clear views that are not cloud shadow, snow, or water.
        'cloud' allows clouds.
        'cloud_shadow' allows only cloud shadows.
        'snow' allows only snow.
        'water' allows only water.

        Here is a table of fmask values and their significances:
        Value Description
        0     Null
        1     Valid
        2     Cloud
        3     Cloud shadow
        4     Snow
        5     water

    Returns
    -------
    clean_mask: xarray.DataArray of boolean
        A boolean `xarray.DataArray` denoting which elements in `dataset` to keep -
        with the same number and order of coordinates as in `dataset`.
    """
    fmask_table = {'null': 0, 'valid': 1, 'cloud': 2, 'cloud_shadow': 3, 'snow': 4, 'water': 5}
    fmask_values_to_keep = [fmask_table[cover_type] for cover_type in cover_types]
    clean_mask = xarray_values_in(dataset.fmask, fmask_values_to_keep)
    return clean_mask

## End Sentinel 2 ##