# CEOS Open Data Cube Notebooks Overview

This document provides an overview of the available notebooks in the `notebooks` directory.

Some directories contain `SAR` directories, which have notebooks that perform analyses with SAR (radar) data (e.g. Sentinel-1). If a notebook is not in a `SAR` directory, it uses data closer to the optical spectrum (e.g. Landsat 8, Sentinel-2).

* `animation`
  These are notebooks and applications that show how to create animations, like GIFs and videos.

* `compositing`  
  These are notebooks that explain how to composite data along time. For an introduction to compositing, see [compositing/Composites.ipynb](../notebooks/compositing/Composites.ipynb).

* `DCAL`  
  These are notebooks for the [Data Cube Applications Library](https://www.opendatacube.org/dcal), a catalogue of Data Cube applications - examples and explanations.

* `DEM`
  These are notebooks that show how to use digital elevation model (DEM) data, such as from the Shuttle Radar Topography Mission (SRTM).

* `feature_extraction`  
  These are notebooks that extract features from imagery. For example, isolating certain types of terrain.

* `general`  
  These are notebooks regarding generally useful techniques, like exporting the results of an analysis to files or masking data with shapefiles. There is also a notebook template, which is useful for structuring new notebooks.

* `IGARSS`  
  These are notebooks used in past IGARSS events. You may ignore them.

* `land_change`  
  These are notebooks that attempt to detect land change. Here, "land change" refers to changes in land class, such as vegetation becoming bare soil.

* `landslides`  
  These are notebooks for detecting land slides.

* `legacy`  
  These are old notebooks that you may ignore.

* `machine_learning`  
  These are notebooks that demonstrate how to employ machine learning in the context of the ODC.

* `SAR`  
  These are notebooks that explore SAR data outside the context of specific analyses.

* `test`
  These are notebooks that we use for testing.

* `training`  
  These are notebooks that have been used in past CEOS training sessions. You may ignore them.

* `UN_SDG`  
  These are notebooks that aim to satisfy reporting requirements for some United Nations (UN) Sustainable Development Goal (SDG) indicators. Currently there are notebooks for the indicators:
  * 6.6.1: Change in the extent of water-related ecosystems over time
  * 11.3.1: Ratio of land consumption rate to population growth rate
  * 15.3.1: Proportion of land that is degraded over total land area

* `urbanization`  
  These are notebooks that analyze urbanization.

* `vegetation`  
  These are notebooks that analyze vegetation. The `forests` subdirectory regards forest change and deforestation. The `phenology` subdirectory regards cyclical changes in vegetation, such as crop cycles.

* `water`  
  These are notebooks that analyze water. The `bathyetry` directory regards water depth measurements. The `coastline` directory regards detection and changes in coastlines. The `detection` directory regards detection of water. The `quality` directory regards water quality, such as the amount of suspended matter.

