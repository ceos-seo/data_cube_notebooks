Data Cube Jupyter Notebook Installation Guide
=================

This document will guide users through the process of installing and configuring our Jupyter notebook Data Cube examples. In this guide, you will be required to install packages (Python and system level) and start a webserver.

Contents
=================

  * [Introduction](#introduction)
  * [Prerequisites](#prerequisites)
  * [Installation Process](#installation_process)
  * [Configuration](#configuration)
  * [Using the Notebooks](#using_notebooks)
  * [Next Steps](#next_steps)
  * [Common problems/FAQs](#faqs)

<a name="introduction"></a> Introduction
========  
Jupyter notebooks are extremely useful as a learning tool and as an introductory use case for the Data Cube. Our Jupyter notebook examples include many of our algorithms and some basic introductory Data Cube API use tutorials. After we have installed all of the required packages, we will verify that our Data Cube installation is working correctly.  

<a name="prerequisites"></a> Prerequisites
========  

To run our Jupyter notebook examples, the following prerequisites must be complete:

* The full Data Cube Installation Guide must have been followed and completed. This includes:
  * You have a local user that is used to run the Data Cube commands/applications
  * You have a database user that is used to connect to your 'datacube' database
  * The Data Cube is installed and you have successfully run 'datacube system init'
  * All code is checked out and you have a virtual environment in the correct directories: `~/Datacube/{data_cube_ui, data_cube_notebooks, datacube_env, agdc-v2}`
* The full Ingestion guide must have been followed and completed. This includes:
  * A sample Landsat 7 scene was downloaded and uncompressed in your `/datacube/original_data` directory
  * The ingestion process was completed for that sample Landsat 7 scene

<a name="installation_process"></a> Installation Process
========  

You will need to be in the virtual environment for this entire guide. If you have not done so, please run:

```
source ~/Datacube/datacube_env/bin/activate
```

Now install the following Python packages:

```
pip install jupyter
pip install matplotlib
pip install scipy
pip install sklearn
pip install lcmap-pyccd
pip install folium
```

We'll now need to manually download and install Basemap from source. Create a temporary directory in your home directory with the following commands and download the required .tar.gz

```
mkdir ~/temp
cd ~/temp
wget 'http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.7/basemap-1.0.7.tar.gz'
```

Now that we have the .tar.gz in the correct location, run the following commands to uncompress Basemap, install GEOS (included with Basemap) and install Basemap. This will produce a considerable amount of console output, but unless there are errors there is nothing to worry about.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'

#this uncompresses basemap and moves into the correct dir.
tar -xvf basemap-*
cd basemap-*

#now we need to install geos - included in basemap.
cd geos-*
export GEOS_DIR=~/
./configure --prefix=$GEOS_DIR
make
make install  

#now install basemap
cd ..
python setup.py install
```

Now that Basemap has been successfully installed, we can move on to configuring our notebook server.

<a name="configuration"></a> Configuration
========  

The first step is to generate a notebook configuration file. Run the following commands:

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
cd ~/Datacube/data_cube_notebooks
jupyter notebook --generate-config
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

Jupyter will create a configuration file in `~/.jupyter/jupyter_notebook_config.py`. Now set the password and edit the server details:

```
#enter a password - remember this for future reference.
jupyter notebook password

gedit ~/.jupyter/jupyter_notebook_config.py
```

Edit the generated configuration file to include relevant details - You'll need to find the relevant entries in the file:

```
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.port = 8888
```

Save the file and then run the notebook server with:

```
cd ~/Datacube/data_cube_notebooks
jupyter notebook
```

Open a web browser and go to localhost:8888 if you're on the server, or use 'ifconfig' to list your ip address and go to {ip}:8888. You should be greeted with a password field - enter the password from the previous step.

<a name="using_notebooks"></a> Using the Notebooks
========  

Now that your notebook server is running and the Data Cube is set up, you can run any of our examples.

Open the notebook titled 'Data_Cube_API_Demo' and run through all of the cells using either the button on the toolbar or CTRL+Enter.

You'll see that a connection to the Data Cube is established, some metadata is listed, and some data is loaded and plotted. Further down the page, you'll see that we are also demonstrating our API that includes getting acquisition dates, scene metadata, and data.

<a name="next_steps"></a> Next Steps
========  

Now that we have the notebook server setup and our examples running, you are able to play with many of our algorithms and become more familiar with the Data Cube and accessing metadata and data. The next step is to set up our web based user interface. You can find that documentation [here](./ui_install.md).

<a name="faqs"></a> Common problems/FAQs
========  
----  

Q: 	
 >I’m having trouble connecting to my notebook server from another computer.

A:  
>	There can be a variety of problems that can cause this issue. Check your notebook configuration file, your network settings, and your firewall settings.

---  
