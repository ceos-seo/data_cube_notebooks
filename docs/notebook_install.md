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

The full Data Cube Installation Guide must have been followed and completed before proceeding. This includes:
* You have a local user that is used to run the Data Cube commands/applications
* You have a database user that is used to connect to your 'datacube' database
* The Data Cube is installed and you have successfully run 'datacube system init'
* All code is checked out and you have a virtual environment in the correct directories: `~/Datacube/{data_cube_ui, data_cube_notebooks, datacube_env, agdc-v2}`

If these requirements are not met, please see the associated documentation.

You can view the notebooks without ingesting any data, but to be able to run notebooks with the sample ingested data, 
the ingestion guide must have been followed and completed. The steps include:
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
pip install jupyter matplotlib scipy sklearn lcmap-pyccd folium
```

<a name="configuration"></a> Configuration
========  

The first step is to generate a notebook configuration file. 
Ensure that you're in the virtual environment. If not, activate with `source ~/Datacube/datacube_env/bin/activate`.
Then run the following commands:
```
cd ~/Datacube/data_cube_notebooks
jupyter notebook --generate-config
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

Jupyter will create a configuration file in `~/.jupyter/jupyter_notebook_config.py`. 
Now set the password and edit the server details. Remember this password for future reference.

```
jupyter notebook password
```

Now edit the Jupyter notebook configuration file `~/.jupyter/jupyter_notebook_config.py` with your favorite text editor.

Edit the generated configuration file to include relevant details. 
You'll need to set the relevant entries in the file:

```
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.port = 8888
```

Save the file and then run the notebook server with the following command.
If this fails with a permissions error (`OSError: [...] Permission denied [...]`),
run the command `export XDG_RUNTIME_DIR=""`.

```
cd ~/Datacube/data_cube_notebooks
jupyter notebook
```

Open a web browser and navigate to the notebook URL. If you are running your browser from the same machine that is 
hosting the notebooks, you can use `localhost:{jupyter_port_num}` as the URL, where `jupyter_port_num` is the port number set for `c.NotebookApp.port` in the configuration file.
If you are connecting from another machine, you will need to enter the public IP address of the server in the URL (which can be determined by running the `ifconfig` command on the server) in place of `localhost`. 
You should be greeted with a password field. Enter the password from the previous step.

<a name="using_notebooks"></a> Using the Notebooks
========  

Now that your notebook server is running and the Data Cube is set up, you can run any of our examples.

Open the notebook titled 'Data_Cube_Test' and run through all of the cells using either the "Run" button on the toolbar or `Shift+Enter`.

You'll see that a connection to the Data Cube is established, some metadata is queried, and some data is loaded and plotted.

<a name="next_steps"></a> Next Steps
========  

Now that we have the notebook server setup and our examples running, you are able to play with many of our algorithms and become more familiar with the Data Cube and accessing metadata and data. The next step is to set up our web based user interface. You can find that documentation [here](./ui_install.md).

<a name="faqs"></a> Common problems/FAQs
========  
----  

Q: 	
 >I’m having trouble connecting to my notebook server from another computer.

A:  
>	There can be a variety of problems that can cause this issue.<br><br>
    First check the IP and port number in your notebook configuration file.
    Be sure you are connecting to `localhost:<port>` if your browser is running on the same
    machine as the Jupyter server, and `<IP>:<port>` otherwise. 
    Also check that your firewall is not blocking the port that it is running on.

---  
