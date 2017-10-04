Data Cube UI Installation Guide
=================

This document will guide users through the process of installing and configuring our Data Cube user interface. Our interface is a full Python web server stack using Django, Celery, PostreSQL, and Boostrap3. In this guide, both python and system packages will be installed and configured and users will learn how to start asynchronous task processing systems. While this guide provides a manual installation process, we have created scripts that do a lot of the initial setup - these can be found in the section title 'Automated Setup'

Contents
=================

  * [Introduction](#introduction)
  * [Prerequisites](#prerequisites)
  * [Automated Setup](#automated_setup)
  * [Installation Process](#installation_process)
  * [Configuring the Server](#configuration)
  * [Initializing the Database](#database_initialization)
  * [Starting Workers](#starting_workers)
  * [System Overview](#system_overview)
  * [Customize the UI](#customization)
  * [Maintenance, Upgrades, and Debugging](#maintenance)
  * [Common problems/FAQs](#faqs)

<a name="introduction"></a> Introduction
=================

The CEOS Data Cube UI is a full stack Python web application used to perform analysis on raster datasets using the Data Cube. Using common and widely accepted frameworks and libraries, our UI is a good tool for demonstrating the Data Cube capabilities and some possible applications and architectures. The UI's core technologies are:

* [**Django**](https://www.djangoproject.com/): Web framework, ORM, template processor, entire MVC stack
* [**Celery + Redis**](http://www.celeryproject.org/): Asynchronous task processing
* [**Data Cube**](http://datacube-core.readthedocs.io/en/stable/): API for data access and analysis
* [**PostgreSQL**](https://www.postgresql.org/): Database backend for both the Data Cube and our UI
* **Apache/Mod WSGI**: Standard service based application running our Django application while still providing hosting for static files
* [**Bootstrap3**](http://getbootstrap.com/): Simple, standard, and easy front end styling

Using these common technologies provides a good starting platform for users who want to develop Data Cube applications. Using Celery allows for simple distributed task processing while still being performant. Our UI is designed for high level use of the Data Cube and allow users to:

* Access various datasets that we have ingested
* Run custom analysis cases over user defined areas and time ranges
* Generate both visual (image) and data products (GeoTiff/NetCDF)
* Provide easy access to metadata and previously run analysis cases

<a name="prerequisites"></a> Prerequisites
=================

To set up and run our Data Cube UI, the following conditions must be met:

* The full Data Cube Installation Guide must have been followed and completed. This includes:
  * You have a local user that is used to run the Data Cube commands/applications
  * You have a database user that is used to connect to your 'datacube' database
  * The Data Cube is installed and you have successfully run 'datacube system init'
  * All code is checked out and you have a virtual environment in the correct directories: `~/Datacube/{data_cube_ui, data_cube_notebooks, datacube_env, agdc-v2}`
* The full Ingestion guide must have been followed and completed. This includes:
  * A sample Landsat 7 scene was downloaded and uncompressed in your '/datacube/original_data' directory
  * The ingestion process was completed for that sample Landsat 7 scene

If these requirements are not met, please see the associated documentation. Please take some time to get familiar with the documentation of our core technologies - most of this guide is concerning setup and configuration and is not geared towards teaching about our tools.

<a name="automated_setup"></a> Automated Setup
=================

We have automated this setup process as much as we could - You will need to edit all the configurations manually, but the rest of the setup is automated. Edit the files in the `config` directory (.datacube.conf, dc_ui.conf) and the project `settings.py` to reflect the user that will be used to run the UI and the database credentials. Examples of this can be found in the later sections. After your credentials are entered and you have replaced instances of 'localuser' with your system user, run:

```
cd ~/Datacube/data_cube_ui
bash scripts/ui_setup.sh
```

This will move the configuration files, do the migrations, and restart everything. This will also daemonize the celery workers. If you want more detail about the setup process or require some additional modifications, follow the entire process below.

<a name="installation_process"></a> Installation Process
=================

The installation process includes both system level packages and python packages. You will need to have the virtual environment activated for this entire guide.

Run the following commands to install Apache and Apache related packages, Redis, and an image processing library.

```
sudo apt-get install -y apache2
sudo apt-get install -y libapache2-mod-wsgi-py3
sudo apt-get install -y redis-server
sudo apt-get install -y libfreeimage3
sudo apt-get install -y imagemagick
```

There are also a few system level packages that are 'nice to have' or helpful if you are a new user/using Ubuntu desktop rather than server.

```
# Additional/helpful packages can be installed if you intend on installing on Ubuntu desktop
sudo apt-get install -y tmux
```

Next, you'll need various Python packages responsible for the entire application:

```
pip install django
pip install redis
pip install imageio
pip install django-bootstrap3
pip install matplotlib
pip install stringcase
```

The UI relies on a slightly newer version of Celery that has not yet been pushed to Pypi - This is due to a bug that was fixed a few days after their latest release.

```
source ~/Datacube/datacube_env/bin/activate
cd ~/Datacube
git clone https://github.com/celery/celery.git
cd celery
python setup.py install
```

You will also need to create a base directory structure for results:

```
mkdir /datacube/ui_results
chmod 777 /datacube/ui_results
```

The Data Cube UI also sends admin mail, so a mail server is required:

```
# https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-14-04
sudo apt-get install mailutils
# configure as an internet site.
```

In /etc/postfix/main.cf:
```
myhostname = {your site name here}
mailbox_size_limit = 0
recipient_delimiter = +
inet_interfaces = localhost
```

and run `sudo service postfix restart`, then `echo "This is the body of the email" | mail -s "This is the subject line" {your_email@mail.com}` to verify the installation.

With all of the packages above installed, you can now move on to the configuration step.

<a name="configuration"></a> Configuring the Server
=================

The configuration of our application involves ensuring that all usernames and passwords are accurately listed in required configuration files, moving those configuration files to the correct locations, and enabling the entire system.

The first step is to check the Data Cube and Apache configuration files. Open the '.datacube.conf' located in `~/Datacube/data_cube_ui/config/.datacube.conf` and ensure that your username, password, and database name all match. This should be the database and database username/password set **during the Data Cube installation process**. If these details are not correct, please set them and save the file.

**Please note that our UI application uses this configuration file for everything rather than the default.**

Next, we'll need to update the Apache configuration file. Open the file found at `~/Datacube/data_cube_ui/config/dc_ui.conf`:

```
<VirtualHost *:80>
	# The ServerName directive sets the request scheme, hostname and port that
	# the server uses to identify itself. This is used when creating
	# redirection URLs. In the context of virtual hosts, the ServerName
	# specifies what hostname must appear in the request's Host: header to
	# match this virtual host. For the default virtual host (this file) this
	# value is not decisive as it is used as a last resort host regardless.
	# However, you must set it for any further virtual host explicitly.
	#ServerName www.example.com

	ServerAdmin webmaster@localhost
	DocumentRoot /var/www/html

	# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
	# error, crit, alert, emerg.
	# It is also possible to configure the loglevel for particular
	# modules, e.g.
	#LogLevel info ssl:warn

	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	# For most configuration files from conf-available/, which are
	# enabled or disabled at a global level, it is possible to
	# include a line for only one particular virtual host. For example the
	# following line enables the CGI configuration for this host only
	# after it has been globally disabled with "a2disconf".
	#Include conf-available/serve-cgi-bin.conf

	# django wsgi
	WSGIScriptAlias / /home/localuser/Datacube/data_cube_ui/data_cube_ui/wsgi.py
	WSGIDaemonProcess dc_ui python-home=/home/localuser/Datacube/datacube_env python-path=/home/localuser/Datacube/data_cube_ui

	WSGIProcessGroup dc_ui
	WSGIApplicationGroup %{GLOBAL}

	<Directory "/home/localuser/Datacube/data_cube_ui/data_cube_ui/">
		Require all granted
	</Directory>

	#django static
	Alias /static/ /home/localuser/Datacube/data_cube_ui/static/
	<Directory /home/localuser/Datacube/data_cube_ui/static>
		Require all granted
	</Directory>

	#results.
	Alias /datacube/ui_results/ /datacube/ui_results/
	<Directory /datacube/ui_results/>
		Require all granted
	</Directory>

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
```

In this configuration file, note that all of the paths are absolute. If you used a different username (other than 'localuser'), change all instance of 'localuser' to your username. For instance, if your username is 'datacube_user', replace all instance of 'localuser' to 'datacube_user'. This file assumes a standard installation with a virtual environment located in the location specified in the installation documentation.

**This refers to the system user - the user that you use to log in to Ubuntu and run all processes with**

We'll now copy the configuration files where they need to be. The '.datacube.conf' file is copied to the home directory for consistency.

```
cp config/.datacube.conf ~/.datacube.conf
sudo cp config/dc_ui.conf /etc/apache2/sites-available/dc_ui.conf
```

The next step is to edit the credentials found in the Django settings. Open the 'settings.py' found at `~/Datacube/data_cube_ui/data_cube_ui/settings.py`:

```
gedit ~/Datacube/data_cube_ui/data_cube_ui/settings.py
```

There are a few small changes that need to be made for consistency with your settings.

Master node refers to a clustered/distributed setup. This should remain 127.0.0.1 on the main machine, while the other machines will enter the ip address of the main machine here. For instance, if your main machine's public ip is 52.200.156.1, then the worker nodes will enter 52.200.156.1 as the MASTER NODE.

```
MASTER_NODE = '127.0.0.1'
```

The application settings are definable as well. Change the BASE_HOST setting to the url that your application will be accessed with, e.g. for our internal development, we have the server running on the ip 192.168.100.13, so we will enter 192.168.100.13 there. The admin email should be the email that you want the UI to send emails as. Email activation and feedback will be sent as the email here. The host and port are configurable based on where your mail server is. We leave it running locally on port 25.

```
# Application definition
BASE_HOST = "localhost:8000/"
ADMIN_EMAIL = "admin@ceos-cube.org"
EMAIL_HOST = 'localhost'
EMAIL_PORT = '25'
```

Next, replace 'localuser' with whatever your local system user is. This corresponds to the values you entered in the Apache configuration file.

```
LOCAL_USER = "localuser"
```

The database credentials need to be entered here as well - enter the database name, username, and password that you entered in your .datacube.conf file:

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'datacube',
      	'USER': 'dc_user',
      	'PASSWORD': 'localuser1234',
      	'HOST': MASTER_NODE
    }
}
```

Now that the Apache configuration file is in place and the Django settings have been set, we will now enable the site and disable the default. Use the commands listed below:

```
sudo a2dissite 000-default.conf
sudo a2ensite dc_ui.conf
sudo service apache2 restart
```

Additionally, a .pgpass is required for the Data Cube On Demand functionality. Edit the .pgpass in the config directory with your database username and password from above and copy it into the home directory of your local user.

```
# assumes you're logged in as your local user - if not, replace ~ with /home/{username}
sudo cp config/.pgpass ~/.pgpass
sudo chmod 600 ~/.pgpass
```

<a name="database_initialization"></a> Initializing the Database
=================

Now that all of the requirements have been installed and all of the configuration details have been set, it is time to initialize the database.

Django manages all database changes automatically through the ORM/migrations model. When there are changes in the models.py files, Django detects them and creates 'migrations' that make changes to the database according to the Python changes. This requires some initialization now to create the base schemas.

Run the following commands:

```
cd ~/Datacube/data_cube_ui
python manage.py makemigrations {data_cube_ui,accounts,coastal_change,custom_mosaic_tool,fractional_cover,ndvi_anomaly,slip,task_manager,tsm,water_detection,dc_algorithm,data_cube_manager,cloud_coverage,urbanization,spectral_indices}
python manage.py makemigrations
python manage.py migrate

python manage.py loaddata db_backups/init_database.json
```

This string of commands makes the migrations for all applications and creates all of the initial database schemas. The last command loads in the default sample data that we use - including some areas, result types, etc.

Next, create a super user account on the UI for personal use:

```
python manage.py createsuperuser
```

Now that we have everything initialized, we can view the site and see what we've been creating. Visit the site in your web browser - either by ip from an outside machine or at localhost within the machine. You should now see a introduction page. Log in using one of the buttons and view the Custom Mosaic Tool - You'll see all of our default areas. **This does not give access to all of these areas, they are examples. You will need to add your own areas and remove the defaults.**

Visit the administration panel by going to either {ip}/admin or localhost/admin. You'll see a page that shows all of the various models and default values.


<a name="starting_workers"></a> Starting Workers
=================

We use Celery workers in our application to handle the asynchronous task processing. We use tmux to handle multiple detached windows to run things in the background. In the future, we will be moving to daemon processes, but for now we like to be able to see the debugging output. For the current implementation, we use multiple worker instances - one for general task processing and one for the Data Cube manager functionality. The Data Cube manager worker has a few specific parameters that make some of the database creation and deletion operations work a little more smoothly.

Open two new terminal sessions and activate the virtual environment in both:

```
source ~/Datacube/datacube_env/bin/activate
cd ~/Datacube/data_cube_ui
```

In the first terminal, run the celery process with:

```
celery -A data_cube_ui worker -l info -c 4
```

In the second terminal, run the single use Data Cube Manager queue.

```
celery -A data_cube_ui worker -l info -c 2 -Q data_cube_manager --max-tasks-per-child 1 -Ofair
```

Additionally, you can run both simultaneously using Celery multi:

```
celery multi start -A data_cube_ui task_processing data_cube_manager -c:task_processing 10 -c:data_cube_manager 2 --max-tasks-per-child:data_cube_manager=1  -Q:data_cube_manager data_cube_manager -Ofair
```

To start the task scheduler, run the folliwng command:
```
celery -A data_cube_ui beat
```

To test the workers we will need to add an area and dataset that you have ingested to the UI's database. This will happen in a separate section.

This process can be automated and daemonized with the following snippet:

```
sudo cp config/celeryd_conf /etc/default/data_cube_ui && sudo cp config/celeryd /etc/init.d/data_cube_ui
sudo chmod 777 /etc/init.d/data_cube_ui
sudo chmod 644 /etc/default/data_cube_ui
sudo /etc/init.d/data_cube_ui start

sudo cp config/celerybeat_conf /etc/default/celerybeat && sudo cp config/celerybeat /etc/init.d/celerybeat
sudo chmod 777 /etc/init.d/celerybeat
sudo chmod 644 /etc/default/celerybeat
sudo /etc/init.d/celerybeat start

```

This is done in the initial setup script.

You can alias the /etc/init.d/* script as whatever you like - you can start, stop, kill, restart, etc. the workers using this script.


<a name="system_overview"></a> Task System Overview
=================

The worker system can seem complex at first, but the basic workflow is shown below:

* The Django view receives form data from the web page. This form data is processed into a Query model for the application
* The main Celery worker receives a task with a Query model and pulls all of the required parameters from this model
* Using predefined chunking options, the main Celery task splits the parameters (latitude, longitude, time) into smaller chunks
* These smaller chunks of (latitude, longitude, time) are sent off to the Celery slave processes - there should be more slave processes than master processes
* The Celery slave processes load in the data in the parameters they received and perform some analysis. The results are saved to disk and the paths are returned
* The master process waits until all chunks have been processed then loads all of the result chunks. The chunks are combined into a single product and saved to disk
* The master process uses the data product to create images and data products and saves them to disk, deleting all the remnant chunk products
* The master process creates a Result and Metadata model based on what was just created and returns the details to the browser


<a name="customization"></a> Customize the UI
=================

To finish the configuration, we will need to create an area and product that you have ingested. For this section, we have to have a few assumptions:

* Your ingested product definition's name is ls7_ledaps_general
* You have ingested a Landsat 7 scene

First, we need to find the bounding box of your area. Open a Django Python shell and use the following commands:

```
source ~/Datacube/datacube_env/bin/activate
cd ~/Datacube/data_cube_ui
python manage.py shell

from utils import data_access_api

dc = data_access_api.DataAccessApi()

dc.get_datacube_metadata('ls7_ledaps_general','LANDSAT_7')
```

Record the latitude and longitude extents.

Go back to the admin page, select dc_algorithm->Areas, delete all of the initial areas, then click the 'Add Area' button.

For the Area Id, enter 'general', or whatever area you've named that is prepended by the 'ls7_ledaps_'. Give the area a name as well.

Enter the latitude and longitude bounds in all of the latitude/longitude min/max fields for both the top and the detail fields.

For all of the imagery fields, enter '/static/assets/images/black.png'/static/assets/images/black.png' - this will give a black area, but will still highlight our area.

Select LANDSAT_7 in the satellites field and save your new area.

Navigate back to the main admin page and select dc_algorithm->Applications. Choose custom_mosaic_tool and select your area in the areas field. Save the model and exit.

Go back to the main site and navigate back to the Custom Mosaic Tool. You will see that your area is the only one in the list - select this area to load the tool. Make sure your workers are running and submit a task over the default time over some area and watch it complete. The web page should load an image result.


<a name="maintenance"></a> Maintenance, Upgrades, and Debugging
=================

Upgrades can be pulled directly from our GitHub releases using Git. There are a few steps that will need to be taken to complete an upgrade from an earlier release version:

* Pull the code from our repository
* Make and run the Django migrations with 'python manage.py makemigrations && python manage.py migrate'. We do not keep our migrations in Git so these are specific to your system.
* If we have added any new applications (found in the apps directory) then you'll need to run the specific migration with 'python manage.py makemigrations {app_name} && python manage.py migrate'
* If there are any new migrations, load the new initial values from our .json file with 'python manage.py loaddata db_backups/init_database.json'
* Now that your database is working, stop your existing Celery workers (daemon and console) and run a test instance in the console with 'celery -A data_cube_ui worker -l info'.
* To test the current codebase for functionality, run 'python manage.py runserver 0.0.0.0:8000'. Any errors will be printed to the console - make any required updates.
* Restart apache2 for changes to appear on the live site and restart your Celery worker. Ensure that only one instance of the worker is running.

Occasionally there may be some issues that need to be debugged. Some of the common scenarios have been enumerated below, but the general workflow is found below:

* Stop the daemon Celery process and start a console instance
* Run the task that is causing your error and observe the error message in the console
* If there is a 500 http error or a Django error page, ensure that DEBUG is set to True in settings.py and observe the error message in the logs or the error page.
* Fix the error described by the message, restart apache, restart workers

If you are having trouble diagnosing issues with the UI, feel free to contact us with a description of the issue and all relevant logs or screenshots. To ensure that we are able to assist you quickly and efficiently, please verify that your server is running with DEBUG = True and your Celery worker process is running in the terminal with loglevel info.

<a name="faqs"></a> Common problems/FAQs
========  
----  

Q: 	
 >I’m getting a “Permission denied error.”  How do I fix this?  

A:  
>	More often than not the issue is caused by a lack of permissions on the folder where the application is located.  Grant full access to the folder and its subfolders and files (this can be done by using the command “chmod -R 777 FOLDER_NAME”).  

Q: 	
 >I'm getting a too many connections error when I visit a UI page

A:  
>	The Celery worker processes have opened too many connections for your database setup. Edit the connection number allowed in your postgresql.conf file. If this number is already sufficient, that means that one of the celery workers is opening connections without closing them. To diagnose this issue, start the celery workers with a concurrency of 1 (e.g. -c 1) and check to see what tasks are opening postgres connections and not closing them. Ensure that you stop the daemon process before creating the console Celery worker process.

Q: 	
 >My tasks won't run - there is an error produced and the UI creates an alert

A:  
>	Start your celery worker in the terminal with debug mode turned on and loglevel=info. Stop the daemon process if it is started to ensure that all tasks will be visible. Run the task that is failing and observe any errors. The terminal output will tell you what task caused the error and what the general problem is.

Q: 	
 >Tasks don't start - when submitted on the UI, a progress bar is created but there is never any progress.

A:  
>	This state means that the Celery worker pool is not accepting your task. Check your server to ensure that a celery worker process is running with 'ps aux | grep celery'. If there is a Celery worker running, check that the MASTER_NODE setting is set in the settings.py file to point to your server and that Celery is able to connect - if you are currently using the daemon process, stop it and run the worker in the terminal.  

Q: 	
 >I'm seeing some SQL related errors in the Celery logs that prevent tasks from running

A:  
>	Run the Django migrations to ensure that you have the latest database schemas. If you have updated recently, ensure that you have a database table for each app - if any are missing, run 'python manage.py makemigrations {app_name}' followed by 'python manage.py migrate'.
---  
