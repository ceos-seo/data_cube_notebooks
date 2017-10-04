Data Cube Installation Guide
=================
This document will guide users through the process of installing and configuring a base Data Cube system. For the Ingestion, UI and Jupyter examples, please refer to the documentation in the associated repository.

Contents
=================
  * [Introduction](#introduction)
  * [System Requirements](#system_requirements)
  * [Checking Out Code](#checking_out_code)
  * [Installation Process](#installation_process)
  * [Configuration](#configuration)
  * [Next Steps](#next_steps)
  * [Common problems/FAQs](#faqs)


<a name="introduction"></a> Introduction
=================
The Data Cube is a system designed to:

* Catalogue large amounts of Earth Observation data
* Provide a Python based API for high performance querying and data access
* Give scientists and other users easy ability to perform Exploratory Data Analysis
* Allow scalable continent scale processing of the stored data
* Track the provenance of all the contained data to allow for quality control and updates

This document will outline the steps required to have a functional Data Cube installation with all required dependencies.

<a name="system_requirements"></a> System Requirements
=================
This document is targeting an Ubuntu based development environment - either on a local server or in a virtual machine. The base requirements can be found below:

* **OS**: Ubuntu 16.04 LTS - [Download here](https://www.ubuntu.com/download/desktop)
* **Memory**: 8GB+ of memory is preferred
* **Local Storage**: 50Gb of local storage is preferred
* **Python Version**: We use Python3 for all of our Data Cube related activities

We recommend downloading all updates during installation. To match our system setup, you should also do the following:

* **Create a local user that will be used to run all of the processes**: We use 'localuser', but this can be anything you want. You can even set up the OS with a single user and just use that as your local user. Do not use special characters in this username as it can potentially cause issues in the future. We recommend an all lowercase underscore separated string.
* **Create your base directory structure to hold all of the relevant codebases**: We create everything in a directory 'Datacube' in the local user's directory. We also create a base directory structure for raw data and the ingested data in the root directory '/datacube/\*'
* **Create a virtual environment named 'datacube_env' in the ~/Datacube directory**: We use a single virtual environment for all of our Data Cube related packages/modules. To set this up, you must install virtualenv for Python3 and initialize the environment.


```
mkdir ~/Datacube
sudo mkdir -p /datacube/{original_data,ingested_data}
sudo chmod -R 777 /datacube/
sudo apt-get install -y python3-pip
sudo pip3 install virtualenv
virtualenv ~/Datacube/datacube_env
```

When installing Python packages, you'll need to have the virtual environment activated. This can be done with:

```
source ~/Datacube/datacube_env/bin/activate
#check the python version with:
python -V
#ensure that the output is 'Python 3.5.x'
```

To exit the virtual environment, simply enter:

```
deactivate
```

<a name="checking_out_code"></a>Checking Out Code
=================
First, ensure that Git is installed:

```
sudo apt-get install git
```

The code should be checked out to the ~/Datacube directory that was created in the previous [system requirements section](#system_requirements):

```
cd ~/Datacube
git clone https://github.com/ceos-seo/agdc-v2.git -b master
git clone https://github.com/ceos-seo/data_cube_ui.git -b master
git clone https://github.com/ceos-seo/data_cube_notebooks.git -b master
cd ~/Datacube/data_cube_ui
git submodule init && git submodule update
cd ~/Datacube/data_cube_notebooks
git submodule init && git submodule update
```

This will check out all of our relevant repositories and initialize all submodules. Our UI and notebook examples share utility functions, so we have created a submodule in each of them that must be initialized.

<a name="installation_process"></a>Installation Process
=================
There are a few system level dependencies that must be satisfied before the agdc-v2/datacube-core codebase can be installed.

```
sudo apt-get install -y postgresql-9.5 postgresql-client-9.5 postgresql-contrib-9.5
sudo apt-get install -y libhdf5-serial-dev libnetcdf-dev
sudo apt-get install -y libgdal1-dev
sudo apt-get install -y hdf5-tools netcdf-bin gdal-bin
```

There are also a few system level packages that are 'nice to have' or helpful if you are a new user/using Ubuntu desktop rather than server.

```
# Additional/helpful packages can be installed if you intend on installing on Ubuntu desktop
sudo apt-get install -y postgresql-doc-9.5 libhdf5-doc netcdf-doc libgdal-doc pgadmin3 tmux
```

Now that all of the system level dependencies have been satisfied, there are some Python packages that must be installed before running the setup script. Ensure that you have your virtual environment activated and ready for use - You should see (datacube_env) on your terminal window.

```
pip install numpy
pip install --global-option=build_ext --global-option="-I/usr/include/gdal" gdal==1.11.2
pip install shapely
pip install scipy
pip install cloudpickle
pip install Cython
pip install netcdf4
```

Please note that the installed gdal version should be as close to your system gdal version as possible, printed with:

```
gdalinfo --version
pip install gdal==99999999999
```

At the time this is being written, the above command outputs 1.11.3, which means that version 1.11.2 is the closest version that satisfies our requirements.

Now that all requirements have been satisfied, run the setup.py script in the agdc-v2 directory:

**It has come to our attention that the setup.py script fails the first time it is run due to some NetCDF/Cython issues. Run the script a second time to install if this occurs.**
```
cd ~/Datacube/agdc-v2
python setup.py develop
```

This should produce a considerable amount of console output, but will ultimately end with a line resembling:

```
Finished processing dependencies for datacube==1.1.15+367.g93ac52e
```

<a name="configuration"></a>System Configuration
=================
There are a few minor changes required to prevent any potential errors that can occur during the Data Cube configuration process.

PostgreSQL Configuration
---------------
The first step is modifying some PostgreSQL settings to ensure that everything goes smoothly for the next few steps. Open the postgresql.conf file found at `/etc/postgresql/9.5/main/postgresql.conf` as a super user.

Open this file in your editor of choice and find the line that starts with 'timezone'. This setting may default to 'localtime'; change this to 'UTC'. The resulting line should look like:

```
timezone = 'UTC'
```

This will ensure that all of the datetime fields in the database are stored in UTC. Next, open the pg_hba.conf file found at:

```
/etc/postgresql/9.5/main/pg_hba.conf
```

Open this file in your editor of choice and find the line that resembles:

```
# "local" is for Unix domain socket connections only
local   all             all                                     peer
```

Change that line so that the authentication method is md5, as seen on the line below:

```
# "local" is for Unix domain socket connections only
local   all             all                                     md5
```

This will ensure that you are able to authenticate via password when connecting to the database from the local system. Now that the PostgreSQL settings have been modified, restart the service:

```
sudo service postgresql restart
```

Data Cube Configuration file
---------------
The Data Cube requires a configuration file that points to the correct database and provides credentials. The file's contents looks like below should be named '.datacube.conf':

```
[datacube]
db_database: datacube

# db_hostname

db_username: dc_user
db_password: localuser1234
```

The db_username and db_password fields represent the credentials to a PostgreSQL role that will need to be created. We use the credentials listed above, but they can be changed to any desired combination that contains only valid PostgreSQL characters. Using this user, a database named 'datacube' will be created. Again, this database name is fully configurable and can be set in the above configuration file. **If you do not want to use dc_user as the database role, please change this in the .datacube.conf file**

Please note that this is the **database user** and is different from the local system user.

A copy of this file can be found in the UI directory that was checked out previously in this document. Modify the file at `~/Datacube/data_cube_ui/config/.datacube.conf` using your editor of choice if you want a different credential set, then copy it to your home directory:

```
#Edit username and password if desired
gedit ~/Datacube/data_cube_ui/config/.datacube.conf
cp ~/Datacube/data_cube_ui/config/.datacube.conf ~/.datacube.conf
```

This will move the required .datacube.conf file to the home directory. The user's home directory is the default location for the configuration file and will be used for all command line based Data Cube operations. The next step is to create the database specified in the configuration file.

To create the database use the following:

```
sudo -u postgres createuser --superuser dc_user
sudo -u postgres psql -c "ALTER USER dc_user WITH PASSWORD 'localuser1234';"
createdb -U dc_user datacube
```

This command block creates a superuser with the username 'dc_user', sets the password, and creates a database as 'dc_user'. If the username, password, or database name was changed in the configuration file change them in the commands listed above as well.

To finish the system initialization process, run the following Data Cube command to initialize the database with the default schemas and metadata types.

```
datacube -v system init
```

If everything was successful, you will see console output that resembles the following:

```
2017-04-17 18:51:47,546 22475 datacube INFO Running datacube command: /home/localuser/Datacube/datacube_env/bin/datacube -v system init
Initialising database...
2017-04-17 18:51:47,571 22475 datacube.index.postgres.tables._core INFO Ensuring user roles.
2017-04-17 18:51:47,665 22475 datacube.index.postgres.tables._core INFO Creating schema.
2017-04-17 18:51:47,666 22475 datacube.index.postgres.tables._core INFO Creating tables.
2017-04-17 18:51:47,801 22475 datacube.index.postgres.tables._core INFO Adding role grants.
2017-04-17 18:51:47,806 22475 datacube.index._api INFO Adding default metadata types.
Created.
Checking indexes/views.
2017-04-17 18:51:47,951 22475 datacube.index.postgres._api INFO Checking dynamic views/indexes. (rebuild views=True, indexes=False)
Done.
```

If you have PGAdmin3 installed, you can view the default schemas and relationships by connecting to the database named 'datacube' and viewing the tables, views, and indexes in the schema 'agdc'.

<a name="next_steps"></a> Next Steps
========  
Now that the Data Cube system is installed and initialized, the next step is to ingest some sample data. Our focus is on ARD (Analysis Ready Data) - the best introduction to the ingestion/indexing process is to use a single Landsat 7 or Landsat 8 SR product. Download a sample dataset from [Earth Explorer](https://earthexplorer.usgs.gov/) and proceed to the next document in this series, [The ingestion process](ingestion.md). Please ensure that the dataset you download is an SR product - the L\*.tar.gz should contain .tif files with the file pattern `L**_sr_band*.tif` This will correspond to datasets labeled "Collection 1 Higher-Level".


<a name="faqs"></a> Common problems/FAQs
========  
----  

Q: 	
 >I’m getting a “Permission denied error.”  How do I fix this?  

A:  
>	More often than not the issue is caused by a lack of permissions on the folder where the application is located.  Grant full access to the folder and its subfolders and files (this can be done by using the command “chmod -R 777 FOLDER_NAME”).  

---  

Q: 	
 >I'm getting a database error that resembles "fe_sendauth: no password supplied". How do I fix this?

A:  
>	This occurrs when the Data Cube system cannot locate a .datacube.conf file and one is not provided as a command line parameter. Ensure that a .datacube.conf file is found in your local user's home directory - ~/.datacube.conf

---  

Q: 	
 >I'm getting an error that resembles "FATAL: Peer authentication failed for user". How do I fix this?

A:  
>	This occurrs when PostgreSQL is incorrectly configured. Open your pg_hba.conf file and check that the local connection authenticates using the md5 method. If you are trying to connect to a remote database (e.g. using PGAdmin3 from a host machine when the Data Cube is on a guest VM) then a new entry will be required to allow non local connections. More details can be found on the [PostgreSQL documentation](https://www.postgresql.org/docs/9.5/static/auth-pg-hba-conf.html).

---  

Q: 	
 >Can the Data Cube be accessed from R/C++/IDL/etc.?

A:  
>This is not currently directly supported, the Data Cube is a Python based API. The base technology managing data access PostgreSQL, so theoretically the functionality can be ported to any language that can interact with the database. An additional option is just shelling out from those languages, accessing data using the Python API, then passing the result back to the other program/language.

---  

Q: 	
 >Does the Data Cube support *xyz* projection?

A:  
>Yes, the Data Cube either does support or can support with minimal changes any projection that rasterio can read or write to.

---  

Q: 	
 >I want to store more metadata that isn't mentioned in the documentation. Is this possible?

A:  
>This entire process is completely customizable. Users can configure exactly what metadata they want to capture for each dataset - we use the default for simplicities sake.

---  

Q: 	
 >Does ingestion handle preprocessing or does data need to be processed before ingestion?

A:  
>The ingestion process is simply a reprojection and resampling process for existing data. Data should be preprocessed before ingestion.

---  
