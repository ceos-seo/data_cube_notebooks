# Operation Manual

This document will guide users through the process of operating the Jupyter Notebook server.

- [Introduction](#introduction)
- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation Process](#installation-process)
  - [Pre-start configuration](#pre-start-configuration)
  - [Starting Stopping Restarting](#starting-stopping-restarting)
  - [SSH to the notebook server](#ssh-to-the-notebook-server)
- [Access the notebooks](#access-the-notebooks)
- [Common problems/FAQs](#common-problemsfaqs)

## Introduction
-----

Jupyter notebooks are extremely useful as a learning tool and as an introductory use case for the Data Cube. Our Jupyter notebook examples include many of our algorithms and some basic introductory Data Cube tutorials.

The production environment is still in development, but a development environment - one that is suitable for personal use or very trusted users but not for public access - is available.

## System Requirements
-----

These are the base requirements for the notebooks:

- **Memory**: 8GiB
- **Local Storage**: 50GiB

## Prerequisites
-----

To run our Jupyter notebook examples, the following prerequisites must be complete:

- The [Environment Setup Guide](https://ceos-odc.readthedocs.io/en/latest/modules/install_docs/environment_setup.html) must have been completed.
- The [Open Data Cube Database Installation Guide](https://ceos-odc.readthedocs.io/en/latest/modules/install_docs/database_install.html)

Before we begin, note that multiple commands should not be copied and pasted to be run simultaneously unless you know it is acceptable in a given command block. Run each line individually.

## Installation Process
-----

>### Pre-start configuration

You can set the port that the notebooks will be available on with the `HOST_PORT` environment varaible in the `build/docker/dev/.env` file. By default, the notebooks will be available on port `8080` in the development environment.

The `ODC_DB_*` variables in the `build/docker/dev/.env` file are the connection credentials for the ODC database. The `ODC_DB_*` variables are set to match the default settings for the ODC database container, but if these settings were changed in the command for the `create-odc-db` target in the `Makefile` file, they will need to be changed here.

If you want to access data on S3, you will need to set the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` variables. By default, they are set to use the values of identically named environment variables. You should set these environment variables before starting the environment. Do not write these AWS credentials to the `build/docker/dev/.env` file directly.

The pre-start configuration for the production environment in `build/docker/prod` is very similar to the pre-start configuration for the development environment. A notable difference is that the default port for the production environment is `8081`.

When you have finished configuring these values, run `make create-odc-network create-odc-db`.

>### Starting Stopping Restarting

To start the development environment, run this command:
```
make dev-up
```

To stop the development environment, run this command:
```
make dev-down
```

To restart the development environment, run this command:
```
dev-restart
```

When starting or restarting in the future, you can use the `-no-build` versions of the `Makefile` targets if the dependencies have not changed (e.g. if only changes have been made to the notebooks). These include:
- dev-up-no-build
- dev-restart-no-build

The commands for the production environment in `build/docker/prod` are very similar to the commands for the development environment.

>### SSH to the notebook server

To connect to the development environment through a bash shell over SSH, run this command:
```
make dev-ssh
```

Once connected, run this command to activate the Python virtual environment:
```
source /env/bin/activate
```
This must be run for every connection with `make dev-ssh`.

In the development environment, you can also launch terminals through the interface in your web browser by clicking the `New` dropdown button and then the `Terminal` option. This will provide a terminal through a webpage in your browser.

## Access the notebooks
-----

In the development environment, you can connect to the notebooks on the host machine at `localhost:<HOST_PORT>`, where `<HOST_PORT>` is the value of the `HOST_PORT` environment variable specified in the `.env` file of the environment (i.e. `build/docker/dev/.env` or `build/docker/prod/.env`).

## Common problems/FAQs
-----

Q: 	
 > I’m having trouble connecting to my notebook server from another computer.

A:  
> There can be a variety of problems that can cause this issue.<br>
    <br>
    First make sure that the notebook server is running, then check (1) the IP or hostname and (2) the port number you are trying to access the server with.
    Be sure you are connecting to `localhost:<HOST_PORT>` if your browser is running on the same
    machine as the Jupyter server, and `<IP-or-hostname>:<HOST_PORT>` otherwise.<br>
    <br>
    Also check that there is no firewall blocking incoming or outgoing traffic on the `HOST_PORT` port.
