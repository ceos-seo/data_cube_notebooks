import numpy as np

import sys
sys.path.append('../')

from interpolate import get_gradient, _bin_and_index

three_colors = ['#ffffff', '#000000', '#ff0000']
two_colors = ['#ffffff', '#000000']


equal = np.testing.assert_array_equal
close_enough = np.testing.assert_allclose

def test_bin_lower():
    value = 0.3
    size = 2
    params = (value, size) 
    expected_answer = 0
    equal(expected_answer, _bin_and_index(*params)) 
    
def test_bin_higher():
    value = 0.9
    size = 2
    params = (value, size) 
    expected_answer = 1
    equal(expected_answer, _bin_and_index(*params)) 

## test_<number of colors>_<value intensity between 0 and 1>
def test_3_half():
    value = 0.5
    params = (three_colors, value)
    expected_answer = np.array([0, 0, 0])
        
    close_enough( expected_answer, get_gradient(*params),atol =  1 )
    
def test_3_quarter():
    value = 0.25
    params = (three_colors, value)
    expected_answer = np.array([127.5, 127.5, 127.5])
        
    close_enough( expected_answer, get_gradient(*params),atol =  1 )    

def test_3_3quarter():
    value = 0.75
    params = (three_colors, value)
    expected_answer = np.array([127.5, 0, 0])
        
    close_enough( expected_answer, get_gradient(*params),atol =  1 )    
    
    
def test_2_half():
    value = 0.5
    params = (two_colors, value)
    expected_answer = np.array([127.5, 127.5, 127.5])
    close_enough( expected_answer, get_gradient(*params),atol =  1 )

def test_2_quarter():
    value = 0.25
    params = (two_colors, value)
    expected_answer = np.array([191.25,191.25,191.25])
    close_enough( expected_answer, get_gradient(*params),atol =  1 )
    
def test_2_3quarter():
    value = 0.75
    params = (two_colors, value)
    expected_answer = np.array([63.75,63.75,63.75])
    close_enough( expected_answer, get_gradient(*params),atol =  1 )
    