import numpy as np

## requires pytest

import sys

sys.path.append('../')
from line_scan import line_scan
equal = np.testing.assert_array_equal

'''
I line can go from....

    lr - left to right
    rl = right to left

    ud - up to down
    du - down to up

    mg - slope greater than 1
    ml - slope less than one
    me - slope equal to one

Or it can be a completely...  

    h, horizontal 
    v, vertical 

The following tests account for all possible combinations of orientation and slope. 
'''

############## lr_ud
def test_lr_ud_mg():
    a, b = [np.array([1, 10]), np.array([4, 2])]
    expected_answer = [[1, 10], [1, 9], [1, 8], [2, 7], [2, 6], [2, 5], [3, 4], [3, 3], [4, 2]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_lr_ud_ml():
    a, b = np.array([1, 10]), np.array([10, 5])
    expected_answer = [[1, 10], [2, 9], [3, 8], [4, 8], [5, 7], [6, 7], [7, 6], [8, 6], [9, 5], [10, 5]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_lr_ud_me():
    a, b = np.array([1, 10]), np.array([10, 1])
    expected_answer = [[1, 10], [2, 9], [3, 8], [4, 7], [5, 6], [6, 5], [7, 4], [8, 3], [9, 2], [10, 1]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


############## lr_du
def test_lr_du_mg():
    a, b = [np.array([1, 2]), np.array([4, 10])]
    expected_answer = [[1, 2], [1, 3], [1, 4], [2, 5], [2, 6], [2, 7], [3, 8], [3, 9], [4, 10]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_lr_du_ml():
    a, b = [np.array([1, 5]), np.array([10, 10])]
    expected_answer = [[1, 5], [2, 5], [3, 6], [4, 6], [5, 7], [6, 7], [7, 8], [8, 8], [9, 9], [10, 10]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_lr_du_me():
    a, b = [np.array([1, 1]), np.array([10, 10])]
    expected_answer = [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


############## rl_ud
def test_rl_ud_mg():
    a, b = [np.array([4, 10]), np.array([1, 2])]
    expected_answer = [[4, 10], [3, 9], [3, 8], [2, 7], [2, 6], [2, 5], [1, 4]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_rl_ud_ml():
    a, b = [np.array([8, 10]), np.array([1, 5])]
    expected_answer = [[8, 10], [7, 9], [6, 8], [5, 7], [4, 7], [3, 6]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_rl_ud_me():
    a, b = [np.array([8, 10]), np.array([4, 5])]
    expected_answer = [[8, 10], [7, 9], [6, 8], [5, 7]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


############## rl_du
def test_rl_du_mg():
    a, b = [np.array([4, 2]), np.array([1, 10])]
    expected_answer = [[4, 2], [3, 3], [3, 4], [2, 5], [2, 6], [2, 7], [1, 8]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_rl_du_ml():  #-0.444444444444
    a, b = [np.array([10, 2]), np.array([1, 6])]
    expected_answer = [[10, 2], [9, 2], [8, 2], [7, 3], [6, 3], [5, 4], [4, 4], [3, 5]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_rl_du_me():
    a, b = [np.array([11, 5]), np.array([1, 15])]
    expected_answer = [[11, 5], [10, 6], [9, 7], [8, 8], [7, 9], [6, 10], [5, 11], [4, 12], [3, 13]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


############### h


def test_rl_h():
    a, b = [np.array([10, 4]), np.array([2, 4])]
    expected_answer = [[10, 4], [9, 4], [8, 4], [7, 4], [6, 4], [5, 4], [4, 4]]
    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_lr_h():
    a, b = [np.array([2, 4]), np.array([10, 4])]
    expected_answer = [[2, 4], [3, 4], [4, 4], [5, 4], [6, 4], [7, 4], [8, 4], [9, 4], [10, 4]]

    equal(np.array(line_scan(a, b)), np.array(expected_answer))


############### v
def test_v_du():
    a, b = [np.array([10, 2]), np.array([10, 8])]
    expected_answer = [[10, 2], [10, 3], [10, 4], [10, 5], [10, 6], [10, 7], [10, 8]]
    equal(np.array(line_scan(a, b)), np.array(expected_answer))


def test_v_ud():
    a, b = [np.array([10, 10]), np.array([10, 2])]
    expected_answer = [[10, 10], [10, 9], [10, 8], [10, 7], [10, 6], [10, 5], [10, 4]]
    equal(np.array(line_scan(a, b)), np.array(expected_answer))
    
    
################################################################################

points = {}
points['lrudmg'] = [np.array([1,10]), np.array([4,2])]
points['lrudml'] = [np.array([1,10]), np.array([10,5])]
points['lrudme'] = [np.array([1,10]), np.array([10,1])]

points['lrdumg'] = [np.array([1,2]), np.array([4,10])]
points['lrduml'] = [np.array([1,5]), np.array([10,10])]
points['lrdume'] = [np.array([1,1]), np.array([10,10])]


points['rludmg'] = [ np.array([4,10]), np.array([1,2])]
points['rludml'] = [ np.array([8,10]), np.array([1,5])]
points['rludme'] = [np.array([8,10]), np.array([4,5])]

points['rldumg'] = [ np.array([4,2]), np.array([1,10])]
points['rlduml'] = [ np.array([10,2]), np.array([1,6])]
points['rldume'] = [np.array([11,5]), np.array([1,15])]


points['h_lr'] = [np.array([2,4]), np.array([10,4])]
points['h_rl'] = [np.array([10,4]), np.array([2,4])]

points['v_du'] = [np.array([10,2]), np.array([10,8])]
points['v_ud'] = [np.array([10,10]), np.array([10,2])]

