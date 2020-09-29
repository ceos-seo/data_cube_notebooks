import time
import numpy as np
import xarray as xr

from . import dc_utilities
import datacube
import rasterio

## Export ##

def export_xarray_to_netcdf(data, path):
    """
    Exports an xarray object as a single NetCDF file.

    Parameters
    ----------
    data: xarray.Dataset or xarray.DataArray
        The Dataset or DataArray to export.
    path: str
        The path to store the exported NetCDF file at.
        Must include the filename and ".nc" extension.
    """
    # Record original attributes to restore after export.
    orig_data_attrs = data.attrs.copy()
    orig_data_var_attrs = {}
    if isinstance(data, xr.Dataset):
        for data_var in data.data_vars:
            orig_data_var_attrs[data_var] = data[data_var].attrs.copy()

    # If present, convert the CRS object from the Data Cube to a string.
    # String and numeric attributes are retained.
    # All other attributes are removed.
    def handle_attr(data, attr):
        if attr == 'crs' and not isinstance(data.attrs[attr], str):
            data.attrs[attr] = data.crs.crs_str
        elif not isinstance(data.attrs[attr], (str, int, float)):
            del data.attrs[attr]

    # To be able to call `xarray.Dataset.to_netcdf()`, convert the CRS
    # object from the Data Cube to a string, retain string and numeric
    # attributes, and remove all other attributes.
    for attr in data.attrs:
        handle_attr(data, attr)
    if isinstance(data, xr.Dataset):
        for data_var in data.data_vars:
            for attr in list(data[data_var].attrs):
                handle_attr(data[data_var], attr)
    # Move units from the time coord attributes to its encoding.
    if 'time' in data.coords:
        orig_time_attrs = data.time.attrs.copy()
        if 'units' in data.time.attrs:
            time_units = data.time.attrs['units']
            del data.time.attrs['units']
            data.time.encoding['units'] = time_units
    # Export to NetCDF.
    data.to_netcdf(path)
    # Restore original attributes.
    data.attrs = orig_data_attrs
    if 'time' in data.coords:
        data.time.attrs = orig_time_attrs
    if isinstance(data, xr.Dataset):
        for data_var in data.data_vars:
            data[data_var].attrs = orig_data_var_attrs[data_var]

def export_slice_to_geotiff(ds, path, x_coord='longitude', y_coord='latitude'):
    """
    Exports a single slice of an xarray.Dataset as a GeoTIFF.

    ds: xarray.Dataset
        The Dataset to export. Must have exactly 2 dimensions - 'latitude' and 'longitude'.
    x_coord, y_coord: string
        Names of the x and y coordinates in `ds`.
    path: str
        The path to store the exported GeoTIFF.
    """
    kwargs = dict(tif_path=path, data=ds.astype(np.float32), bands=list(ds.data_vars.keys()),
                  x_coord=x_coord, y_coord=y_coord)
    if 'crs' in ds.attrs:
        kwargs['crs'] = str(ds.attrs['crs'])
    dc_utilities.write_geotiff_from_xr(**kwargs)


def export_xarray_to_multiple_geotiffs(ds, path, x_coord='longitude', y_coord='latitude'):
    """
    Exports an xarray.Dataset as individual time slices - one GeoTIFF per time slice.

    Parameters
    ----------
    ds: xarray.Dataset
        The Dataset to export. Must have exactly 3 dimensions - 'latitude', 'longitude', and 'time'.
        The 'time' dimension must have type `numpy.datetime64`.
    path: str
        The path prefix to store the exported GeoTIFFs. For example, 'geotiffs/mydata' would result in files named like
        'mydata_2016_12_05_12_31_36.tif' within the 'geotiffs' folder.
    x_coord, y_coord: string
        Names of the x and y coordinates in `ds`.
    """
    def time_to_string(t):
        return time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime(t.astype(int) / 1000000000))

    for t_ind, t in enumerate(ds.time):
        time_slice_xarray = ds.isel(time=t_ind)
        export_slice_to_geotiff(time_slice_xarray,
                                path + "_" + time_to_string(t) + ".tif",
                                x_coord=x_coord, y_coord=y_coord)


def export_xarray_to_geotiff(data, tif_path, bands=None, no_data=-9999, crs="EPSG:4326",
                             x_coord='longitude', y_coord='latitude'):
    """
    Export a GeoTIFF from a 2D `xarray.Dataset`.

    Parameters
    ----------
    data: xarray.Dataset or xarray.DataArray
        An xarray with 2 dimensions to be exported as a GeoTIFF.
        If the dtype is `bool`, convert to dtype `numpy.uint8`.
    tif_path: string
        The path to write the GeoTIFF file to. You should include the file extension.
    bands: list of string
        The bands to write - in the order they should be written.
        Ignored if `data` is an `xarray.DataArray`.
    no_data: int
        The nodata value.
    crs: string
        The CRS of the output.
    x_coord, y_coord: string
        The string names of the x and y dimensions.
    """
    from .dc_utilities import _get_transform_from_xr

    if isinstance(data, xr.DataArray):
        height, width = data.sizes[y_coord], data.sizes[x_coord]
        count, dtype = 1, data.dtype
    else:
        if bands is None:
            bands = list(data.data_vars.keys())
        else:
            assrt_msg_begin = "The `data` parameter is an `xarray.Dataset`. "
            assert isinstance(bands, list), assrt_msg_begin + "Bands must be a list of strings."
            assert len(bands) > 0 and isinstance(bands[0], str), assrt_msg_begin + "You must supply at least one band."
        height, width = data.dims[y_coord], data.dims[x_coord]
        count, dtype = len(bands), data[bands[0]].dtype
    with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=count,
            dtype=dtype,
            crs=crs,
            transform=_get_transform_from_xr(data, x_coord=x_coord, y_coord=y_coord),
            nodata=no_data) as dst:
        if isinstance(data, xr.DataArray):
            dst.write(data.values, 1)
        else:
            for index, band in enumerate(bands):
                dst.write(data[band].values.astype(dtype), index + 1)
    dst.close()

## End export ##