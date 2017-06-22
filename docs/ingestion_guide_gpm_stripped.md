# Data Cube Ingestion Guide

This document will guide users through the process of indexing and ingesting ARD datasets into the Data Cube using the command line tool and required configuration files. This document contains information and snippets from the [official ODC user guide](http://datacube-core.readthedocs.io/en/latest/user/intro.html). This document describes the process for indexing and ingesting any arbitrary raster dataset, from Landsat to real time GPM data.

# Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Product Definitions](#product_definition)
- [Generating Metadata](#generating_metadata)
- [Indexing Datasets](#indexing_datasets)
- [Ingesting Datasets](#ingesting_datasets)
- [Brief Overview of Processes](#overview)
- [Next Steps](#next_steps)
- [Common problems/FAQs](#faqs)

# []() Introduction

The indexing and ingestion workflow is required to add data to the Data Cube and provide access to the data via a Python API. Data is loaded by querying the Data Cube for data that matches certain metadata attributes, such as measurement name, product and platform type, geospatial and temporal extents.

**Read the official ODC documentation on [their readthedocs.io page](http://datacube-core.readthedocs.io/en/stable/ops/config.html)**

The ingestion workflow consists of: Creating a product definition for your new dataset, creating a preparation script for your new dataset, generating a .yaml metadata file using the preparation script, indexing the dataset's metadata in the Data cube, and running the ingestion process on indexed datasets. A brief description of these steps can be found below:

- **Creating and adding a product definition**: Product definitions include a name, description, basic metadata, and a list of measurements with relevant properties in the dataset.
- **Creating a preparation script and generating metadata**: Dataset metadata is a .yaml file that describes a dataset is required for indexing in the Data Cube. This metadata file will include properties such as measurements with paths to the data, platform and sensor names, geospatial extents and projection, and acquisition dates. This is done using a Python preparation script that pulls the required fields from file names, dataset xml metadata, and raster datasets.
- **Indexing dataset metadata**: Indexing a dataset involves recording the content of the metadata file in the database. This allows access to the metadata via the Python API and for programmatic loading of data based on metadata.
- **Ingesting indexed datasets**: The ingestion process defines a mapping between a source dataset and a dataset with more desirable properties. A new product definition will be added to the Data Cube with the properties defined in the ingestion configuration file and datasets that match the provided criteria will be modified according to the new product definition and written to disk in the new format. Each modified dataset (or dataset tile) is indexed in the Data Cube.

# []() Ingestion Cheat Sheet

The first step is to add your product definition. This will be done _once_ for each dataset type - e.g. If we are indexing all GPM data over our country and continue to collect data after the initial download, this is done a _single_ time. There is only one product definition for each dataset type.

```
datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/gpm/gpm_imgerg_gis.yaml
```

Now, for each dataset that is collected you will need to run a preparation script that generates the correct metadata as well as the 'datacube' command that indexes the dataset in the database. This only needs to be done once _for each dataset_ - if you collect a new scene, you'll need to do this process for only that scene. Please note that indexing the dataset in the database creates an absolute reference to the path on disk - you cannot move the dataset on disk after indexing or it won't be found and will create problems.

```
python ~/Datacube/agdc-v2/ingest/prepare_scripts/gpm/gpm_imgerg_gis_prepare.py /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A
datacube -v dataset add /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A/*.yaml
```

Now that the datasets have the correct metadata generated and have been indexed, we can run the ingestion process. Ingestion skips all datasets that have already been ingested, so this is a single command.

```
datacube -v ingest -c ~/Datacube/agdc-v2/ingest/ingestion_configs/gpm/gpm_monthly_global.yaml --executor multiproc 2
```

After an initial ingestion, when you download new acquisitions all you need to do is generate the metadata, index the dataset, and run the ingestion process.

# []() Prerequisites

To index and ingest data into the Data Cube, the following prerequisites must be met:

- The full Data Cube Installation Guide must have been followed and completed. This includes:

  - You have a local user that is used to run the Data Cube commands/applications
  - You have a database user that is used to connect to your 'datacube' database
  - The Data Cube is installed and you have successfully run 'datacube system init'
  - All code is checked out and you have a virtual environment in the correct directories: `~/Datacube/{data_cube_ui, data_cube_notebooks, datacube_env, agdc-v2}`

- A georeferenced raster dataset. This can come in the form of:

  - A series of GeoTiff files for each band
  - A NetCDF/HDF5 file containing multiple bands
  - A BEAM-DIMAP formatted dataset (.dim with .img)
  - Other widely supported raster datasets

- Associated metadata for your dataset (XML, file naming details, etc). This includes (at the very least, more is always better):

  - Acquisition date
  - Processing level
  - Product type

- Your product's associated datasheet. This should describe your bands, datatypes, flag definitions, nodata values, etc. For example, the Landsat 7 datasheet can be found [here](https://landsat.usgs.gov/sites/default/files/documents/ledaps_product_guide.pdf), GPM datasheet [here](https://pps.gsfc.nasa.gov/Documents/README.GIS.pdf). If you do not have access to a datasheet, a lot of the datatype information can be found using 'gdalinfo'. The main objective here is to identify the datatype of each band and the nodata value for each band.

If you have not yet completed our Data Cube Installation Guide, please do so before continuing.

The only _required_ metadata for the default 'eo' metadata (found [here](https://github.com/opendatacube/datacube-core/blob/develop/datacube/index/default-metadata-types.yaml) in the search fields) are platform, instrument, product type, lat, lon, and time.

For this example, we will be using a GPM Monthly dataset, found [here](http://ec2-52-201-154-0.compute-1.amazonaws.com/datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A.zip). Accompanying this dataset is the associated product datasheet, found [here](http://ec2-52-201-154-0.compute-1.amazonaws.com/datacube/original_data/gpm/README.GIS.pdf). Please download these two files before continuing.

# []() Creating and adding a product definition

Product definitions define the attributes for entire datasets and are stored as .yaml files. These attributes include:

- A short name for the dataset
- A short description of what the dataset is
- A metadata type - more on this later
- Product metadata, including platform, instrument, product type, etc.
- Any number of measurements that are associated with the dataset and their attributes.

For the GPM data used for this workshop we have provided a product definition, which can be found at ~/Datacube/agdc-v2/ingest/dataset_types/gpm/gpm_imgerg_gis.yaml

For detailed information on creating a product definition for a different dataset seethe official ODC documentation on product definitions on their readthedocs.io page http://datacube-core.readthedocs.io/en/stable/ops/config.html

Once your product definition has all required information, you add it to the Data Cube. For our GPM example, this is done with the following command:

```
datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/gpm/gpm_imerge_gis.yaml
```

This command should be run from within the virtual environment. This will validate your product definition and, if valid, will index it in the Data Cube. The expected output should look like below:

```
2017-04-19 11:23:39,861 21121 datacube INFO Running datacube command: /home/localuser/Datacube/datacube_env/bin/datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/gpm/gpm_imerge_gis.yaml
2017-04-19 11:23:40,184 21121 datacube.index.postgres._dynamic INFO Creating index: .....
2017-04-19 11:23:40,194 21121 datacube.index.postgres._dynamic INFO Creating index: .....
Added "gpm_imerge_gis_monthly"
```

If you open pgAdmin3 and examine the data in the dataset_type table, you'll see that there is now a row for the added product with all associated metadata.
With the product definition added to the Data Cube, the next step is generating the required metadata to add a dataset.

# []() Generating Metadata

Before starting this step, create a new directory use the following command:
```
mkdir /datacube/original_data/gpm
```
Store the downloaded GPM dataset inside. Ensure that the sole contents of the directory are the .zip GPM files downloaded earlier in this guide.


Now that we have the data inside a named directory, we can generate the required metadata .yaml file. This is done with Python scripts found in `~/Datacube/agdc-v2/ingest/prepare_scripts/*`.

There are a variety of scripts provided, including USGS Landsat, Sentinel 1, ALOS, and GPM, which we will use for this workshop.

These scripts are responsible for creating a .yaml metadata file that contains all required metadata fields. For detailed information on creating a script to generate metadata for a different dataset, see the Generating Metadata section in the Ingestion Guide document.

In order to run the script on the GPM dataset, use the command:

```
python ~/Datacube/agdc-v2/ingest/prepare_scripts/gpm/gpm_imerg_gis_prepare.py /datacube/original_data/gpm/*.zip
```

If ran correctly, the output should be as follows:
```
2017-06-09 18:24:18,821 INFO Processing /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A
2017-06-09 18:27:27,356 INFO Writing /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A/datacube-metadata.yaml
```

You'll see that the script has created a .yaml file titled datacube-metadata.yaml in the same directory as your data files.
Open this .yaml file and verify that all fields have been populated and there are no errors.

# []() Indexing Datasets

## Indexing Datasets in the Database

Now that you have a product definition added and a datacube-metadata.yaml file generated for your scene, it is now time to index the dataset and associate it with the product definition.
This is done with the 'datacube dataset add' command from the CLI.
Please note that indexing the dataset in the database creates an absolute reference to the path on disk - you cannot move the dataset on disk after indexing or it won't be found and will create problems.

The `datacube dataset add` command can be run on the directory or metadata .yaml file generated for the dataset.
This command will load the .yaml metadata file and create a Dataset class object from the contents.
It will then try to match the dataset to a product definition using the provided metadata.

```
#ensure that you are doing this from within the virtual environment. If not, activate it with 'source ~/Datacube/datacube_env/bin/activate'
datacube -v dataset add /datacube/original_data/gpm/*/
#or
#datacube -v dataset add /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A/datacube-metadata.yaml
```

The resulting console output will resemble the output below:

```
2017-06-09 18:32:32,075 5086 datacube INFO Running datacube command: /home/localuser/Datacube/datacube_env/bin/datacube -v dataset add /datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A/datacube-metadata.yaml
Indexing datasets  [####################################]  100%2017-06-09 18:32:32,122 5086 datacube-dataset INFO Matched Dataset <id=18163152-7388-4607-a75b-1f20e7b70045 type=gpm_imerg_gis_monthly location=/datacube/original_data/gpm/3B-MO-GIS.MS.MRG.3IMERG.20140301-S000000-E235959.03.V04A/datacube-metadata.yaml>
2017-06-09 18:32:32,123 5086 datacube.index._datasets INFO Indexing 18163152-7388-4607-a75b-1f20e7b70045
```

If there is a problem matching your dataset, please go back and ensure that the metadata matches between your dataset type and dataset metadata. This includes:

- Measurements/bands
- Platform
- Instrument
- Product type

Now that the dataset has been added, you can open up pgAdmin3 and view the data in the 'datasets' table - you'll notice that there is now an entry for the dataset you've just added.
This should include:

- the id
- A reference to the metadata definition corresponding to a primary key in the 'metadata_type' table
- A reference to the dataset type corresponding to a primary key in the 'dataset_type' table.

If you look at the 'metadata_type' and 'dataset_type' tables with the listed ids, you'll see the full metadata and dataset type definitions from the previous steps.

Now that we have demonstrated the indexing process and data access, we can ingest the dataset.

# []() Ingesting Datasets

With a newly indexed dataset, the next step is ingestion.

Ingestion is the process of transforming original datasets into more accessible format that can be used by the Data Cube.
Like the previous steps, ingestion relies on the use of a .yaml configuration file that specifies all of the input and output details for the data.
The ingestion configuration file contains all of the information required for a product definition - it uses the information to create a new product definition and index it in the Data Cube.
Next, indexed source datasets that fit the criteria are identified, tiled, reprojected, and resampled (if required) and written to disk as NetCDF storage units.
The required metadata is generated and the newly created datasets are indexed (added) to the Data Cube.

The ingestion configuration file is essentially defining a transformation between the source and the output data.
You can define attributes such as resolution, projection, tile sizes, bounds, and measurements, along with file type and other metadata in a configuration file.
When you run the ingestion process, the Data Cube determines what data fits the input data attributes by product type and bounds, applies the defined transformation, and saves the result to disk and in the database.
This process is generally done when the data is in a file format not optimized for random access such as GeoTiff - NetCDF is the preferred file type.

We have provided a GPM ingestion configuration for this workshop For detailed information on creating an ingestion configuration for other datasets see the Ingesting Datasets section in the Ingestion Guide document.

Now that we have a complete ingestion configuration file, we are able to start the ingestion process. Use the following code snippet:

```
datacube -v ingest -c ~/Datacube/agdc-v2/ingest/ingestion_configs/gpm/gpm_monthly_global.yaml --executor multiproc 2
```

You'll notice a few things in the command above: -c is the option for the configuration file, and --executor multiproc enables multiprocessing.
In our case, we're using two cores. You should see a significant amount of console output as well as a constantly updating status until ingestion is finished.
With our ~1 degree tiles, you can also see that we are producing 9 tiles for the single acquisition due to our tiling settings. The final lines of the console output can be seen below:

```

2017-06-11 12:03:13,244 12997 agdc-ingest INFO Finished task (-3, 9, numpy.datetime64('2015-12-12T10:28:23.000000000'))
2017-06-11 12:03:14,053 12986 agdc-ingest INFO completed 1, failed 0, pending 0
2017-06-11 12:03:14,053 12986 datacube.index._datasets INFO Indexing 39b9a5a5-840e-4bc2-ade7-d682ec8a4e56
8 successful, 0 failed
```

If you visit your `/datacube/ingested_data` directory, you'll see that a NetCDF file was created for each task.
Using pgAdmin3 and viewing the data in the 'dataset' table, you can see that there are now 10 total datasets - one for your original scene and one for each ingested tile.

**If you have issues creating the storage units, make sure the user that is running ingestion has permissions to write to the file path template and base location.**

# []() Brief Overview of Processes

Now that we've gone through the entire ingestion process and all required configuration file details, we can create a quick process guide that assumes that all of our configuration files are correctly set up.

The first step is to add your product definition. This will be done _once_ for each dataset type - e.g. If we are indexing all Landsat 7 data over our country and continue to collect data after the initial download, this is done a _single_ time.
There is only one product definition for each dataset type.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#datacube -v product add {path to configuration file}
datacube -v product add ~/Datacube/agdc-v2/ingest/dataset_types/gpm/gpm_imgerg_gis.yaml
```

Now, for each dataset that is collected you will need to run a preparation script that generates the correct metadata as well as the 'datacube' command that indexes the dataset in the database.
This only needs to be done once _for each dataset_ - if you collect a new scene, you'll need to do this process for only that scene.
Please note that indexing the dataset in the database creates an absolute reference to the path on disk - you cannot move the dataset on disk after indexing or it won't be found and will create problems.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#python ~/Datacube/agdc-v2/ingest/prepare_scripts/{script for dataset you want to add} {path to dataset(s)}
python ~/Datacube/agdc-v2/ingest/prepare_scripts/gpm/gpm_imerg_gis_prepare.py /datacube/original_data/gpm/*.zip

datacube -v dataset add /datacube/original_data/General/*/
```

Now that the datasets have the correct metadata generated and have been indexed, we can run the ingestion process. Ingestion skips all datasets that have already been ingested, so this is a single command.

```
#ensure that you're in the virtual environment. If not, activate with 'source ~/Datacube/datacube_env/bin/activate'
#datacube -v ingest -c {path to config} --executor multiproc {number of available cores}
datacube -v ingest -c ~/Datacube/agdc-v2/ingest/ingestion_configs/gpm/gpm_monthly_global.yaml --executor multiproc 2
```

After an initial ingestion, when you download new acquisitions all you need to do is generate the metadata, index the dataset, and run the ingestion process.

# []() Common problems/FAQs

--------------------------------------------------------------------------------

Q:

> Why ingest the data if you can access indexed data programmatically?

A:

> Ingesting data allows for reprojection, resampling, and reformatting data into a more convenient format. NetCDF is the storage unit of choice for ingestion due to its performance benefits, and we choose to reproject into the standard WGS84 projection for ease of use.

--------------------------------------------------------------------------------

Q:

> What if my dataset is already in a performant file format and my desired projection?

A:

> If your dataset is already in an optimized format and you don't desire any projection or resampling changes, then you can simply index the data and then begin to use the Data Cube.

--------------------------------------------------------------------------------

Q:

> My ingestion runs, but reports only failed tasks and doesn't create storage units. How do I fix this?

A:

> Check the permissions on the location that your ingested data is going to be written to. The user that you're running ingestion as needs to have write permissions to that directory.

--------------------------------------------------------------------------------

Q:

> In one of the examples, you specify an output CRS and resolution - can I do this to any dataset that I have indexed or ingested?

A:

> Yes, the Data Cube supports setting projection and resolution on data load. This takes some time, so if a single projection is generally desired it may be better to ingest the data into that projection.

--------------------------------------------------------------------------------

Q:

> During ingestion, I'm getting a rasterio error specifying that a location does not exist or is not a valid dataset, how can I fix this?

A:

> Has the location of your dataset on disk (the metadata .yaml file) changed? When data is indexed, an absolute path to the data on disk is created so you cannot easily move data after indexing.

--------------------------------------------------------------------------------
