import numpy as np  
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
from datetime import datetime
import matplotlib.pyplot as plt
import time

def gauss(x, A, mu, sigma):
    '''Evaluates point on Gaussian Curve'''  
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def _n64_to_string(x):
    ''' Takes numpy 64 datetime object and returns a string with month-day information encoded in it'''  
    return time.strftime("%b %d", time.gmtime(x.astype(int)/1000000000))

def plot_fit(times,values, standard_deviations = 3):
    ''' Takes time series data(list of values and list of times), fits a gaussian curve to it, then displays both the line-gra'''

    x = range(len(times))
    y = values

    n = len(x)                       
    mean = sum(x*y)/n                 
    sigma = sum(y*(x-mean)**2)/n      

    popt,pcov = curve_fit(gauss,range(len(times)),values,p0=[1,mean,sigma])

    plt.plot(range(len(times)),values, label = 'data') 
    plt.plot(x,gauss(x,*popt),color = 'red',label='fit')

    margin = (standard_deviations* popt[2])
    
    plt.axvline(x=popt[1] - margin, color = 'green', linestyle='--')
    plt.axvline(x=popt[1] + margin, color = 'green', linestyle='--', label = str(standard_deviations) + '*std')
    
    plt.legend()
    plt.title('Fig. 3 - Fit for Time Constant')
    plt.xlabel('Time')
    
    _ticks = plt.xticks()[0]
    _ticks = [t for t in _ticks if t >= 0 and t <= len(times)]
    ticks = np.array(_ticks)
    
    plt.xticks(ticks,[_n64_to_string(times[int(i)]) for i in ticks])
    
    plt.ylabel('Precipitation')
    plt.show()

## Get Dates 
def get_bounds(times,values, standard_deviations = 1 ):
    "Takes time series data, returns time "
    x = range(len(times))
    y = values

    n = len(x)                       
    mean = sum(x*y)/n                 
    sigma = sum(y*(x-mean)**2)/n      

    stand = np.std(values)
    popt,pcov = curve_fit(gauss,range(len(times)),values,p0=[1,mean,sigma])

    
    start_index = int(popt[1] - (standard_deviations*popt[2]))
    end_index   = int(popt[1] + (standard_deviations*popt[2]))
    
    return times[start_index], times[end_index]
