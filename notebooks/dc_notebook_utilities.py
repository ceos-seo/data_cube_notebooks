from ipywidgets import widgets
from IPython.display import display, HTML
from typing import List

from matplotlib.colors import LinearSegmentedColormap
import math # ceil

import datacube


def create_acq_date_gui(acq_dates):
    """
    Description:
      
    -----
    """
    
    # Create widget
    acq_date_sel = widgets.Dropdown(options=acq_dates,
                                    values=acq_dates)
    
    # Display form
    display(widgets.Label('Acquisition Date: '), acq_date_sel)
    
    return acq_date_sel
    

    
def create_platform_product_gui(platforms: List[str],
                                products:  List[str],
                                datacube:  datacube.Datacube,
                                default_platform:str = None,
                                default_product:str  = None,):
    """
    Description:
      
    -----
    """
    plat_selected = [None]
    prod_selected = [None]
    
    def parse_widget(x):
        var = datacube.list_products()
        return var["name"][(var["platform"] == x) & (var["name"].isin(products))]
    
    def get_keys(platform):
        products = [x for x in parse_widget(platform)]
        product = default_product if default_product in products else products[0]
        product_widget = widgets.Select(options=products, value=product)
        product_field = widgets.interactive(get_product, prod=product_widget, continuous_update=True)
        display(product_field)
        plat_selected[0] = (platform)
        return platform
    
    def get_product(prod):
            prod_selected[0] = (prod)
            return prod
    
    platform = default_platform if default_platform in platforms else platforms[0]
    platform_widget = widgets.Select(options=platforms, value=platform)
    platform_field = widgets.interactive(get_keys, platform=platform_widget, continuous_update=True)
    display(platform_field)
    return [plat_selected, prod_selected]

        
        
def create_extents_gui(min_date, max_date, min_lon, max_lon, min_lat, max_lat):
    """
    Description:
      
    -----
    """
    
    # Create widgets 
    start_date_text = widgets.Text(min_date) 
    end_date_text = widgets.Text(max_date) 

    min_lon_text = widgets.BoundedFloatText(min=min_lon, 
                                            max=max_lon,
                                            value=min_lon)
    max_lon_text = widgets.BoundedFloatText(min=min_lon, 
                                            max=max_lon, 
                                            value=max_lon)
    min_lat_text = widgets.BoundedFloatText(min=min_lat, 
                                            max=max_lat,
                                            value=min_lat)
    max_lat_text = widgets.BoundedFloatText(min=min_lat, 
                                            max=max_lat, 
                                            value=max_lat)

    # Display form
    display(widgets.Label('Start date: '), start_date_text)
    display(widgets.Label('End date: '), end_date_text)

    display(widgets.Label('Min lon: '), min_lon_text)
    display(widgets.Label('Max lon: '), max_lon_text)
    display(widgets.Label('Min lat: '), min_lat_text)
    display(widgets.Label('Max lat: '), max_lat_text)
    
    return [start_date_text, 
            end_date_text,
            min_lon_text, 
            max_lon_text,
            min_lat_text, 
            max_lat_text]

def generate_metadata_report(min_date, max_date, min_lon, max_lon, lon_dist, min_lat, max_lat, lat_dist):
    metadata_report = ( '<table><tr><th></th><th>Min</th><th>Max</th><th>Resolution</th></tr>'
                      + '<tr><th>Date: </th>'
                      + '<td>' + min_date + '</td><td>' + max_date + '</td><td></td></tr>'
                      + '<tr><th>Longitude: </th>'
                      + '<td>' + str(min_lon) + '</td>'
                      + '<td>' + str(max_lon) + '</td>'
                      + '<td>' + str(lon_dist) + '</td></tr>'
                      + '<tr><th>Latitude: </th>'
                      + '<td>' + str(min_lat) + '</td>'
                      + '<td>' + str(max_lat) + '</td>'
                      + '<td>' + str(lat_dist) + '</td></tr></table>' )

    display(HTML('<h2>Metadata Report: </h2>'))
    display(HTML(metadata_report))



def show_map_extents(min_lon, max_lon, min_lat, max_lat):
    extents=(
        min_lat,
        min_lon,
        max_lat,
        max_lon,
    )

    margin = max( math.ceil(extents[3]-extents[1]), math.ceil(extents[2]-extents[0]) )+0.5
    center = ( (extents[2]-extents[0])/2.0+extents[0], (extents[3]-extents[1])/2.0+extents[1] )


    map = Basemap(
        llcrnrlon=extents[1]-margin,
        llcrnrlat=extents[0]-margin,
        urcrnrlon=extents[3]+margin,
        urcrnrlat=extents[2]+margin,
        resolution='i',
        projection='tmerc',
        lat_0 = center[0],
        lon_0 = center[1],
    )

    map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(color='coral',lake_color='aqua')
    map.drawcoastlines()
    map.drawstates()
    map.drawcountries()
    # eh... just draw the whole globe's worth of lines
    map.drawparallels(range( -90,  90, 1))
    map.drawmeridians(range(-180, 180, 1))

    # Draw region of interest
    #map.plot((34,34,37,37,34),(-1,1,1,-1,-1),latlon=True, linewidth=2, color='yellow')
    map.plot(( # Lat
            extents[1],
            extents[1],
            extents[3],
            extents[3],
            extents[1]
        ),( # Lon
            extents[0],
            extents[2],
            extents[2],
            extents[0],
            extents[0]
        ),latlon=True, linewidth=2, color='yellow')

    # Add some annotation
    x, y = map(center[1], extents[2])
    plt.text(x, y, 'Region of\nInterest',fontsize=13,fontweight='bold',ha='center',va='bottom',color='k')

    # map.nightshade(datetime.now(), delta=0.2) # Draw day/night areas

    plt.show()


import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from time import time
import numpy as np


# Change the bands (RGB) here if you want other false color combinations
def rgb(dataset,
        at_index = 0,
        bands = ['red', 'green', 'blue'],
        paint_on_mask = [],
        max_possible = 3500,
        width = 10,
        figsize=None
       ):

    def aspect_ratio_helper(x,y, fixed_width = 20):
        width = fixed_width
        height = y * (fixed_width / x)
        return (width, height)
    
    ### < Dataset to RGB Format, needs float values between 0-1 
    rgb = np.stack([dataset[bands[0]],
                    dataset[bands[1]],
                    dataset[bands[2]]], axis = -1).astype(np.int16)
    
    rgb[rgb<0] = 0    
    rgb[rgb > max_possible] = max_possible # Filter out saturation points at arbitrarily defined max_possible value
    
    rgb = rgb.astype(float)
    rgb *= 1 / np.max(rgb)
    ### > 
    
    ### < takes a T/F mask, apply a color to T areas  
    for mask, color in paint_on_mask:        
        rgb[mask] = np.array(color)/ 255.0
    ### > 
    
    if figsize is None:
        figsize = aspect_ratio_helper(*rgb.shape[:2], fixed_width = width)
    fig, ax = plt.subplots(figsize = figsize)

    lat_formatter = FuncFormatter(lambda x, pos: round(dataset.latitude.values[pos] ,4) )
    lon_formatter = FuncFormatter(lambda x, pos: round(dataset.longitude.values[pos],4) )

    plt.ylabel("Latitude")
    ax.yaxis.set_major_formatter(lat_formatter)
    plt.xlabel("Longitude")
    ax.xaxis.set_major_formatter(lon_formatter)
   
    if 'time' in dataset:
        plt.imshow((rgb[at_index]))
    else:
        plt.imshow(rgb)  
    
    plt.show()
    
def create_discrete_color_map(data_range, th, colors, cmap_name='my_cmap'):
    """
    Creates a discrete matplotlib LinearSegmentedColormap with thresholds for color changes.
    
    Parameters
    ----------
    data_range: list-like
        A 2-tuple of the minimum and maximum values the data may take.
    th: list
        Threshold values. Must be in the range of `data_range` - noninclusive.
    colors: list
        Colors to use between thresholds, so `len(colors) == len(th)+1`.
        Colors can be string names of matplotlib colors or 3-tuples of rgb values in range [0,255].
    cmap_name: str
        The name of the colormap for matplotlib.
    """
    import matplotlib as mpl
    # Normalize threshold values based on the data range.
    th = list(map(lambda val: (val - data_range[0])/(data_range[1] - data_range[0]), th))
    # Normalize color values.
    for i, color in enumerate(colors):
        if isinstance(color, tuple):
            colors[i] = [rgb/255 for rgb in color]
    th = [0.0] + th + [1.0]
    cdict = {}
    # These are fully-saturated red, green, and blue - not the matplotlib colors for 'red', 'green', and 'blue'.
    primary_colors = ['red', 'green', 'blue']
    # Get the 3-tuples of rgb values for the colors.
    color_rgbs = [(mpl.colors.to_rgb(color) if isinstance(color,str) else color) for color in colors]
    # For each color entry to go into the color dictionary...
    for primary_color_ind, primary_color in enumerate(primary_colors):
        cdict_entry = [None]*len(th)
        # For each threshold (as well as 0.0 and 1.0), specify the values for this primary color.
        for row_ind, th_ind in enumerate(range(len(th))):
            # Get the two colors that this threshold corresponds to.
            th_color_inds = [0,0] if th_ind==0 else \
                            [len(colors)-1, len(colors)-1] if th_ind==len(th)-1 else \
                            [th_ind-1, th_ind]
            primary_color_vals = [color_rgbs[th_color_ind][primary_color_ind] for th_color_ind in th_color_inds]
            cdict_entry[row_ind] = (th[th_ind],) + tuple(primary_color_vals)
        cdict[primary_color] = cdict_entry
    cmap = LinearSegmentedColormap(cmap_name, cdict)
    return cmap

