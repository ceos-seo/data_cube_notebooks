"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Utility class designed to access the DOM of various web pages and perform a number of different
fucntional tests.  Any combination of these methods can be used to test a variety of functionality
within the application.  This is a constantly growing python file.  Everything should be abstracted
out enough so no values are hard code.
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

import time
import platform
import os

# Configuration options for Firefox
caps = DesiredCapabilities.FIREFOX
caps["marionette"] = True
caps["binary"] = "C:\\Program Files (x86)\\Mozilla Firefox\\firefox"

# Configuration options for Chrome
my_chrome_options = Options()
my_chrome_options.add_argument("--ignore-gpu-blacklist")

# Constants
# Localhost being used here on the VM.  Can code in actual IP address if desired.
url = "http://bigdata-node3.ama-inc.com:8000"
#url = "http://192.168.100.155"
browser_type = "chrome"

# Driver
driver = None

# Connecting to browser and opening.
# Returns the driver to be used to navigate.
def open_browser():
    global driver
    global url
    global browser_type

    # For Firefox.  Can't use yet due to lack of functionality.
    if browser_type == 'firefox':
        driver = webdriver.Firefox(capabilities=caps)
    
    # Checking for type of OS
    if browser_type == 'chrome':
        if "Linux" in platform.platform():
            driver = webdriver.Chrome('/home/localuser/Datacube/data_cube_ui/testsuite/drivers/chromedriver_linux', chrome_options=my_chrome_options)
        elif "Windows" in platform.platform():
            driver_location = os.getcwd().replace("selenium","drivers") + "\\chromedriver_windows"
            driver = webdriver.Chrome(driver_location, chrome_options=my_chrome_options)
    
    driver.get(url)
    driver.maximize_window()

    log_in()
    
    return driver

# Logging in.
def log_in():
    driver.find_element_by_id("login-button").click()
    driver.find_element_by_id("id_username").send_keys("localuser")
    driver.find_element_by_id("id_password").send_keys("amadev12")
    time.sleep(2)
    driver.find_element_by_id("log-in-submit").click()

# Given a cube name will go to that cube.    
def get_cube(cube_name):
    action = webdriver.ActionChains(driver)
    elem = driver.find_element_by_id("map_tools")
    action.move_to_element(elem)
    time.sleep(2)
    action.move_to_element(driver.find_element_by_id(cube_name))
    time.sleep(2)
    action.perform()
    
    time.sleep(2)
    driver.find_element_by_id(cube_name).click()

# Run a job for Landsat 7/8
# band_selection must be a list of strings
def create_job_landsat(lat_min, lat_max, lon_min, lon_max, start_date, end_date, title, description, landsat_number, sleep_time, band_selection):
    driver.find_element_by_id("satellite_sel").click()
    time.sleep(1)
    if landsat_number == "7":
        driver.find_element_by_xpath("//*[contains(text(), 'Landsat 7')]").click()
    elif landsat_number == "8":
        driver.find_element_by_xpath("//*[contains(text(), 'Landsat 8')]").click()
    driver.find_element_by_id("satellite_sel").click()

    driver.find_element_by_id("LANDSAT_"+landsat_number+"_band_selection_ms").click()
    checkboxes = driver.find_elements_by_xpath("//input[@type='checkbox']")
    for checkbox in checkboxes:
        #if 'LANDSAT_'+landsat_number in checkbox.get_attribute('id'):
        if ('LANDSAT_'+landsat_number in checkbox.get_attribute('id')) and (checkbox.get_attribute('title') in band_selection):
            checkbox.click()
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_band_selection_ms").click()
    time.sleep(2)
    
    # Set Lon,Lat min and max.
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_latitude_min").send_keys(lat_min)
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_latitude_max").send_keys(lat_max)
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_longitude_min").send_keys(lon_min)
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_longitude_max").send_keys(lon_max)

    # Set the date.
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_time_start").send_keys(start_date)
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_time_end").clear()
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_time_end").send_keys(end_date)
    time.sleep(2)
    driver.find_element_by_xpath("//*[contains(text(), 'Done')]").click()
    time.sleep(2)

    # Add additional info.
    driver.find_element_by_id("additional-info-LANDSAT_"+landsat_number+"").click()
    time.sleep(2)
    driver.find_element_by_id("query-title").send_keys(title)
    driver.find_element_by_id("query-description").send_keys(description)
    time.sleep(2)
    driver.find_element_by_id("save-and-close").click()
    time.sleep(2)

    # Submit request
    driver.find_element_by_id("submit-request-LANDSAT_"+landsat_number+"").click()
    driver.find_element_by_id("LANDSAT_"+landsat_number+"_latitude_min").click()
    time.sleep(sleep_time)

# Cancels the currently running job given an ID of a cancel button.
def cancel_job(job_id):
    driver.find_element_by_id(job_id).click()
    time.sleep(2)

# Detects a popup and closes it.
def close_popup():
    try:
        driver.switch_to_alert().accept()
        time.sleep(2)
    except NoAlertPresentException as e:
        print("no alert")

# Shows the results of the first item in the list of executed tasks.
def show_results():
    driver.find_element_by_id("past_0").click()
    time.sleep(2)
    driver.find_element_by_id("load0").click()
    time.sleep(2)
    driver.find_element_by_id("ui-id-2").click()
    time.sleep(2)
    driver.find_element_by_xpath("//div[@id='task_list']/h3").click()
    time.sleep(10)

# Clicks to highlight the no data or unhighlight
def toggle_no_data():
    driver.find_element_by_xpath("//*[@name='show_nodata']").click()
    time.sleep(3)

# Clicks to high or unhide the data.
def toggle_show_hide():
    driver.find_element_by_xpath("//*[contains(text(), 'Show/Hide')]").click()
    time.sleep(3)

# Loads the first of scene.  Wait time necesary because the scene may be rather larges.
def load_single_scene(wait_time):
    driver.find_element_by_xpath("//*[contains(text(), 'Load this scene')]").click()
    time.sleep(wait_time)

# Havigate to task manager.
def go_to_task_manager():
    driver.find_element_by_id("logout-button")
    driver.find_element_by_id("task-manager-nav").click()
    time.sleep(2)
    
# Click on the details for a single query.
def get_details_page():
    driver.find_element_by_class_name("btn").click()
    time.sleep(2)

# Click to view image by itself.
def view_image():
    driver.find_element_by_xpath("//*[contains(text(), 'View image')]").click()
    time.sleep(3)
    driver.find_element_by_tag_name("body").send_keys(Keys.CONTROL + "w")
    time.sleep(2)

# Download the TIF file
def download_tif():
    driver.find_element_by_xpath("//*[contains(text(), 'Download tif')]").click()
    time.sleep(2)

# Logging out method
def logout():
    driver.find_element_by_id("logout-button").click()
    time.sleep(5)

# Sends keys to the search bar in the task manager.
def type_keys_in_search(list_of_keys):
    driver.find_element_by_xpath("//div[@id='query-list-table-full_filter']/label/input").send_keys(list_of_keys)
    time.sleep(3)
    driver.find_element_by_xpath("//div[@id='query-list-table-full_filter']/label/input").clear()
    time.sleep(1)

# Click next or previouse.
def navigate_pagination(pagination_fp):
    if pagination_fp == 'next':
        driver.find_element_by_xpath("//div[@id='query-list-table-full_paginate']/a[@id='query-list-table-full_next']").click()
    elif pagination_fp == 'previous':
        driver.find_element_by_xpath("//div[@id='query-list-table-full_paginate']/a[@id='query-list-table-full_previous']").click()
    time.sleep(3)
