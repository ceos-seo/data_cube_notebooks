import numpy as np

def _reformat(xs, ys):
    '''Zips a list of xs and a list of ys. Converts to np.array. Casts to int'''
    return np.array(list(zip(xs, ys))).astype(int)

def line_scan(c1, c2):
    '''
    Accepts two integer coordinate pairs, c1 and c2.  
    Returns a list of integer coordinate pairs representing all points on the line drawn between c1 and c2.  
    '''
    
    c1 = np.array(c1)
    c2 = np.array(c2)
    x_direction = int( 2 * (int(c1[0] < c2[0]) - .5))
    y_direction = int( 2 * (int(c1[1] < c2[1]) - .5))

    if c1[0] == c2[0]:
        range_of_ys = list(range(c1[1], c2[1] + 1, y_direction))
        range_of_xs = [c1[0] for x in range_of_ys]
        return _reformat(range_of_xs, range_of_ys)
    
    if c1[1] == c2[1]:
        range_of_xs = list(range(c1[0], c2[0] + 1, x_direction))
        range_of_ys = [c1[1] for x in range_of_xs]
        return _reformat(range_of_xs, range_of_ys)

    dy = c2[1] - c1[1]
    dx = c2[0] - c1[0]

    m = dy/dx
    _y = c1[1]
    _x = c1[0]
    
    sign = 1 if m > 0 else -1
    
    if abs(m) >= 1:
        
        range_of_ys = list(range(c1[1], c2[1] + sign, sign*x_direction))
        range_of_xs =  [ (((y-_y)/m) + _x)//1 for y in range_of_ys]
        return _reformat(range_of_xs, range_of_ys)
        
    elif abs(m) < 1:
        
        range_of_xs = list(range(c1[0], c2[0] + 1, x_direction))
        range_of_ys =  [ (m * (x-_x))//1 + _y  for x in range_of_xs]        
        
        return _reformat(range_of_xs, range_of_ys)