from ipywidgets import widgets
from IPython.display import display, HTML
from typing import List
import numpy as np

#Please refactor this
try:
    from mpl_toolkits.basemap import Basemap
except:
    print("'{0}' was not found in '{1}'.  It is likely that '{1}' is not present".format("Basemap", "mpl_toolkits.basemap"))
    pass
import matplotlib.pyplot as plt
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
        return var["name"][var["platform"] == x]
    
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
       
    ##old code:
    # Create widgets
#     platform_sel = widgets.Dropdown(options=platforms, 
#                                     values=platforms)
#     print(type(platform_sel))
#     # Display form
#     display(widgets.Label('Platform: '), platform_sel)
    
#     val = platform_sel.value
#     products = [k for k in products if parse_widget(val) in k]
# #     print(products)
    
#     product_sel = widgets.Dropdown(options=products,
#                                    values=products)
#     display(widgets.Label('Product: '), product_sel)
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


def rgb(dataset, at_index = 0, bands = ['red', 'green', 'blue'], paint_on_mask = []):
    rgb = np.stack([dataset[bands[0]], dataset[bands[1]], dataset[bands[2]]], axis = -1)
    max_possible = 3500
    rgb = rgb.astype(np.float32)
    rgb[rgb<0] = 0
    rgb[rgb > max_possible] = max_possible
    rgb *= 255.0/rgb.max()

    rgb = rgb.astype(int)
    rgb = rgb.astype(np.float32)
    rgb = 255-rgb
    
    rgb[rgb > 254] = 254
    rgb[rgb < 1]   = 1
    
    
    for mask, color in paint_on_mask:        
        rgb[mask] = np.array([256,256,256]) - np.array(color).astype(np.int16)
    
    if 'time' in dataset:
        plt.imshow((rgb[at_index]))
    else:
        plt.imshow(rgb)


