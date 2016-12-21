"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a selenium test designed to test the UI for creating requests.  It has methods that have
both correct and incorrect inputs, tests cancelling, and tests repeat queries.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
# Selenium dependencies
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import util_methods as util

import time
import platform
import os

try:
    driver = None
    driver = util.open_browser()

    # Setting to poll for 5 seconds if element isn't present.
    driver.implicitly_wait(5)

    util.get_cube("colombia_micro")

    # Long request just to be able to cancel.
    util.create_job_landsat("-0.5", "0.25", "-75.2", "-74.5", "01/01/2010", "01/01/2016", "Sample Title", "Sample description", "7", 3, ['Blue'])
    util.cancel_job("cancel_2010-01-01-2016-01-01-0.25--0.5--74.5--75.2-blue-LANDSAT_7--true_color")
    driver.refresh()
    # This is an invald job with bad parameters.
    util.create_job_landsat("asdf", "spooky", "not real inputs", "25", "01/01/2015", "01/01/2016", "Sample Title", "Sample description", "7", 10, ['Blue'])
    driver.refresh()
    # This is a valid job for the Colombia Microcube
    util.create_job_landsat("-0.5", "0.25", "-75.2", "-74.5", "01/01/2015", "01/01/2016", "Sample Title", "Sample description", "7", 30, ['Blue'])
    driver.refresh()
    # Repeat of the same query.
    util.create_job_landsat("-0.5", "0.25", "-75.2", "-74.5", "01/01/2015", "01/01/2016", "Sample Title", "Sample description", "7", 10, ['Blue'])
    driver.refresh()
    # This has no acquisitions
    util.create_job_landsat("-0.5", "0.25", "-75.2", "-75.2", "01/01/2015", "01/01/2016", "Sample Title", "Sample description", "7", 5, ['Blue'])
    util.close_popup()
    driver.refresh()
    
    # Adding extra data for later testing
    util.create_job_landsat("-1.0", "-0.5", "-76.5", "-75.5", "01/01/2015", "01/01/2016", "Query1", "Sample description", "7", 30, ['Blue','Green'])
    driver.refresh()
    util.create_job_landsat("-0.5", "0.0", "-76.0", "-75.0", "01/01/2015", "01/01/2016", "Query2", "Sample description", "7", 30, ['Red'])
    driver.refresh()
    util.create_job_landsat("0.0", "0.25", "-75.5", "-74.5", "01/01/2015", "01/01/2016", "Query3", "Sample description", "7", 30, ['NIR','SWIR1'])
    driver.refresh()
    util.create_job_landsat("0.25", "0.5", "-75.0", "-74.7", "01/01/2015", "01/01/2016", "Query4", "Sample description", "7", 30, ['Blue','SWIR2'])
    driver.refresh()
    util.create_job_landsat("0.5", "0.75", "-74.5", "-74.3", "01/01/2015", "01/01/2016", "Query5", "Sample description", "7", 30, ['SWIR1','SWIR2'])
    driver.refresh()
    util.create_job_landsat("0.5", "1.0", "-74.5", "-74.0", "01/01/2015", "01/01/2016", "Query6", "Sample description", "7", 30, ['Green','Red'])
    driver.refresh()

finally:
    time.sleep(10)
    util.logout()
    driver.quit()
