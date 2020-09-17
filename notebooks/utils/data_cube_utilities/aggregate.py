import xarray as xr
import numpy as np

def get_bin_intervals(data, num_bins):
    """
    Returns bin intervals for 1D data.

    Parameters
    ----------
    data: np.ndarray
        A 1D NumPy array of values to get bin intervals for.
    num_bins: int
        The number of bins to create.

    Returns
    -------
    bin_intervals: np.ndarray of shape (num_bins, 2)
        A 2D NumPy array of bin intervals, with each row being one bin,
        with the first value being the lower bound for the bin and
        the second being the upper bound for the bin.
    """
    # Transition points between bins.
    bin_trans = np.linspace(data[0], data[-1], num_bins+1, endpoint=True)
    bin_intervals = np.empty((num_bins, 2), dtype=data.dtype)
    for i in range(num_bins):
        bin_intervals[i, :] = [bin_trans[i], bin_trans[i+1]]
    return bin_intervals


def xr_scale_res(dataset, x_coord='longitude', y_coord='latitude',
                 frac_res=None, abs_res=None):
    """
    Scales the resolution of an `xarray.Dataset` or `xarray.DataArray`
    to a fraction of its original resolution or an absolute resolution.

    Parameters
    ----------
    dataset: xarray.Dataset or xarray.DataArray
        The Dataset or DataArray to reduce the resolution of.
    x_coord, y_coord: str
        Names of the x and y coordinates in `dataset` to scale.
    frac_res: float
        The fraction of the original resolution to scale to. Must be postive.
        Note that this can be greater than 1.0, in which case the resolution
        is upsampled.
    abs_res: list-like
        A list-like of the number of pixels for the x and y axes, respectively.
        Overrides `frac_res` if specified.

    Returns
    -------
    dataset_scaled: xarray.Dataset or xarray.DataArray
        The result of scaling the resolution of `dataset`.

    Raises
    ------
    AssertionError: If neither `frac_res` nor `abs_res` is specified.
    """
    assert frac_res is not None or abs_res is not None, \
        "Either frac_res or abs_res must be specified (i.e. not None)."
    if frac_res is not None:
        x_px = y_px = np.sqrt(frac_res)
        interp_param = 'frac'
    elif abs_res is not None:
        interp_param = 'num'
        x_px, y_px = abs_res
    return xr_interp(dataset, {x_coord: ('interp', {interp_param: x_px}), \
                               y_coord: ('interp', {interp_param: y_px})})


def xr_sel_time_by_bin(dataset, num_bins, time_coord='time'):
    """
    Selects time coordinates by nearest neighbors of the means of bins.
    This is useful for plotting data with high variance in temporal
    spacing between acquisitions.

    Parameters
    ----------
    dataset: xarray.Dataset or xarray.DataArray
        The Dataset or DataArray to aggregate by binning.
        Must have a 'time' coordinate of type `datetime64`.
    num_bins: int
        The number of bins to use.
    time_coord: str
        The name of the time coordinate to bin.

    Returns
    -------
    result: xarray.Dataset or xarray.DataArray
        The result of aggregating within bins for the binned data.
    """
    return xr_interp(dataset, {time_coord: ('bin', {'num': num_bins})})


def xr_interp(dataset, interp_config):
    """
    Interpolates an `xarray.Dataset` or `xarray.DataArray`.
    This is often done to match dimensions between xarray objects or
    downsample to reduce memory consumption.

    First, coordinates are interpolated according to `interp_config`.
    Then the data values for those interpolated coordinates are obtained
    through nearest neighbors interpolation.

    Parameters
    ----------
    dataset: xarray.Dataset or xarray.DataArray
        The Dataset or DataArray to interpolate.
    interp_config: dict
        Mapping of names of coordinates to 2-tuples of the interpolation types
        to use for those coordinates and the parameters for those interpolation types.
        The supported coordinate interpolation types are 'interp' for
        linear interpolation and 'bin' for binning.
        The parameters, with supported interpolation types annotated to their
        left, are as follow:
        ('interp', 'bin'): 'frac':
            The fraction of the original size to use. Exclusive with 'num'.
        ('interp', 'bin'): 'num':
            The number of points in the output. Exclusive with 'frac'.
            Either 'frac' or 'num' must be in the interpolation parameters.
        The following is an example value:
        `{'latitude':('interp',{'frac':0.5}),'longitude':('interp',{'frac':0.5}),
          'time':('bin',{'num':20})}`.

    Returns
    -------
    interp_data: xarray.Dataset or xarray.DataArray
        The specified interpolation of `dataset`.

    :Authors:
        John Rattz (john.c.rattz@ama-inc.com)
    """
    from .dc_time import _n64_datetime_to_scalar, \
        _scalar_to_n64_datetime

    # Create the new coordinates.
    new_coords = {}
    for dim, (interp_type, interp_kwargs) in interp_config.items():
        # Determine the number of points to use.
        num_pts = interp_kwargs.get('num', None)
        if num_pts is None:
            frac = interp_kwargs.get('frac', None)
            num_pts_orig = len(dataset[dim])
            num_pts = int(round(num_pts_orig * frac))
        dim_vals = dataset[dim].values
        dim_dtype = type(dim_vals[0])
        # Convert NumPy datetime64 objects to scalars.
        if dim_dtype == np.datetime64:
            dim_vals = np.array(list(map(_n64_datetime_to_scalar, dim_vals)))
        interp_vals = None
        # Interpolate coordinates.
        if interp_type == 'bin':
            bin_intervals = get_bin_intervals(dim_vals, num_pts)
            interp_vals = np.mean(bin_intervals, axis=1)
        if interp_type == 'interp':
            interp_inds = np.linspace(0, len(dim_vals) - 1, num_pts, dtype=np.int32)
            interp_vals = dim_vals[interp_inds]
        # Convert scalars to NumPy datetime64 objects.
        if dim_dtype == np.datetime64:
            interp_vals = np.array(list(map(_scalar_to_n64_datetime, interp_vals)))
        new_coords[dim] = interp_vals
    # Nearest-neighbor interpolate data values.
    interp_data = dataset.interp(coords=new_coords, method='nearest')
    # xarray.Dataset.interp() converts to dtype float64, so cast back to the original dtypes.
    if isinstance(dataset, xr.DataArray):
        interp_data = interp_data.astype(dataset.dtype)
    elif isinstance(dataset, xr.Dataset):
        for data_var_name in interp_data.data_vars:
            interp_data[data_var_name] = interp_data[data_var_name].astype(dataset[data_var_name].dtype)
    return interp_data