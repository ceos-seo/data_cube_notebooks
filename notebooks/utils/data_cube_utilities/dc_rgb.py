import matplotlib.pyplot as plt
from time import time
import numpy as np


# Change the bands (RGB) here if you want other false color combinations
def rgb(dataset, time_index=0, x_coord='longitude', y_coord='latitude',
        bands=['red', 'green', 'blue'], paint_on_mask = [],
        min_inten=0.0, max_inten=1.0,
        width=10, fig=None, ax=None, imshow_kwargs=None, 
        percentiles=(5, 95)):
    """
    Creates a figure showing an area, using three specified bands as the rgb componenets.

    Parameters
    ----------
    dataset: xarray.Dataset
        A Dataset containing at least latitude and longitude coordinates and optionally time.
        The coordinate order should be time, latitude, and finally longitude.
        Must contain the data variables specified in the `bands` parameter.
    time_index:
        The time index to show data for if `dataset` is not 2D.
    x_coord, y_coord, time_coord: str
        Names of DataArrays in `dataset_in` to use as x, y, and time coordinates.
    bands: list-like
        A list-like containing 3 names of data variables in `dataset` to use as the red, green, and blue
        bands, respectively.
    paint_on_mask: tuple
        A 2-tuple of a boolean NumPy array (a "mask") and a list-like of 3 numeric values
        in the range [0, 255]. The array specifies where to "paint" over the RGB image with
        the RGB color specified by the second element.
    min_inten, max_inten: float
        The min and max intensities for any band. These can be in range [0,1].
        These can be used to brighten or darken the image.
    width: int
        The width of the figure in inches.
    fig: matplotlib.figure.Figure
        The figure to use for the plot.
        If only `fig` is supplied, the Axes object used will be the first.
    ax: matplotlib.axes.Axes
        The axes to use for the plot.
    imshow_kwargs: dict
        The dictionary of keyword arguments passed to `ax.imshow()`.
        You can pass a colormap here with the key 'cmap'.
    percentiles: list-like, default (5, 95)
        A 2-tuple of the lower and upper percentiles of the selected bands to set the min and max intensities
        to. The lower or upper values are overridden by `vmin` and `vmax` in `imshow_kwargs`.
        The range is [0, 100]. So `percentiles=(0,100)` would scale to the min and max of the selected bands.

    Returns
    -------
    fig, ax: matplotlib.figure.Figure, matplotlib.axes.Axes
        The figure and axes used for the plot.
    """
    from .plotter_utils import figure_ratio, \
        xarray_set_axes_labels, retrieve_or_create_fig_ax

    imshow_kwargs = {} if imshow_kwargs is None else imshow_kwargs
    vmin = imshow_kwargs.pop('vmin', None)
    vmax = imshow_kwargs.pop('vmax', None)

    ### < Dataset to RGB Format, needs float values between 0-1 
    rgb = np.stack([dataset[bands[0]],
                    dataset[bands[1]],
                    dataset[bands[2]]], axis = -1)
    # Interpolate values to be in the range [0,1] for creating the image.
    if vmin is None:
        vmin = np.nanpercentile(rgb, percentiles[0])
    if vmax is None:
        vmax = np.nanpercentile(rgb, percentiles[1])
    rgb = np.interp(rgb, (vmin, vmax), [min_inten,max_inten])
    rgb = rgb.astype(float)
    ### > 
    
    ### < takes a T/F mask, apply a color to T areas  
    for mask, color in paint_on_mask:        
        rgb[mask] = np.array(color)/ 255.0
    ### > 
    
    fig, ax = retrieve_or_create_fig_ax(fig, ax, figsize=figure_ratio(rgb.shape[:2], fixed_width = width))

    xarray_set_axes_labels(dataset, ax, x_coord, y_coord)
   
    if 'time' in dataset.dims:
        ax.imshow(rgb[time_index], **imshow_kwargs)
    else:
        ax.imshow(rgb, vmin=vmin, vmax=vmax, **imshow_kwargs)
    
    return fig, ax