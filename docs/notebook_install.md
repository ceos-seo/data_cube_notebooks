# CEOS Open Data Cube Notebooks Installation Guide

This document will guide users through the process of installing and configuring 
our Open Data Cube (ODC) Jupyter Notebook server.

## Contents

  * [Introduction](#introduction)
  * [System Requirements](#system_requirements)
  * [Prerequisites](#prerequisites)
  * [Installation Process](#installation_process)
    * [Pre-start configuration](#install_pre_start_config)
    * [Start, stop, or restart the notebook server](#install_start_stop_restart)
    * [SSH to the notebook server](#install_ssh)
  * [Access the notebooks](#connect)
  * [Common problems/FAQs](#faqs)

## <a name="introduction"></a> Introduction
-------  
Jupyter notebooks are extremely useful as a learning tool and as an introductory use case for the Data Cube. Our Jupyter notebook examples include many of our algorithms and some basic introductory Data Cube tutorials.

The production environment is still in development, but a development environment - one that is suitable for personal use or very trusted users but not for public access - is available.

## <a name="system_requirements"></a> System Requirements
-------

These are the base requirements for the notebooks:

* **Memory**: 8GiB
* **Local Storage**: 50GiB

## <a name="prerequisites"></a> Prerequisites
-------

To run our Jupyter notebook examples, the following prerequisites must be complete:

<!-- * An Open Data Cube database must be accessible. -->
* The [Docker Installation Guide](https://github.com/ceos-seo/data_cube_ui/blob/master/docs/docker_install.md) must have been completed.

Before we begin, note that multiple commands should not be copied and pasted to be run simultaneously unless you know it is acceptable in a given command block. Run each line individually.

## <a name="installation_process"></a> Installation Process
-------

>### <a name="install_pre_start_config"></a> Pre-start configuration
-------

You can set the port that the notebooks will be available on with the `HOST_PORT` environment varaible in the `docker/dev/.env` file. By default, the notebooks will be available on port `8080` in the development environment.

The `ODC_DB_*` variables in the `docker/dev/.env` file are the connection credentials for the ODC database. The `ODC_DB_*` variables are set to match the default settings for the ODC database container, but if these settings were changed in the command for the `create-odc-db` target in the `Makefile` file, they will need to be changed here.

If you want to access data on S3, you will need to set the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` variables. By default, they are set to use the values of identically named environment variables. You should set these environment variables before running the UI. Do not write these AWS credentials to the `docker/dev/.env` file directly.

>### <a name="install_start_stop_restart"></a> Start, stop, or restart the notebook server
-------

<a name="install_start"></a>To start the development environment, run this command:
```
make dev-up
```

<a name="install_stop"></a>To stop the development environment, run this command:
```
make dev-down
```

<a name="install_restart"></a>To restart the development environment, run this command:
```
dev-restart
```

When starting or restarting in the future, you can use the `-no-build` versions of the `Makefile` targets if the dependencies have not changed (e.g. if only changes have been made to the notebooks). These include:
* dev-up-no-build
* dev-restart-no-build

>### <a name="install_ssh"></a> SSH to the notebook server
-------

To connect to the development environment through a bash shell over SSH, run this command:
```
make dev-ssh
```

Once connected, run this command to activate the Python virtual environment:
```
source /env/bin/activate
```
This must be run for every connection with `make dev-ssh`.

In the development environment, you also can launch terminals by clicking the `New` dropdown button and then the `Terminal` option. This will provide a terminal through a webpage in your browser.

## <a name="connect"></a> Access the notebooks
-------

In the development environment, you can connect to the notebooks on the host machine at `localhost:<HOST_PORT>`, where `<HOST_PORT>` is the value of the `HOST_PORT` environment variable specified in `docker/dev/.env`.


## <a name="faqs"></a> Common problems/FAQs
-------

Q: 	
 >I’m having trouble connecting to my notebook server from another computer.

A:  
>	There can be a variety of problems that can cause this issue.<br>
    <br>
    First make sure that the notebook server is running, then check (1) the IP or hostname and (2) the port number you are trying to access the server with.
    Be sure you are connecting to `localhost:<HOST_PORT>` if your browser is running on the same
    machine as the Jupyter server, and `<IP-or-hostname>:<HOST_PORT>` otherwise.<br>
    <br>
    Also check that there is no firewall blocking incoming or outgoing traffic on the `HOST_PORT` port.

---  
