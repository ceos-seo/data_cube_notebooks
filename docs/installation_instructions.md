Data Cube UI Installation Guide
=================


Before beginning this installation process ensure the Data Cube has been properly installed and data has been ingested. For installation and ingestion instructions, refer to [this guide]().

Contents
=================

  * [Introduction](#introduction)
  * [Checking Out Code](#checking_out_code)
  * [Installation Process](#installation_process)
  * [Configuration](#configuration)
  * [Creating a User Account](#creating_a_user_account)
  * [Running the Application](#running_the_application)
  * [Importing Areas and Adding New Areas](#importing_areas_of_interest)
  * [Common problems/FAQs](#faws)
			

Introduction <a name="introduction"></a>
=================
The UI application is designed for high level use of the Data Cube.  It allows for users to:  

- traverse various cubes (assuming multiple cubes have been ingested)
- set customized bounds via direct input or highlighting of the desired area
- 	obtain an image of the given area
- 	load previously ran results
- 	view advanced details for a given request
- 	download the image for the given bounds
- 	download the tif data

This document outlines the steps required to set up the UI given the previous DataCube base installation instructions have been followed.


Checking Out Code <a name="checking_out_code"></a>
=================

The code should be checked out to the Datacube directory that was created from the previous [datacube installation document]():

	cd ~/Datacube
	git clone https://github.com/ceos-seo/data_cube_ui.git -b master
	cd ~/Datacube/data_cube_ui
	git submodule init && git submodule update

Installation Process <a name="installation_process"></a>
=================
There are two dependencies that will need to be installed that accompany the application:  

- 	`Redis v2.10.5`  
-	`Celery v3.1.23`  

The admin will also need to install `Apache2` and the `Mod-WSGI` with the following commands:  

	sudo apt-get install -y apache2
	sudo apt-get install -y libapache2-mod-wsgi-py3

The next set of dependencies are installed in the python virtual environment:  

	source ~/Datacube/datacube_env/bin/activate
	pip install django==1.9.7
	pip install redis==2.10.5
	pip install celery==3.1.23
	pip install imageio
	pip install scipy

>NOTE: If Notebooks were installed then this dependency is already installed.  

	sudo apt-get install -y redis-server  

Configuration <a name="configuration"></a>
================= 

Edit the `dc_ui.conf` file found at `~/Datacube/data_cube_ui/config/dc_ui.conf`:  

- 	If your username is `localuser`, you can just copy this into your apache sites directory in the next step. 
	- If you username is not `localuser`, change all instances of `localuser` to your username and ensure that your directory structure matches that listed in the configuration file. 
	`/home/<username>/Datacube/data_cube_ui/`  

Copy the `dc_ui.conf` file to your apache folder and activate the site.  
  
	sudo cp ~/Datacube/data_cube_ui/config/dc_ui.conf /etc/apache2/sites-available/dc_ui.conf
	sudo a2ensite dc_ui.conf
	sudo a2dissite 000-default.conf
	sudo service apache2 restart
	
Edit the `.datacube.conf` file found at `~/Datacube/data_cube_ui/config/.datacube.conf`:  

- Ensure that the hostname is commented out with a ‘#’, 
	- e.g. #db_hostname: `192.168.101.3`  


- Ensure that the `db_username` and `db_password` fields match the `postgresql` user that was used to create the datacube database in the Data Cube installation procedure.  
 
- This should be `dc_user//dcuser1`


Copy the `.datacube.conf` file to your home directory:  

	sudo cp ~/Datacube/data_cube_ui/config/.datacube.conf ~/.datacube.conf  

Creating a User Account  <a name="creating_a_user_account"></a>
============  

In order to log in to the application, a user account must be created to authenticate against.

To start the user creation process, open a terminal and launch the python virtual environment 

	source ~/Datacube/datacube_env/bin/activate  

Navigate to the root directory of the UI application 

	cd ~/Datacube/data_cube_ui/data_cube_ui  

Open the file located at  
  
`~/Datacube/data_cube_ui _ui/data_cube_ui/settings.py`  

Make sure the username is `dc_user` and the password is `dcuser1`

>Note: This should match the postgresql username and password used when installing the Data Cube. 


Migrate the auth tables with the command:  

	cd ~/Datacube/data_cube_ui
	python manage.py migrate auth

Migrate the other tables with the command:  

	python manage.py makemigrations
	python manage.py migrate

Type the following command:
	python manage.py createsuperuser

The terminal will ask for three pieces of information:  

- `user name` - this should be `localuser`  
- `email address` - this can be left blank by simply hitting return  
- `password` - alpha-numeric (at least 8 characters long). For the sake of easy/consistent installation, use `localuser1234`  


Running the Application<a name="running_the_application"></a>
==============

In order to run the application, `Celery` and `Redis` must be started.

To start Celery:  

- Open a terminal for each process
	- Master process started with:  
  
			cd ~/Datacube/data_cube_ui  
			celery -A data_cube_ui worker -l info -c 4

	- Slave process started with:  
	
			celery -A data_cube_ui worker -l info -c 8 -Q chunk_processing -n chunk_processing  

		- `-c 8` represents the number of workers.  For less powerful machines, this number should be lower as it will consume more resources the higher it is.


Navigate to the site’s home page by getting the IP address (ifconfig) and typing that directly into the URL box in the browser.

Importing Areas and Adding New Areas<a name="importing_areas_of_interest"></a>
===

The DataCube UI comes with a set of default areas along with having the ability to add new areas with ease:

- **To import the list of areas** run the following series of commands:  

		source ~/Datacube/datacube_env/bin/activate  
		cd ~/Datacube/data_cube_ui  
		python manage.py loaddata db_backups/empty_db.json
	- Another option for adding areas is to do this through the admin page of the UI
		- Start by navigating to the URL:
			`http://<IP_ADDRESS>/admin`
		- Under `DATA_CUBE_UI`, there is an areas with an `Add` button.  
		- Click the add button and fill out the data with the appropriate information.  
		- Hit the save button and the area will have been added to the UI database allowing for use in the application.

Common problems/FAQs <a name="faqs"></a>
========  
----  

Q: 	
 >I’m getting a “Permission denied error.”  How do I fix this?  
 
A:  
>	More often than not the issue is caused by a lack of permissions on the folder where the application is located.  Grant full access to the folder and its subfolders and files (this can be done by using the command “chmod -R 777 FOLDER_NAME”).  
	
---  

Q:
>`DoesNotExist` page appears when I click on the details for a given task.  
 
A:  
> This is probably due to bad data in the database.  It is best to simply remove this particular task and run it again.  
  
---    

Q:
> I ran a query but it’s not showing in the Track History section.  I don’t see a popup with any error.  

A:  
>	Celery is designed to handle any failures gracefully.  This means that you may need to bring up the terminal that has Celery running to look for errors.  
  
---    

Q:  
>	I typed in the correct username and password but it still won’t let me log in.  
  
A:  
>	This problem usually occurs when trying to export the application to another computer.  It can be fixed easily with the following command:  
>	
		python manage.py changepassword USER_NAME

>You’ll be prompted to enter the password then once more for confirmation.  Try logging in again the problem should be resolved.
