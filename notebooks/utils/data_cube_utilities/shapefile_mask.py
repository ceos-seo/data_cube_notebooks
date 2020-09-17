import fiona
import xarray as xr
import numpy as np

from rasterio.features import geometry_mask
import shapely
from shapely.ops import transform
from shapely.geometry import shape
from functools import partial

def get_y_x_bounds_shapefile(shapefile):
    """
    Returns the y/x bounds of a shapefile.

    Parameters
    ----------
    shapefile: string
        The shapefile to be used.

    Returns
    -------
    y, x: list
        The y and x bounds of the shapefile.
    """
    with fiona.open(shapefile, 'r') as src:
        # create a shapely geometry
        # this is done for the convenience for the .bounds property only
        shp_geom = shape(src[0]['geometry'])

        # get the bounding box of the shapefile geometry
        y, x = [[None] * 2, [None] * 2]
        x[0], y[0] = shp_geom.bounds[0:2]
        x[1], y[1] = shp_geom.bounds[2:4]
        return y, x

def shapefile_mask(dataset: xr.Dataset, shapefile) -> np.array:
    """
    Extracts a mask from a shapefile using dataset latitude and longitude extents.

    Args:
        dataset (xarray.Dataset): The dataset with latitude and longitude extents.
        shapefile (string): The shapefile to be used.

    Returns:
        A boolean mask array.
    """
    import pyproj

    with fiona.open(shapefile, 'r') as src:
        collection = list(src)
        geometries = []
        for feature in collection:
            geom = shape(feature['geometry'])
            project = partial(
                pyproj.transform,
                pyproj.Proj(init=src.crs['init']), # source crs
                pyproj.Proj(init='epsg:4326')) # destination crs
            geom = transform(project, geom)  # apply projection
            geometries.append(geom)
        geobox = dataset.geobox
        mask = geometry_mask(
            geometries,
            out_shape=geobox.shape,
            transform=geobox.affine,
            all_touched=True,
            invert=True)
    return mask