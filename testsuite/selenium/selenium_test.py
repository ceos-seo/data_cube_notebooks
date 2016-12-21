"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a selenium document that is designed to show some of the features of the UI.  This will not
test all functionality and only tests data on the Colombia Microcube.
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

    # Go to any Cube page.
    util.get_cube("kenya_micro")
    util.get_cube("colombia_micro")

    # Creates a Request
    util.create_job_landsat("-0.5", "0.25", "-75.2", "-74.5", "01/01/2015", "01/01/2016", "Sample Title", "Sample description", "7", 30, ['Blue', 'Green'])

    util.show_results()
    util.toggle_no_data()
    util.toggle_show_hide()
    util.toggle_show_hide()
    util.toggle_no_data()
    util.load_single_scene(10)
    
    # Go to Task Manager page.
    util.go_to_task_manager()
    
    # Go to Details page.
    util.get_details_page()
    util.view_image()
    util.download_tif()

finally:
    time.sleep(10)
    util.logout()
    driver.quit()
