CEOS Data Cube UI
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

Installation
=================
```
git clone https://github.com/ceos-seo/data_cube_ui.git -b master
cd ~/Datacube/data_cube_ui
git submodule init && git submodule update
```

Requirements
=================

* Full Data Cube installation with ingested data

* apache2
* libapache2-mod-wsgi-py3
* redis-server
* libfreeimage3
* tmux
* django
* redis
* celery
* imageio
* django-bootstrap3
* matplotlib
* stringcase

For more detailed instructions, please read the [documentation](docs/ui_install.md). If you want to add a new algorithm to the UI, you can follow our [adding a new algorithm](docs/adding_new_pages.md) documentation.
