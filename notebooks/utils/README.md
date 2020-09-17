Data Cube Utilities
=================

This repository serves as a common module for our Jupyter examples and our UI.

This includes:
* A wrapper for the Data Cube Core API with some added functionality
* Water detection (WOfS)
* TSM
* Coastline Classification
* Coastal Change detection
* Continuous Change Detection (CCD) 
* Spectral Unmixing (Fractioanl Coverage) 
* Various plotting utilities
* Cloudfree mosaicking
* SLIP
* RGB display methods

This repository is set up as a submodule in our data_cube_ui and data_cube_notebooks repositories but can be used as a general utility module if desired.

Requirements
=================
* Full Data Cube installation with ingested data
* imagemagick (sudo apt-get install imagemagick)
* jupyter
* matplotlib
* scipy
* sklearn
* lcmap-pyccd=2017.08.18
* skimage
* seaborn
* folium

