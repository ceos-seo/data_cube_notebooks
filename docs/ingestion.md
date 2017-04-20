Data Cube Ingestion Guide
=================
This document will guide users through the process of indexing and ingesting ARD datasets into the Data Cube using the command line tool and required configuration files. This document contains information and snippets from the [official ODC user guide](http://datacube-core.readthedocs.io/en/latest/user/intro.html). This document describes the process for indexing and ingesting a Landsat 7 SR scene, but can be applied to indexing and ingesting any dataset. For the Installation, UI and Jupyter examples, please refer to the documentation in the associated repository.

Contents
=================
  * [Introduction](#introduction)
  * [Prerequisites](#prerequisites)
  * [Product Definitions](#product_definition)
  * [Generating Metadata](#generating_metadata)
  * [Indexing Datasets](#indexing_datasets)
  * [Ingesting Datasets](#ingesting_datasets)
  * [Brief Overview of Processes](#overview)
  * [Next Steps](#next_steps)
  * [Common problems/FAQs](#faqs)


<a name="introduction"></a> Introduction
=================
The indexing and ingestion workflow is required to add data to the Data Cube and provide access to the data via a Python API. Data is loaded by querying the Data Cube for data that matches certain metadata attributes, such as measurement name, product and platform type, geospatial and temporal extents.

**Read the official ODC documentation on [their readthedocs.io page](http://datacube-core.readthedocs.io/en/stable/ops/config.html)**

The ingestion workflow consists of: Adding a product definition to the Data Cube that describes the dataset attributes, generating required metadata for an ARD dataset, indexing the ARD dataset's metadata in the Data Cube, and running the ingestion process on indexed datasets. A brief description of these steps can be found below:
* **Adding a product definition**: Product definitions include a name, description, basic metadata, and a list of measurements with relevant properties in the dataset.
* **Generating required metadata**: A metadata .yaml file that describes a dataset is required for indexing in the Data Cube. This metadata file will include properties such as measurements with paths to the data, platform and sensor names, geospatial extents and projection, and acquisition dates. This is generally done using Python preparation scripts.
* **Indexing dataset metadata**: Indexing a dataset involves recording the content of the metadata file in the database. This allows access to the metadata via the Python API and for programmatic loading of data based on metadata.
* **Ingesting indexed datasets**: The ingestion process defines a mapping between a source dataset and a dataset with more desirable properties. A new product definition will be added to the Data Cube with the properties defined in the ingestion configuration file and datasets that match the provided criteria will be modified according to the new product definition and written to disk in the new format. Each modified dataset (or dataset tile) is indexed in the Data Cube.

<a name="prerequisites"></a> Prerequisites
=================
To index and ingest data into the Data Cube, the following prerequisites must be complete:
* The full Data Cube Installation Guide must have been followed and completed. This includes:
  * You have a local user that is used to run the Data Cube commands/applications
  * You have a database user that is used to connect to your 'datacube' database
  * The Data Cube is installed and you have successfully run 'datacube system init'
  * All code is checked out and you have a virtual environment in the correct directories: ~/Datacube/{data_cube_ui, data_cube_notebooks, datacube_env, agdc-v2}
* This guide will use a Landsat 7 SR product as an example. Please download a Landsat SR product from [Earth Explorer](https://earthexplorer.usgs.gov/). Please ensure that the dataset you download is an SR product - the L\*.tar.gz should contain .tif files with the file pattern L\*\*\_sr_band\*.tif This will correspond to datasets labeled "Collection 1 Higher-Level", or the pre-collection datasets if you have an older download. Move this dataset into the directory '/datacube/original_data/' so that the path looks like '/datacube/original_data/L*.tar.gz'

If you have not yet completed our Data Cube Installation Guide, please do so before continuing.

<a name="product_definition"></a> Product Definitions
========  

Product definitions define the attributes for entire datasets. These attributes include:
* A short name for the dataset
* A short description of what the dataset is
* A metadata type - more on this later
* Product metadata, including platform, instrument, product type, etc.
* Any number of measurements that are associated with the dataset and their attributes.

**Read the official ODC documentation on product definitions on [their readthedocs.io page](http://datacube-core.readthedocs.io/en/stable/ops/config.html)**

We will be using our Landsat 7 SR product definition as an example - open the file located at '~/Datacube/agdc-v2/ingest/dataset_types/ls7_sr_scenes_agdc.yaml' or view the full file [here](https://github.com/ceos-seo/agdc-v2/blob/develop/ingest/dataset_types/ls7_sr_scenes_agdc.yaml). We will go through this file and describe each attribute. The schema for the dataset type .yaml files can be found [here](https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/dataset-type-schema.yaml). This outlines the required fields as well as the datatypes and what fields are allowed. This schema is used to validate any new product definitions that are added.

	name: ls7_ledaps_scene
	description: Landsat 7 LEDAPS 30 metre. Will be used for all ls7 scenes, which are then split into utms on the ingestion config level.
	metadata_type: eo

The name is a short name for the dataset - we generally stick with an all lower case, underscore seperated string. This is the name that will be used to access datasets of this type programatically and during ingestion.

An optional element, 'storage', can be included as well. This can be seen in the [dataset type schema](https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/dataset-type-schema.yaml) - This can be included to describe the format of the data on disk, including the CRS, resolution, and driver. These are used in the ingestion process to specify projection/tiling/file type, but for now it is completely optional.  

Description is just a short description of what each dataset type encompasses. In this case, its describing Landsat 7 LEDAPS SR scenes.

The metadata type refers to another .yaml schema and describes what metadata will be collected during the [Generating Metadata](#generating_metadata) section. You can create your own metadata type if custom fields or metadata sets are desired, but we will stick with the default metadata type for this example.

The metadata type schema can be found [here](https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/metadata-type-schema.yaml), with the default metadata type ('eo') being found [here](https://github.com/opendatacube/datacube-core/blob/develop/datacube/index/default-metadata-types.yaml). You can see in the default metadata type that the name is 'eo', corresponding to our dataset type. Additionally, you'll see that the dataset field in that file includes an id, creation date, measurements, etc. These fields correspond with what needs to be generated in the next step and the structure of the .yaml/.json file - for now, just note that each product definition must be associated with a metadata type.

Next in the file is the metadata field:

	metadata:
    	platform:
    	    code: LANDSAT_7
    	instrument:
    	    name: ETM
    	product_type: ledaps
    	format:
    	    name: GeoTiff

The metadata as defined by the product definition schema [here](https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/dataset-type-schema.yaml) is an object - any number of fields and any schemas can be put here, as long as they are defined in the metadata type definition. If you open the [default metadata type file](https://github.com/opendatacube/datacube-core/blob/develop/datacube/index/default-metadata-types.yaml), you'll see that the format is expected to be nexted in format -> name, the product type is just in product type, etc. This is described using an 'offset' from the document root. This metadata is used to 'match' datasets to their appropriate product type, so the script in the next section that generates the metadata files must produce the same platform and product type as what is listed above.

The last element (or list of elements) in the product definition is the measurement, seen below.

	- name: 'sr_band7'
	  aliases: [band_7, swir2]
	  dtype: int16
	  nodata: -9999
	  units: '1'
	  spectral_definition:
	      wavelength: [2000, 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2018, 2020, 2022, 2024, 2026, 2028, 2030, 2032, 2034, 2035, 2037, 2039, 2041, 2043, 2045, 2047, 2049, 2051, 2052, 2054, 2056, 2058, 2060, 2062, 2064, 2066, 2067, 2069, 2071, 2073, 2075, 2077, 2079, 2081, 2083, 2085, 2086, 2088, 2090, 2092, 2094, 2096, 2099, 2100, 2102, 2104, 2106, 2108, 2110, 2112, 2114, 2116, 2117, 2119, 2121, 2123, 2125, 2127, 2129, 2131, 2133, 2135, 2136, 2138, 2140, 2142, 2144, 2146, 2148, 2150, 2151, 2153, 2155, 2157, 2159, 2161, 2163, 2165, 2166, 2168, 2170, 2172, 2174, 2176, 2178, 2180, 2182, 2183, 2185, 2187, 2189, 2191, 2193, 2195, 2197, 2199, 2201, 2203, 2205, 2207, 2209, 2210, 2212, 2214, 2216, 2218, 2220, 2222, 2223, 2226, 2227, 2229, 2231, 2233, 2235, 2237, 2239, 2241, 2242, 2244, 2246, 2248, 2250, 2252, 2254, 2256, 2258, 2259, 2261, 2263, 2265, 2267, 2269, 2271, 2273, 2274, 2276, 2278, 2280, 2282, 2284, 2286, 2288, 2290, 2292, 2293, 2295, 2297, 2299, 2301, 2303, 2305, 2307, 2309, 2310, 2312, 2314, 2316, 2318, 2320, 2322, 2323, 2325, 2327, 2329, 2331, 2333, 2335, 2337, 2339, 2340, 2342, 2344, 2346, 2348, 2350, 2352, 2354, 2355, 2357, 2359, 2361, 2363, 2365, 2367, 2369, 2371, 2373, 2374, 2376, 2378, 2380, 2382, 2384, 2386, 2390, 2395, 2400]
	      response: [0.0, 0.003, -0.002, 0.003, -0.001, 0.0, 0.004, -0.004, 0.002, 0.002, 0.002, 0.012, 0.009, 0.007, 0.011, 0.02, 0.017, 0.03, 0.035, 0.037, 0.044, 0.051, 0.065, 0.08, 0.088, 0.102, 0.133, 0.165, 0.188, 0.22, 0.264, 0.316, 0.367, 0.421, 0.484, 0.554, 0.59, 0.67, 0.683, 0.73, 0.756, 0.767, 0.794, 0.774, 0.776, 0.789, 0.775, 0.784, 0.778, 0.768, 0.762, 0.761, 0.775, 0.775, 0.764, 0.784, 0.792, 0.814, 0.794, 0.825, 0.817, 0.806, 0.819, 0.821, 0.852, 0.832, 0.836, 0.85, 0.855, 0.862, 0.853, 0.871, 0.848, 0.882, 0.875, 0.86, 0.856, 0.887, 0.85, 0.872, 0.879, 0.857, 0.865, 0.867, 0.871, 0.882, 0.87, 0.869, 0.873, 0.877, 0.868, 0.88, 0.877, 0.87, 0.878, 0.88, 0.868, 0.881, 0.87, 0.856, 0.863, 0.863, 0.857, 0.844, 0.859, 0.857, 0.852, 0.866, 0.868, 0.856, 0.856, 0.847, 0.861, 0.862, 0.84, 0.856, 0.838, 0.856, 0.837, 0.842, 0.826, 0.844, 0.827, 0.842, 0.822, 0.843, 0.823, 0.854, 0.839, 0.853, 0.854, 0.865, 0.873, 0.869, 0.865, 0.893, 0.89, 0.89, 0.906, 0.924, 0.92, 0.922, 0.939, 0.916, 0.94, 0.93, 0.942, 0.957, 0.954, 0.951, 0.954, 0.966, 0.975, 0.985, 0.971, 0.973, 0.97, 0.993, 0.996, 0.983, 0.972, 1.0, 0.998, 0.971, 0.968, 0.967, 0.962, 0.949, 0.923, 0.929, 0.917, 0.934, 0.903, 0.926, 0.916, 0.942, 0.924, 0.92, 0.863, 0.824, 0.775, 0.684, 0.583, 0.48, 0.378, 0.275, 0.233, 0.171, 0.131, 0.111, 0.081, 0.069, 0.046, 0.029, 0.038, -0.002, 0.029, 0.016, 0.009, 0.017, 0.003, 0.015, 0.0, -0.009, 0.007, 0.0, 0.0, 0.0]

The full measurement schema with all possible formats can be found in the [dataset type schema](https://github.com/opendatacube/datacube-core/blob/develop/datacube/model/schema/dataset-type-schema.yaml). The example above includes the optional spectral definition, but flag definitions are also allowed. The only properties that are required are **name, dtype, nodata, and units**. If you were to create a product definition for Sentinel 1 data, you would use the data guide to find out what bands are available, the datatype of those bands, what the no data value is, and the units and enumerate them here.

There should be one measurement entry for each expected band in the dataset.

Once your product definition has all required information, you add it to the Data Cube. For our Landsat 7 example, this is done with the following command:

	datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/ls7_sr_scenes_agdc.yaml

This command should be run from within the virtual environment. This will validate your product definition and, if valid, will index it in the Data Cube. The expected output should look like below:

	2017-04-19 11:23:39,861 21121 datacube INFO Running datacube command: /home/localuser/Datacube/datacube_env/bin/datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/ls7_sr_scenes_agdc.yaml
	2017-04-19 11:23:40,184 21121 datacube.index.postgres._dynamic INFO Creating index: dix_ls7_ledaps_scene_lat_lon_time
	2017-04-19 11:23:40,194 21121 datacube.index.postgres._dynamic INFO Creating index: dix_ls7_ledaps_scene_time_lat_lon
	Added "ls7_ledaps_scene"_

The 'Added \*' statement should read that it has added the name defined within the product definition.

If you open pgAdmin3 and examine the data in the dataset_type table, you'll see that there is now a row for the added product with all associated metadata. With the product definition added to the Data Cube, the next step is generating the required metadata to add a dataset.


<a name="generating_metadata"></a> Generating Metadata
========  

Before starting this step, you'll need to make sure that you have your Landsat 7 scene downloaded (.tar.gz format) in the '/datacube/original_data' directory.

Uncompress this scene into the default location with the following commands:

	#Replace L* with your actual scene Id - if your scene id is LE71240522000128-SC20170217181717, your command will be tar -xzf LE71240522000128-SC20170217181717.tar.gz LE71240522000128-SC20170217181717
	mkdir L*/
	tar -xzf L*.tar.gz -C L*/

This will result in a directory with the same name as your archive file with the contents of the archive extracted to the directory. There are scripted versions of this process in our checkout of the agdc-v2 codebase in '~/Datacube/agdc-v2/ingest'

Now that we have the data extracted into a named directory, we can generate the required metadata .yaml file. This is done with Python scripts found in '~/Datacube/agdc-v2/ingest/prepare_scripts/\*'. There are a variety of scripts provided, including USGS Landsat, Sentinel 1, and ALOS.

**Read the official ODC documentation on dataset definitions on [their readthedocs.io page](http://datacube-core.readthedocs.io/en/stable/ops/config.html)**

These scripts are responsible for creating a .yaml metadata file that contains all required metadata fields. The required and available metadata fields are defined in the metadata type definition that is associated with the product definition. In the previous section, we added a product definition with a metadata type of 'eo', the default metadata type. We can view the default metadata types at [this url](https://github.com/opendatacube/datacube-core/blob/develop/datacube/index/default-metadata-types.yaml). In this file, you'll see the properties that the preparation scripts need to produce and the structure of the file. The fields in the 'search_fields' section list the fields that can be used to query the Data Cube for data while the fields not in that section are just general metadata. For instance:

> The 'id' field is listed as "id: ['id']", so the id metadata field will be found in the metadata .yaml file in the root of the document

> The 'measurements' field is described in comments as a dict with certain attributes with an offset of ['image', 'bands'], so the measurements will be a dictionary keyed by measurement name found in the document as image: bands: {key: val, ...}

> platform, product type, lat, and lon are all search fields, so the user will be able to select storage units based on these attributes with the API.

Each of the fields defined in the metadata type reference should be filled in the dataset metadata .yaml file. Please note that only the 'search fields' are required, but there should be as much metadata collected as possible. We are also able to add metadata to the document that is not listed in the metadata type, everything will be stored in the database. We will verify that this is correct after generating the .yaml file for our Landsat 7 scene.

Since we are processing a Landsat scene, we'll use the script titled 'usgslsprepare.py'. Run this script on your uncompressed scene with the following command (please note that you should run this command on the **directory**):

	#if you are not already in the virtual environment, please activate that now with 'source ~/Datacube/datacube_env/bin/activate'
	python usgslsprepare.py /datacube/original_data/L*/

These scripts can run on a single directory of a list of directories specified with a wildcard (\*). The output should resemble what is shown below:

	2017-04-19 12:30:25,134 INFO Processing /datacube/original_data/LE71240522000128-SC20170217181717
	2017-04-19 12:30:25,141 INFO Writing /datacube/original_data/LE71240522000128-SC20170217181717/agdc-metadata.yaml

You'll see that the script has created a .yaml file titled agdc-metadata.yaml in the same directory as your GeoTiff data files.

Opening this metadata .yaml file, you'll see that is contains all of the fields listed in the 'eo' metadata definition. The nested fields will also correspond to the 'offset' or listed fields in the metadata definition.

```
acquisition:
  aos: '2000-05-07 02:59:38'
  groundstation: {code: SGS}
  los: '2000-05-07 03:00:02'
creation_dt: 2000-05-08 00:00:00
extent:
  center_dt: '2000-05-07 02:59:50'
  coord:
    ll: {lat: 10.641493156929936, lon: 106.75870991242047}
    lr: {lat: 10.622400004728664, lon: 108.88195125452104}
    ul: {lat: 12.515617895333568, lon: 106.77046427359687}
    ur: {lat: 12.493065194188315, lon: 108.90783262592694}
  from_dt: '2000-05-07 02:59:38'
  to_dt: '2000-05-07 03:00:02'
format: {name: GeoTiff}
grid_spatial:
  projection:
    geo_ref_points:
      ll: {x: 692385.0, y: 1176885.0}
      lr: {x: 924915.0, y: 1176885.0}
      ul: {x: 692385.0, y: 1384215.0}
      ur: {x: 924915.0, y: 1384215.0}
    spatial_reference: PROJCS["WGS 84 / UTM zone 48N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS
      84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",105],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32648"]]
id: 708d0d1b-8832-460b-b79e-67694875e101
image:
  bands:
    '1': {path: LE71240522000128SGS00_b1.tif}
    '2': {path: LE71240522000128SGS00_b2.tif}
    '3': {path: LE71240522000128SGS00_b3.tif}
    '4': {path: LE71240522000128SGS00_b4.tif}
    '5': {path: LE71240522000128SGS00_b5.tif}
    '61': {path: LE71240522000128SGS00_b61.tif}
    '62': {path: LE71240522000128SGS00_b62.tif}
    '7': {path: LE71240522000128SGS00_b7.tif}
    '8': {path: LE71240522000128SGS00_b8.tif}
    cfmask: {path: LE71240522000128SGS00_cfmask.tif}
    cfmask_conf: {path: LE71240522000128SGS00_cfmask_conf.tif}
    sr_adjacent_cloud_qa: {path: LE71240522000128SGS00_sr_adjacent_cloud_qa.tif}
    sr_atmos_opacity: {path: LE71240522000128SGS00_sr_atmos_opacity.tif}
    sr_band1: {path: LE71240522000128SGS00_sr_band1.tif}
    sr_band2: {path: LE71240522000128SGS00_sr_band2.tif}
    sr_band3: {path: LE71240522000128SGS00_sr_band3.tif}
    sr_band4: {path: LE71240522000128SGS00_sr_band4.tif}
    sr_band5: {path: LE71240522000128SGS00_sr_band5.tif}
    sr_band7: {path: LE71240522000128SGS00_sr_band7.tif}
    sr_cloud_qa: {path: LE71240522000128SGS00_sr_cloud_qa.tif}
    sr_cloud_shadow_qa: {path: LE71240522000128SGS00_sr_cloud_shadow_qa.tif}
    sr_ddv_qa: {path: LE71240522000128SGS00_sr_ddv_qa.tif}
    sr_fill_qa: {path: LE71240522000128SGS00_sr_fill_qa.tif}
    sr_land_water_qa: {path: LE71240522000128SGS00_sr_land_water_qa.tif}
    sr_snow_qa: {path: LE71240522000128SGS00_sr_snow_qa.tif}
  satellite_ref_point_end: {x: 124, y: 52}
  satellite_ref_point_start: {x: 124, y: 52}
instrument: {name: ETM}
lineage:
  source_datasets: {}
platform: {code: LANDSAT_7}
processing_level: sr_refl
product_type: LEDAPS
```

If you are looking to create a new script to process a dataset that we don't have a script for already, the easiest path is to use an existing script as a template and change only what is required to process your new dataset.

<a name="indexing_datasets"></a> Indexing Datasets
========  

Indexing Datasets in the Database
--------

Now that you have a product definition added and a agdc-metadata.yaml file generated for your scene, it is now time to index the dataset and associate it with the product definition. This is done with a datacube command from the CLI. Please note that indexing the dataset in the database creates an absolute reference to the path on disk - you cannot move the dataset on disk after indexing or it won't be found and will create problems.

Run the 'datacube dataset add' command on the directory or metadata .yaml file generated for the dataset. This command will load the .yaml metadata file and create a Dataset class object from the contents. It will then try to match the dataset to a product definition using the provided metadata.

```
#ensure that you are doing this from within the virtual environment. If not, activate it with 'source ~/Datacube/datacube_env/bin/activate'
datacube -v dataset add /datacube/original_data/LE71240522000128-SC20170217181717
#or
#datacube -v dataset add /datacube/original_data/LE71240522000128-SC20170217181717/agdc-metadata.yaml
```

The resulting console output will resemble the output below:

```
Indexing datasets  [####################################]  100%2017-04-19 13:45:16,405 22577 datacube-dataset INFO Matched Dataset <id=708d0d1b-8832-460b-b79e-67694875e101 type=ls7_ledaps_scene location=/datacube/original_data/LE71240522000128-SC20170217181717/agdc-metadata.yaml>
2017-04-19 13:45:16,406 22577 datacube.index._datasets INFO Indexing 708d0d1b-8832-460b-b79e-67694875e101
```

Please note that you are able to run these 'datacube' command line tools on wildcard inputs, e.g. 'datacube dataset add /datacube/original_data/LE*/\*.yaml' to batch process directories.

Now that the dataset has been added, you can open up pgAdmin3 and view the data in the 'datasets' table - you'll notice that there is now an entry for the dataset you've just added that includes the id, a reference to the metadata definition corresponding to a primary key in the 'metadata_type' table and a reference to the dataset type corresponding to a primary key in the 'dataset_type' table. If you look at the 'metadata_type' and 'dataset_type' tables with the listed ids, you'll see the full metadata and dataset type definitions from the previous steps.

***Since dataset references in the database use absolute paths, please ensure that your datasets are organized and in a location that you want to keep before indexing***

Testing the Indexed Data
--------

Now that we have a single dataset indexed, we can test out the Data Cube API access. This example will involve loading the entire dataset that we've just indexed into an in-memory array in the form of an xArray dataset. To simplify things, we can just use a Python console:

```
#first, start a Python console
python

#import the datacube
import datacube

#this will create a new Datacube instance - leaving out any configuration files
#without entering a config parameter, the Data Cube will use the .datacube.conf in the default location.
#this in in your home directory '~/.datacube.conf'
dc = datacube.Datacube()

print(dc)

#now, query the data cube for some data using the name of the product type
#if you added a different dataset type, use that here.
data_full = dc.load(product='ls7_ledaps_scene')

#this should produce an error! since we didn't specify a crs or resolution in the product definition, we need to enter one now. The Data Cube will load the data in the entered projection and resolution - we can reproject any dataset to any resolution or projection when it is loaded, not only during ingestion.

#resolution is in the format of y, x - y is negative.
data_full = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027))

#since our Landsat scene is in a UTM based projection at 30m resolution, it will need to be converted to EPSG:4326 with a fractional degree resolution. Here, we use .00027 as a rough estimation of 30m at a latitude of 0.

print(data_full)

#You'll see that we've got access to all the sr_bands and a variety of qa bands.
#now, we'll demonstrate some query options.

#all of the search fields are listed in the 'eo' metadata definition.
#if we only want to load a small subset of our indexed data:

#replace latitude and longitude ranges with whatever you want - we're now loading in a single 0.5 degree square. Note that all lat/lon query parameters are in latitude/longitude WGS84 coordinates.
#using the printed data_full, look at the listing for latitude and longitude. The first values there is the upper left corner. in our case, the upper left corner is at 12.52 lat, 106.8 lon.
data_partial = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027), latitude=(12, 12.5), longitude=(107, 107.5))

print(data_partial)

#You'll see that the data is now a small subset of the original set. This works with time as well - if we have multiple times over a single region indexed, we can load them all at once and it will be indexed over latitude, longitude, and time.

#we can also load a small subset of data at once by measurement to have a smaller memory footprint.

data_partial = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027), latitude=(12, 12.5), longitude=(107, 107.5), measurements=['sr_band1', 'cfmask'])

print(data_partial)
```

The output of our script can be seen below - feel free to copy and paste the commands one at a time and to take some time to familiarize yourself with the commands.

```
python
Python 3.5.2 (default, Nov 17 2016, 17:05:23)
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
>>> #import the datacube
... import datacube
>>>
>>> #this will create a new Datacube instance - leaving out any configuration files
... #without entering a config parameter, the Data Cube will use the .datacube.conf in the default location.
... #this in in your home directory '~/.datacube.conf'
... dc = datacube.Datacube()
>>>
>>> print(dc)
Datacube<index=Index<db=PostgresDb<engine=Engine(postgresql://dc_user:***@:5432/datacube)>>>
>>>
>>> #now, query the data cube for some data using the name of the product type
... #if you added a different dataset type, use that here.
... data_full = dc.load(product='ls7_ledaps_scene')
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
  File "/home/localuser/Datacube/agdc-v2/datacube/api/core.py", line 305, in load
    raise RuntimeError("Product has no default CRS. Must specify 'output_crs' and 'resolution'")
RuntimeError: Product has no default CRS. Must specify 'output_crs' and 'resolution'
>>>
>>> #this should produce an error! since we didn't specify a crs or resolution in the product definition, we need to enter one now. The Data Cube will load the data in the entered projection and resolution - we can reproject any dataset to any resolution or projection when it is loaded, not only during ingestion.
...
>>> #resolution is in the format of y, x - y is negative.
... data_full = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027))
>>>
>>> #since our Landsat scene is in a UTM based projection at 30m resolution, it will need to be converted to EPSG:4326 with a fractional degree resolution. Here, we use .00027 as a rough estimation of 30m at a latitude of 0.
...
>>> print(data_full)
<xarray.Dataset>
Dimensions:               (latitude: 7013, longitude: 7961, time: 1)
Coordinates:
  * time                  (time) datetime64[ns] 2000-05-07T02:59:50
  * latitude              (latitude) float64 12.52 12.52 12.52 12.51 12.51 ...
  * longitude             (longitude) float64 106.8 106.8 106.8 106.8 106.8 ...
Data variables:
    sr_band1              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band2              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band3              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band4              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band5              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band7              (time, latitude, longitude) int16 -9999 -9999 ...
    cfmask                (time, latitude, longitude) uint8 255 255 255 255 ...
    cfmask_conf           (time, latitude, longitude) uint8 255 255 255 255 ...
    sr_adjacent_cloud_qa  (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_atmos_opacity      (time, latitude, longitude) int16 -9999 -9999 ...
    sr_cloud_qa           (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_cloud_shadow_qa    (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_ddv_qa             (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_fill_qa            (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_land_water_qa      (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_snow_qa            (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
Attributes:
    crs:      EPSG:4326
>>>
>>> #You'll see that we've got access to all the sr_bands and a variety of qa bands.
... #now, we'll demonstrate some query options.
...
>>> #all of the search fields are listed in the 'eo' metadata definition.
... #if we only want to load a small subset of our indexed data:
...
>>> #replace latitude and longitude ranges with whatever you want - we're now loading in a single 0.5 degree square. Note that all lat/lon query parameters are in latitude/longitude WGS84 coordinates.
... #using the printed data_full, look at the listing for latitude and longitude. The first values there is the upper left corner. in our case, the upper left corner is at 12.52 lat, 106.8 lon.
... data_partial = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027), latitude=(12, 12.5), longitude=(107, 107.5))
>>>
>>> print(data_partial)
<xarray.Dataset>
Dimensions:               (latitude: 1853, longitude: 1853, time: 1)
Coordinates:
  * time                  (time) datetime64[ns] 2000-05-07T02:59:50
  * latitude              (latitude) float64 12.5 12.5 12.5 12.5 12.5 12.5 ...
  * longitude             (longitude) float64 107.0 107.0 107.0 107.0 107.0 ...
Data variables:
    sr_band1              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band2              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band3              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band4              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band5              (time, latitude, longitude) int16 -9999 -9999 ...
    sr_band7              (time, latitude, longitude) int16 -9999 -9999 ...
    cfmask                (time, latitude, longitude) uint8 255 255 255 255 ...
    cfmask_conf           (time, latitude, longitude) uint8 255 255 255 255 ...
    sr_adjacent_cloud_qa  (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_atmos_opacity      (time, latitude, longitude) int16 -9999 -9999 ...
    sr_cloud_qa           (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_cloud_shadow_qa    (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_ddv_qa             (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_fill_qa            (time, latitude, longitude) uint8 255 255 255 255 ...
    sr_land_water_qa      (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
    sr_snow_qa            (time, latitude, longitude) uint8 0 0 0 0 0 0 0 0 ...
Attributes:
    crs:      EPSG:4326
>>>
>>> #You'll see that the data is now a small subset of the original set. This works with time as well - if we have multiple times over a single region indexed, we can load them all at once and it will be indexed over latitude, longitude, and time.
...
>>> #we can also load a small subset of data at once by measurement to have a smaller memory footprint.
...
>>> data_partial = dc.load(product='ls7_ledaps_scene', output_crs='EPSG:4326', resolution=(-0.00027,0.00027), latitude=(12, 12.5), longitude=(107, 107.5), measurements=['sr_band1', 'cfmask'])
>>>
>>> print(data_partial)
<xarray.Dataset>
Dimensions:    (latitude: 1853, longitude: 1853, time: 1)
Coordinates:
  * time       (time) datetime64[ns] 2000-05-07T02:59:50
  * latitude   (latitude) float64 12.5 12.5 12.5 12.5 12.5 12.5 12.5 12.5 ...
  * longitude  (longitude) float64 107.0 107.0 107.0 107.0 107.0 107.0 107.0 ...
Data variables:
    sr_band1   (time, latitude, longitude) int16 -9999 -9999 -9999 -9999 ...
    cfmask     (time, latitude, longitude) uint8 255 255 255 255 255 255 255 ...
Attributes:
    crs:      EPSG:4326

```

The Data Cube loads data into xArray datasets - [documentation found here](http://xarray.pydata.org/en/stable/index.html). All normal numpy and xArray functions can be applied to Data Cube data.

Now that we have demonstrated the indexing process and data access, we can ingest the dataset.

<a name="ingesting_datasets"></a> Ingesting Datasets
========  

With a newly indexed dataset, the next step is ingestion.

Ingestion is the process of transforming original datasets into more accessible format that can be used by the Data Cube. Like the previous steps, ingestion relies on the use of a .yaml configuration file that specifies all of the input and output details for the data. The ingestion configuration file contains all of the information required for a product definition - it uses the information to create a new product definition and index it in the Data Cube. Next, indexed source datasets that fit the criteria are identified, tiled, reprojected, and resampled (if required) and written to disk as NetCDF storage units. The required metadata is generated and the newly created datasets are indexed (added) to the Data Cube.

The ingestion configuration file is essentially defining a transformation between the source and the output data - you can define attributes such as resolution, projection, tile sizes, bounds, and measurements, along with file type and other metadata in a configuration file. When you run the ingestion process, the Data Cube determines what data fits the input data attributes by product type and bounds, applies the defined transformation, and saves the result to disk and in the database. This process is generally done when the data is in a file format not optimized for random access such as GeoTiff - NetCDF is the preferred file type.

**Read the official ODC documentation on ingestion configuration files on [their readthedocs.io page](http://datacube-core.readthedocs.io/en/stable/ops/config.html)**

**Please note that you will need to create a new ingestion configuration file to match the scene bounds that you have downloaded. If you do not want to do that, delete the ingestion bounds section from the configuration file we are using as an example - your product will be 'ls7_ledaps_vietnam'**

In this section we will go through an example Landsat 7 ingestion configuration and then ingest our sample dataset.

Open the ingestion configuration file located in '~/Datacube/agdc-v2/ingest/ingestion_configs/ls7_sr_scenes_wgs84_vietnam.yaml', or view [the page on GitHub](https://github.com/ceos-seo/agdc-v2/blob/develop/ingest/ingestion_configs/ls7_sr_scenes_wgs84_vietnam.yaml)

The first two lines in the file are:

```
source_type: ls7_ledaps_scene
output_type: ls7_ledaps_vietnam
```

This tells the ingestion process to match the input parameters to datasets that are associated with the 'ls7_ledaps_scene' product definition and to create a new product definition named 'ls7_ledaps_vietnam'.

Next, there are two parameters that specify the location and file path templates for the newly created storage units:

```
location: '/datacube/ingested_data'
file_path_template: 'LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_{tile_index[0]}_{tile_index[1]}_{start_time}.nc'
```

This specifies that the base path for the ingested data is '/datacube/ingested_data' - this was created previously and should have 777 permissions.
> 'file_path_template' describes the rest of the storage unit path - the directory structure 'LS7_ETM_LEDAPS/Vietnam' will be created and populated with storage units.

> Files named 'LS7_ETM_LEDAPS_4326_{tile_index[0]}_{tile_index[1]}_{start_time}.nc' will be created in the above directory. The bracketed parameters are filled in by the ingestion process.

The next elements are global metadata elements, as seen below.

```
global_attributes:
  title: CEOS Data Cube Landsat Surface Reflectance
  summary: Landsat 7 Enhanced Thematic Mapper Plus Analysis Ready data prepared by NASA on behalf of CEOS.
  source: Surface reflectance from LEDAPS
  institution: CEOS
  instrument: ETM
  cdm_data_type: Grid
  keywords: AU/GA,NASA/GSFC/SED/ESD/LANDSAT,REFLECTANCE,ETM+,TM,OLI,EARTH SCIENCE
  keywords_vocabulary: GCMD
  platform: LANDSAT-7
  processing_level: L2
  product_version: '2.0.0'
  product_suite: USGS Landsat
  project: CEOS
  coverage_content_type: physicalMeasurement
  references: http://dx.doi.org/10.3334/ORNLDAAC/1146
  license: https://creativecommons.org/licenses/by/4.0/
  naming_authority: gov.usgs
acknowledgment: Landsat data is provided by the United States Geological Survey (USGS).
```

The next field group defines what subset (if any) of the source dataset that should be used for the ingestion process. If the entire source dataset should be ingested, then this can be left out. In the example below, we are restricting the ingestion process to datasets that match the input dataset type that fall between those bounds. These numbers should be in latitude and longitude WGS84 coordinates.

```
ingestion_bounds:
  left: 100.0
  bottom: 5.0
  right: 115.0
  top: 20.0
```

The storage fields specify a few things: Projection, resolution, tile size, chunk size, etc.

```
storage:
  driver: NetCDF CF

  crs: EPSG:4326
  tile_size:
          longitude: 0.943231048326
          latitude:  0.943231048326
  resolution:
          longitude: 0.000269494585236
          latitude: -0.000269494585236
  chunking:
      longitude: 200
      latitude: 200
      time: 1
  dimension_order: ['time', 'latitude', 'longitude']
```
Some notes on these inputs can be found below:
* NetCDF CF is the only current storage driver.
* The CRS is user defined - any transverse mercator, sinusoidal, or albers conic equal area projections are supported.
* Chunking and dimension order are internal to the NetCDF storage units - the chunking parameter can have an effect on performance based on the use case, but we generally leave it alone

**Important notes**
* Resolution specifies the x/y or latitude/longitude resolution in the **units of the crs setting** - if the units of the crs are degrees (e.g. EPSG:4326), then latitude/longitude should be used here. If x/y are used (e.g. Transverse mercator projections, UTM based etc.) then these should read x and y instead.
* The tile size refers to the tiling of the source datasets - in the above example, ~0.94 degrees are used for both values. This means that given the ~6 square degree Landsat 7 scene, the ingestion process will produce ~6 separate tiles. This can be raised or lowered - we lower it for higher resolution data so that the file sizes are all roughly the same.
* The tile size must be evenly divisible by the resolution for both latitude and longitude - this means that the latitude tile size % the latitude resolution must be **exactly** zero. Not doing this can result in a single pixel gap between tiles caused by some rounding errors. If we were ingesting into Albers 25m, a valid tile size would be 100000, but not 100321 as it does not evenly divide. For projections that require fractional degrees (like above), we calculate our desired resolution in both the x and y direction and then multiply by an arbitrary constant (generally 3000-4000) to ensure that there are no rounding errors.

The last part of the configuration file is the measurement information. These look like the snippet seen below:

```
- name: blue
  dtype: int16
  nodata: -9999
  resampling_method: nearest
  src_varname: 'sr_band1'
  zlib: True
  attrs:
      long_name: "Surface Reflectance 0.45-0.52 microns (Blue)"
  alias: "band_1"
```

The important points to note here are that it contains the same information (or can contain) all of the same attributes from the product definition, as well as information required to map the source measurements to the ingested measurements.

The 'src_varname' field maps the ingested dataset measurements to source variables - in the above case, we are mapping 'sr_band1' to blue. If you open the agdc-metadata.yaml file, you'll see that one of the listed bands is 'sr_band1' and has a path to a .tif file. Additionally, the resampling method is listed along with the dtype and nodata if you desire a data type conversion or a change in nodata value.

Now that we have a complete ingestion configuration file, we are able to start the ingestion process. Use the following code snippet:

```
datacube -v ingest -c ~/Datacube/agdc-v2/ingest/ingestion_configs/ls7_sr_scenes_wgs84_vietnam.yaml --executor multiproc 2
```

You'll notice a few things in the command above: -c is the option for the configuration file, and --executor multiproc enables multiprocessing. In our case, we're using two cores. You should see a significant amount of console output as well as a constantly updating status until ingestion is finished. With our ~1 degree tiles, you can also see that we are producing 9 tiles for the single acquisition due to our tiling settings. The console output can be seen below:

```
2017-04-20 10:00:11,758 27010 datacube INFO Running datacube command: /home/localuser/Datacube/datacube_env/bin/datacube -v ingest -c /home/localuser/Datacube/agdc-v2/ingest/ingestion_configs/ls7_sr_scenes_wgs84_vietnam.yaml
2017-04-20 10:00:11,822 27010 agdc-ingest INFO Created DatasetType ls7_ledaps_vietnam
2017-04-20 10:00:11,916 27010 datacube.index.postgres._dynamic INFO Creating index: dix_ls7_ledaps_vietnam_lat_lon_time
2017-04-20 10:00:11,960 27010 datacube.index.postgres._dynamic INFO Creating index: dix_ls7_ledaps_vietnam_time_lat_lon
(106, 5)
...
(121, 21)
2017-04-20 10:00:12,405 27010 agdc-ingest INFO 9 tasks discovered
2017-04-20 10:00:12,485 27010 agdc-ingest INFO Submitting task: (114, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,486 27010 agdc-ingest INFO Submitting task: (115, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,486 27010 agdc-ingest INFO Submitting task: (113, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,486 27010 agdc-ingest INFO Submitting task: (115, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,486 27010 agdc-ingest INFO Submitting task: (114, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,487 27010 agdc-ingest INFO Submitting task: (113, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,487 27010 agdc-ingest INFO Submitting task: (113, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,487 27010 agdc-ingest INFO Submitting task: (114, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,487 27010 agdc-ingest INFO Submitting task: (115, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:12,488 27010 agdc-ingest INFO Starting task (114, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:19,265 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_114_13_20000507025950000000.nc
2017-04-20 10:00:22,625 27010 agdc-ingest INFO Finished task (114, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:22,626 27010 agdc-ingest INFO completed 1, failed 0, pending 8
2017-04-20 10:00:22,626 27010 datacube.index._datasets INFO Indexing 82b339a4-a12d-45c0-a851-f7a203b9a670
2017-04-20 10:00:22,898 27010 agdc-ingest INFO Starting task (115, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:35,432 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_115_11_20000507025950000000.nc
2017-04-20 10:00:38,110 27010 agdc-ingest INFO Finished task (115, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:38,110 27010 agdc-ingest INFO completed 1, failed 0, pending 7
2017-04-20 10:00:38,111 27010 datacube.index._datasets INFO Indexing 490d81eb-a22f-4411-9598-07f964fefb77
2017-04-20 10:00:38,156 27010 agdc-ingest INFO Starting task (113, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:41,747 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_113_13_20000507025950000000.nc
2017-04-20 10:00:44,523 27010 agdc-ingest INFO Finished task (113, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:44,524 27010 agdc-ingest INFO completed 1, failed 0, pending 6
2017-04-20 10:00:44,524 27010 datacube.index._datasets INFO Indexing e0e3b1c4-3d59-4255-aa31-20a2aa1b569b
2017-04-20 10:00:44,556 27010 agdc-ingest INFO Starting task (115, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:00:59,737 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_115_12_20000507025950000000.nc
2017-04-20 10:01:03,200 27010 agdc-ingest INFO Finished task (115, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:03,201 27010 agdc-ingest INFO completed 1, failed 0, pending 5
2017-04-20 10:01:03,201 27010 datacube.index._datasets INFO Indexing 04f5ccc5-c2a0-4824-8be1-2887a2721499
2017-04-20 10:01:03,278 27010 agdc-ingest INFO Starting task (114, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:08,624 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_114_12_20000507025950000000.nc
2017-04-20 10:01:14,500 27010 agdc-ingest INFO Finished task (114, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:14,501 27010 agdc-ingest INFO completed 1, failed 0, pending 4
2017-04-20 10:01:14,501 27010 datacube.index._datasets INFO Indexing 0921386d-333b-46c5-8398-40080fcf25f8
2017-04-20 10:01:14,567 27010 agdc-ingest INFO Starting task (113, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:18,858 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_113_11_20000507025950000000.nc
2017-04-20 10:01:22,925 27010 agdc-ingest INFO Finished task (113, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:22,925 27010 agdc-ingest INFO completed 1, failed 0, pending 3
2017-04-20 10:01:22,926 27010 datacube.index._datasets INFO Indexing 3ab3673a-e7bd-4fc7-a8aa-e3ff05042c3a
2017-04-20 10:01:23,000 27010 agdc-ingest INFO Starting task (113, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:27,720 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_113_12_20000507025950000000.nc
2017-04-20 10:01:32,007 27010 agdc-ingest INFO Finished task (113, 12, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:32,008 27010 agdc-ingest INFO completed 1, failed 0, pending 2
2017-04-20 10:01:32,008 27010 datacube.index._datasets INFO Indexing 45582c02-22f2-4efc-a81d-ee566f990c8a
2017-04-20 10:01:32,111 27010 agdc-ingest INFO Starting task (114, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:36,723 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_114_11_20000507025950000000.nc
2017-04-20 10:01:41,250 27010 agdc-ingest INFO Finished task (114, 11, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:41,250 27010 agdc-ingest INFO completed 1, failed 0, pending 1
2017-04-20 10:01:41,251 27010 datacube.index._datasets INFO Indexing 3a83cd2a-ca8f-419e-b937-8ea88b136b12
2017-04-20 10:01:42,293 27010 agdc-ingest INFO Starting task (115, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:45,774 27010 datacube.storage.storage INFO Creating storage unit: /datacube/ingested_data/LS7_ETM_LEDAPS/Vietnam/LS7_ETM_LEDAPS_4326_115_13_20000507025950000000.nc
2017-04-20 10:01:48,268 27010 agdc-ingest INFO Finished task (115, 13, numpy.datetime64('2000-05-07T02:59:50.000000000'))
2017-04-20 10:01:48,268 27010 agdc-ingest INFO completed 1, failed 0, pending 0
2017-04-20 10:01:48,269 27010 datacube.index._datasets INFO Indexing 2e0d1a7b-078d-4173-a636-f73ee9f920bd
9 successful, 0 failed
```

If you visit your '/datacube/ingested_data' directory, you'll see that a NetCDF file was created for each task. Using pgAdmin3 and viewing the data in the 'dataset' table, you can see that there are now 10 total datasets - one for your original scene and one for each ingested tile.

<a name="next_steps"></a> Next Steps
========  

Now that you have a complete Data Cube install and at least one ingested scene, we can move on into the application space. The next steps are setting up some of the example apps that we have created that demonstrate some of the Data Cube capabilities. First up is our Jupyter notebooks - these contain some example applications such as NDVI anomaly, water detection, SLIP, and mosaicking. The documentation for the Jupyter notebook setup can be found [here](./notebook_install.md). If you'd rather skip ahead and set up and configure our example web based user interface, see the documentation [here](./ui_install.md)

<a name="overview"></a> Brief Overview of Processes
========

Now that we've gone through the entire ingestion process and all required configuration file details, we can create a quick process guide that assumes that all of our configuration files are correctly set up.

The first step is to add your product definition. This will be done *once* for each dataset type - e.g. If we are indexing all Landsat 7 data over our country and continue to collect data after the initial download, this is done a *single* time. There is only one product definition for each dataset type.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#datacube -v product add {path to configuration file}
datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/ls8_sr_scenes.yaml
```

Now, for each dataset that is collected you will need to run a preparation script that generates the correct metadata as well as the 'datacube' command that indexes the dataset in the database. This only needs to be done once *for each dataset* - if you collect a new scene, you'll need to do this process for only that scene. Please note that indexing the dataset in the database creates an absolute reference to the path on disk - you cannot move the dataset on disk after indexing or it won't be found and will create problems.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#python ~/Datacube/agdc-v2/ingest/prepare_scripts/{script for dataset you want to add} {path to dataset(s)}
python ~/Datacube/agdc-v2/ingest/prepare_scripts/usgslsprepare.py /datacube/original_data/vietnam/LC8*/

datacube -v dataset add /datacube/original_data/vietnam/LC8*/
```

Now that the datasets have the correct metadata generated and have been indexed, we can run the ingestion process. Ingestion skips all datasets that have already been ingested, so this is a single command.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#datacube -v ingest -c {path to config} --executor multiproc {number of available cores}
datacube -v ingest -c ~/Datacube/agdc-v2/ingest/ingestion_configs/ls8_sr_scenes_wgs84_vietnam.yaml --executor multiproc 8
```

After an initial ingestion, when you download new acquisitions all you need to do is generate the metadata, index the dataset, and run the ingestion process.

<a name="faqs"></a> Common problems/FAQs
========  
----  

Q: 	
 > Why ingest the data if you can access indexed data programmatically?

A:  
 > Ingesting data allows for reprojection, resampling, and reformatting data into a more convenient format. NetCDF is the storage unit of choice for ingestion due to its performance benefits, and we choose to reproject into the standard WGS84 projection for ease of use.

---  

Q: 	
 > What if my dataset is already in a performant file format and my desired projection?

A:  
 > If your dataset is already in an optimized format and you don't desire any projection or resampling changes, then you can simply index the data and then begin to use the Data Cube.

---  

Q: 	
 > My ingestion runs, but reports only failed tasks and doesn't create storage units. How do I fix this?

A:  
 > Check the permissions on the location that your ingested data is going to be written to. The user that you're running ingestion as needs to have write permissions to that directory.

---  

Q: 	
 > In one of the examples, you specify an output CRS and resolution - can I do this to any dataset that I have indexed or ingested?

A:  
 > Yes, the Data Cube supports setting projection and resolution on data load. This takes some time, so if a single projection is generally desired it may be better to ingest the data into that projection.

---  

Q: 	
 > During ingestion, I'm getting a rasterio error specifying that a location does not exist or is not a valid dataset, how can I fix this?

A:  
 > Has the location of your dataset on disk (the metadata .yaml file) changed? When data is indexed, an absolute path to the data on disk is created so you cannot easily move data after indexing.

---  
