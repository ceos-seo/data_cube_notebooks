from ipywidgets import widgets
from IPython.display import display, HTML

#Please refactor this
try:
    from mpl_toolkits.basemap import Basemap
except:
    print("'{0}' was not found in '{1}'.  It is likely that '{1}' is not present".format("Basemap", "mpl_toolkits.basemap"))
    pass
import matplotlib.pyplot as plt
import math # ceil

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
    

def create_platform_product_gui(platforms, products):
    """
    Description:
      
    -----
    """
    
    # Create widgets
    platform_sel = widgets.Dropdown(options=platforms, 
                                    values=platforms)
    product_sel = widgets.Dropdown(options=products,
                                   values=products)
    
    # Display form
    display(widgets.Label('Platform: '), platform_sel)
    display(widgets.Label('Product: '), product_sel)
    
    return [platform_sel, 
            product_sel]

def create_extents_gui(min_date, max_date, min_lon, max_lon, min_lat, max_lat):
    """
    Description:
      
    -----
    """
    
    # Create widgets 
    start_date_text = widgets.Text() 
    end_date_text = widgets.Text() 

    min_lon_text = widgets.BoundedFloatText(min=min_lon, 
                                            max=max_lon)
    max_lon_text = widgets.BoundedFloatText(min=min_lon, 
                                            max=max_lon, 
                                            value=min_lon_text.value + 1)
    min_lat_text = widgets.BoundedFloatText(min=min_lat, 
                                            max=max_lat)
    max_lat_text = widgets.BoundedFloatText(min=min_lat, 
                                            max=max_lat, 
                                            value=min_lat_text.value + 1)

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

try: 
    from mpl_toolkits.basemap import Basemap

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
        
except:
    print("Basemap is no longer in use. Please install or refactor.")
    pass