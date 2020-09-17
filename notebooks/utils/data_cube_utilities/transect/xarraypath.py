import numpy as np

def get_index_at(coords, ds):
    lat = coords[0]
    lon = coords[1]
    
    nearest_lat = ds.sel(latitude = lat, method = 'nearest').latitude.values
    nearest_lon = ds.sel(longitude = lon, method = 'nearest').longitude.values
    
    lat_index = np.where(ds.latitude.values == nearest_lat)[0]
    lon_index = np.where(ds.longitude.values == nearest_lon)[0]
    
    return (int(lat_index), int(lon_index))

def create_pixel_trail(start, end, ds):
    a = get_index_at(start, ds)
    b = get_index_at(end, ds)
    
    indices = line_scan(a, b)

    pixels = [ ds.isel(latitude = x, longitude = y) for x, y in indices]
    return pixels


