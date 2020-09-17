# Author: AC
# Creation date: 2016-07-29
# Modified by:
# Last modified date: 

# Utility file - adds some colormaps to matplotlib's built-in collection.  Currently, they include:
# - Australian
#  - dc_au_ClearObservations
#  - dc_au_WaterObservations
#  - dc_au_Confidence
#  - dc_au_WaterSummary

import matplotlib
import matplotlib.colors

def htmlColorMap(html,step=False,name='customColorMap'):
    """Return a dictionary suitable for passing to matplotlib.colors.LinearSegmentedColormap
    html: a sequence of numbers and HTML style (hex string) colors. The numbers will be normalized.
    step: indicates whether the map should be smooth (False, default) or have hard steps (True).
    name: a name for the custom gradient.  Defaults to 'customColorMap'.
    """
    stops = html[::2]
    cols = html[1::2]
    stop_min = float(min(stops))
    stop_max = float(max(stops))
    cdict = {'red':[], 'green':[], 'blue':[]}

    stops = [(float(s)-stop_min)/(stop_max-stop_min) for s in stops] # Normalize
    cols = [matplotlib.colors.hex2color(c) for c in cols] # Convert html to (r,g,b)
    
    # Smooth gradient
    if (step==False):
        for i, item in enumerate(stops):
            r, g, b = cols[i]
            cdict['red'].append([item,r,r])
            cdict['green'].append([item,g,g])
            cdict['blue'].append([item,b,b])
    else:
    # Solid bands (color is FROM the %, so color @ 100% is ignored)
        cols = [(0,0,0)]+cols
        for i, item in enumerate(stops):
            r1, g1, b1 = cols[i]
            r2, g2, b2 = cols[i+1]
            cdict['red'].append([item,r1,r2])
            cdict['green'].append([item,g1,g2])
            cdict['blue'].append([item,b1,b2])

    #return cdict;
    ret = matplotlib.colors.LinearSegmentedColormap(name,cdict);
    matplotlib.pyplot.register_cmap(cmap=ret)
    ret.levels = html[::2] # Add a levels property which retains the un-normalized threshold values
    return ret;

dc_au_ClearObservations_discrete = htmlColorMap([
    0,'#FFFFFF',
    10,'#B21800',
    25,'#FF4400',
    50,'#FF8000',
    100,'#FFA200',
    150,'#FFC000',
    200,'#FFD500',
    250,'#FFF300',
    300,'#E6FF00',
    350,'#BCFF00',
    400,'#89FF00',
    500,'#68C400',
    600,'#44C400',
    700,'#03B500',
    800,'#039500',
    1000,'#026900',
],True,'dc_au_ClearObservations_discrete')

dc_au_ClearObservations = htmlColorMap([
    0,'#FFFFFF',
    10,'#B21800',
    25,'#FF4400',
    50,'#FF8000',
    100,'#FFA200',
    150,'#FFC000',
    200,'#FFD500',
    250,'#FFF300',
    300,'#E6FF00',
    350,'#BCFF00',
    400,'#89FF00',
    500,'#68C400',
    600,'#44C400',
    700,'#03B500',
    800,'#039500',
    1000,'#026900',
],False,'dc_au_ClearObservations')

dc_au_WaterObservations_discrete = htmlColorMap([
    0,'#FFFFFF',
    2,'#890000',
    5,'#990000',
    10,'#E38400',
    25,'#E3DF00',
    50,'#A6E300',
    100,'#00E32D',
    150,'#00E3C8',
    200,'#0097E3',
    250,'#005FE3',
    300,'#000FE3',
    350,'#000EA9',
    400,'#5700E3',
],True,'dc_au_WaterObservations_discrete')

dc_au_WaterObservations = htmlColorMap([
    0,'#FFFFFF',
    2,'#890000',
    5,'#990000',
    10,'#E38400',
    25,'#E3DF00',
    50,'#A6E300',
    100,'#00E32D',
    150,'#00E3C8',
    200,'#0097E3',
    250,'#005FE3',
    300,'#000FE3',
    350,'#000EA9',
    400,'#5700E3',
],False,'dc_au_WaterObservations')

dc_au_Confidence_discrete = htmlColorMap([
    0,'#FFFFFF',
    1,'#000000',
    2,'#990000',
    5,'#CF2200',
    10,'#E38400',
    25,'#E3DF00',
    50,'#A6E300',
    75,'#62E300',
    100,'#00E32D',
],True,'dc_au_Confidence_discrete')

dc_au_Confidence = htmlColorMap([
    0,'#FFFFFF',
    1,'#000000',
    2,'#990000',
    5,'#CF2200',
    10,'#E38400',
    25,'#E3DF00',
    50,'#A6E300',
    75,'#62E300',
    100,'#00E32D',
],False,'dc_au_Confidence')

dc_au_WaterSummary_discrete = htmlColorMap([
    0.2,'#FFFFFF',
    0.5,'#8E0101',
    1,'#CF2200',
    2,'#E38400',
    5,'#E3DF00',
    10,'#A6E300',
    20,'#62E300',
    30,'#00E32D',
    40,'#00E384',
    50,'#00E3C8',
    60,'#00C5E3',
    70,'#0097E3',
    80,'#005FE3',
    90,'#000FE3',
    100,'#5700E3',
    100,'#5700E3'
],True,'dc_au_WaterSummary_discrete')

dc_au_WaterSummary = htmlColorMap([
    0.002,'#FFFFFF',
    0.005,'#8E0101',
    0.01,'#CF2200',
    0.02,'#E38400',
    0.05,'#E3DF00',
    0.10,'#A6E300',
    0.20,'#62E300',
    0.30,'#00E32D',
    0.40,'#00E384',
    0.50,'#00E3C8',
    0.60,'#00C5E3',
    0.70,'#0097E3',
    0.80,'#005FE3',
    0.90,'#000FE3',
    1.00,'#5700E3',
    1.10,'#5700E3',
],False,'dc_au_WaterSummary')
