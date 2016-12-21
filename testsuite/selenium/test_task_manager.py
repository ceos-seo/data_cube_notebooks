"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a selenium test designed to test the UI, specifically the Task Manager page to include
filtering and pagination.
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

    util.go_to_task_manager()
    util.type_keys_in_search('green')
    util.type_keys_in_search('blue')
    util.type_keys_in_search('swir1')
    util.type_keys_in_search('swir2')
    util.type_keys_in_search('red')

    driver.refresh()
    time.sleep(3)

    util.navigate_pagination('next')
    util.navigate_pagination('previous')
    
finally:
    time.sleep(10)
    util.logout()
    driver.quit()
