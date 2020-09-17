import numpy as np
from itertools import islice

nan = np.nan

def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def hex_to_rgb(rgbstr):
    rgbstr= rgbstr.replace('#','')
    hex_prefix = '0x'
    
    r = hex_prefix + rgbstr[:2]
    g = hex_prefix + rgbstr[2:4]
    b = hex_prefix + rgbstr[4:]
    
    return np.array([int(r, 16),
        int(g, 16),
        int(b, 16)])
   
def _bin_and_index(value, size):
    '''Takes two arguments. value and size. value is a float between 0 and 1, size is the number of bins into which
       we divide the range 0 and 1. An index is returned denoting which of these bins value falls into
    '''
    for i in range(size):
        if value > i/size and value <= (i + 1)/size:
            return i
    return 0

def get_gradient(colors, value):
    ''' make sure the value is between 0 and 1. If the value is between 0 and 1, you will get interpolated values in between.
        This displays gradients with quadruple digit precision
    '''
    
    if np.isnan(value):
        return np.array([nan,nan,nan])
    
    colors = [np.array(hex_to_rgb(color)) for color in colors]
    color_pairs = list(window(colors)) 
            
    size = len(color_pairs)
    index = _bin_and_index(value,size)
    color1,color2 = color_pairs[index]
    
    direction = (color2 - color1).astype(float)
    
    v = value * size - index
    return (v * direction) + color1 

