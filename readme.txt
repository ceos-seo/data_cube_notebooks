********************************************************************************************
*                                Simple Application Spin Up                                *
********************************************************************************************

This is designed as a quick guide for spinning up a UI application based on the template that
is used for applications under the "UI Suite."  The document will explain creating an application
as well as copying from a template application made available in the source coude.For a full
reference of Django and its features, as well as a tutorial, see the following link:
https://docs.djangoproject.com/en/1.10/intro/tutorial01/



------------------
+Creating the app+
------------------
Django handles most of the file creation through a series of commands under the manage.py.
In developing the application on this VM, the python virtual environment must first be
started.  This is accomplished through the following command:

	  source ~/Datacube/datacube_env/bin/activate

Once started, the text "(datacube_env)" should be shown next to the new line in the shell. The
next step is to create the application itself.  The commands are as follows:

     	  cd ~/Datacube/data_cube_ui
	  python manage.py startapp NAME_OF_APP

This will create a directory for the app at the top level.  The app folder should be moved to
the same level as the other applications in the suite.

    	 mv NAME_OF_APP ~/Datacube/data_cube_ui/apps

Once in the same directory, the new application must be registered with Django to be recognized.
Open the "settings.py" file under the directory ~/Datacube/data_cube_ui/data_cube_ui.  In this
file there are a list of installed applications.  Add the application that was recently created to
the list of applications like so (exclude double quotes): "`apps.NAME_OF_APP`,"

::NOTE:: The comma must be present even at the end of the list.

To navigate to and within the new application, the URLs must be included in the main application.
Open the "urls.py" file under the directory where the "settings.py" exists (~/Datacube/data_cube_ui/data_cube_ui).
There are a list of url patterns present.  Add the following line after the last URL object:

      	  url(r'^NAME_OF_APP/', include('apps.NAME_OF_APP.urls')),

With the addition of this line the new application can be reached and navigated.


-----------------------------------------
+Customizing the App for GeoSpatial Work+
-----------------------------------------
As the suite of applications used in this UI App are designed to work on GeoSpatial data, an
empty sample project containing some features that are common to the project are made avaiable
under the apps/sample_geo_app.

Resuable features in this application include the following:
	 models.py: Contains a basic Query, Metadata, and Result object.
	 urls.py: Contains the basic urls needed to perform the common functions.
	 forms.py: Contains the Geospatial form and a Data Select form template that can be modified
	 	   to fid the users needs.
	 views.py: Contains the basic view methods that will be required to perform common tasks.

::NOTE:: The templates that store the HTML returned to the user are stored in a higher level of
	 the application.  This means that it is not required to create individual instances of
	 the HTML pages for each application. If a new page is required, create and place the
	 file in the "~/Datacube/data_cube_ui/templates/" directory.

::NOTE:: The product landing page provides a level of customization for the Results and Output tabs.
	 Each of these tabs has their respective sections in which a variety of data can be included.
	 The design for the blocks of content will be in their own respective folders under the
	 templates folder (ie. water_detection/results_list.html, custom_mosaic/output_list.html).
	 It will be required to create instances of these HTML documents for data display purposes.
	 This can be accomplished through copying a preexisting plugin with the desired functionality
	 or by creating a new HTML document.

To use the sample_geo_app, create a copy and rename to the desired application name (SOME_APP).
This application should live in the same directory as all the other apps (~/Datacube/data_cube_ui/apps).
Once a copy of the application has been created, register the application in the "settings.py"
located in the following directory:

	~/Datacube/data_cube_ui/data_cube_ui/settings.py

Add the following line under the INSTALLED_APPS to include the application:

    	'apps.SOME_APP',

To navigate to and within the new application, the URLs must be included in the main application.
Open the "urls.py" file under the directory where the "settings.py" exists (~/Datacube/data_cube_ui/data_cube_ui).
There are a list of urlpatters present.  Add the following line after the last URL object:

      	  url(r'^NAME_OF_APP/', include('apps.SOME_APP.urls')),

With the addition of this line the new application can be reached and navigated.

Due to it's high modularity, a number of features have been broken out based on apps.  In the case
of the output list, query history, and result List, the templates is common between all the different
applications.  As a result, the developer should create custom pages within respective folders in the
template directory (as seen with the Sample Geo App) to include customized fields for user input and
program out.

::NOTE:: Django will not recognize the subfolders of the templates directory unless included in the
	 `setting.py` file under the TEMPLATES field.

----------------------------
+Contents of Sample_Geo_App+
----------------------------

***models.py***

Contains Query, Metadata, Result, and Area models.  Each of these models contains data commonly
found through out the suite of applications.  Note that more fields may be required to fit the
applications needs.  Also worth noting that fields can be removed if necessary.

To put the models in the database (as these are Python represenations of database tables), the
following commands can be ran:

	  cd ~/Datacube/data_cube_ui
	  python manage.py makemigrations
	  python manage.py migrate

These will create the Django version of SQL statements to create the database tables for a developer.

***urls.py***

Contains the URLs necessary for basic funtionality.  This includes submitting single or multiple
requests, cancelling the requests, displaying the results, and navigating the application.  It should
be noted that the final URL listed points to the basic view of the sample_geo_app.  This will
change as the developer renames the application to the desired name.  More URLs can be added if
so desired to include other pages.

***forms.py***

Contains the GeospatialForm template for a form.  This is most often used to gather required user
input fields regarding geospatial data.  More fields can be added if required.

The DataSelectForm allows for the creation of drop down menus to provide for users to input the
desired data.  More fields can be added in the __init__ function if desired.  This form holds only
one field as a sample for developers to replicate.

***views.py***

Contains the logic to build and return the Templates populated with data.  This file has all the
required methods for showing the landing page (which include three tabs a map area), submitting
the requests, loading the forms for recieving user input, and loading older results.

The comments in the code have been templated out so the developer can see the format for the
docstring the application follows.  More methods and views may be required as the application
grows in functionality.
