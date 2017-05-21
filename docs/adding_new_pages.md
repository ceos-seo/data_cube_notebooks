Data Cube Algorithm Addition Guide
=================

This document will guide users through the process of adding new algorithms or analysis cases to the UI, including the general Django files and the Celery workflow. This guide assumes that the user has a working Data Cube installation and has completed the full UI installation guide.

Contents
=================

  * [Introduction](#introduction)
  * [Basic Components](#basic_components)
  * [Base Classes](#base_classes)
  * [Generating Base Files](#base_files)
  * [Basic Applications](#band_math_app)
  * [Complex Applications](#complex_app)
  * [Templating Changes](#templates)
  * [Common problems/FAQs](#faqs)

<a name="introduction"></a> Introduction
=================
The Data Cube UI is designed to be quickly and easily extended to integrate new algorithms that operate on Data Cube based raster datasets. A new algorithm implementation includes three main parts:

* Django views - map URLs to rendered HTML pages
* Django models - Hold the main task attributes (parameters, results, etc)
* Celery workflows - Process asynchronous tasks, populating a Django model with updates and results

Two manage.py commands are provided to expedite this processing, requiring only simple and defined changes to get an application working.

<a name="basic_components"></a> Basic Components
=================
The three main components of a new algorithm implementation were outlined above - the views, models, and celery tasks.

Django Views
--------
```
class SubmitNewRequest(SubmitNewRequest):
    """
    Submit new request REST API Endpoint
    Extends the SubmitNewRequest abstract class - required attributes are the tool_name,
    task_model_name, form_list, and celery_task_func

    Note:
        celery_task_func should be callable with .delay() and take a single argument of a TaskModel pk.

    See the dc_algorithm.views docstrings for more information.
    """
    tool_name = 'coastal_change'
    task_model_name = 'CoastalChangeTask'
    #celery_task_func = create_cloudfree_mosaic
    celery_task_func = run
    form_list = [DataSelectionForm, AdditionalOptionsForm]

...
```

Each view class subclasses the base dc_algorithm class so only minor changes need to be made for a new page. Functions and variables that need to be provided are defined in the base class docstring, and if they are omitted then an exception is raised. HTML content that is rendered in the browser is controlled here - forms, panels, etc.

Django models
------
```
class Query(BaseQuery):
    """

    Extends base query, adds app specific elements. See the dc_algorithm.Query docstring for more information
    Defines the get_or_create_query_from_post as required, adds new fields, recreates the unique together
    field, and resets the abstract property. Functions are added to get human readable names for various properties,
    foreign keys should define __str__ for a human readable name.

    """

    #override the time start and time end properties of the base class - this is yearly.
    time_end = models.IntegerField()
    time_start = models.IntegerField()

    animated_product = models.ForeignKey(AnimationType)

    config_path = '/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/config/.datacube.conf'
    measurements = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'cf_mask']
    base_result_dir = '/datacube/ui_results/coastal_change'

    class Meta(BaseQuery.Meta):
        unique_together = (('platform', 'area_id', 'time_start', 'time_end', 'latitude_max', 'latitude_min', 'longitude_max',
                            'longitude_min', 'title', 'description', 'animated_product'))
        abstract = True

    def get_fields_with_labels(self, labels, field_names):
        for idx, label in enumerate(labels):
            yield [label, getattr(self, field_names[idx])]

    def get_chunk_size(self):
        """Implements get_chunk_size as required by the base class

        See the base query class docstring for more information.

        """
        #Creating median mosaics on a yearly basis.
        return {'time': None, 'geographic': 0.005}

    def get_iterative(self):
        """implements get_iterative as required by the base class

        See the base query class docstring for more information.

        """
        return False

    def get_reverse_time(self):
        """implements get_reverse_time as required by the base class

        See the base query class docstring for more information.

        """
        return False

    def get_processing_method(self):
        """implements get_processing_method as required by the base class

        See the base query class docstring for more information.

        """

        return create_median_mosaic

    @classmethod
    def get_or_create_query_from_post(cls, form_data):
        """Implements the get_or_create_query_from_post func required by base class

        See the get_or_create_query_from_post docstring for more information.
        Parses out the time start/end, creates the product, and formats the title/description

        Args:
            form_data: python dict containing either a single obj or a list formatted with post_data_to_dict

        Returns:
            Tuple containing the query model and a boolean value signifying if it was created or loaded.

        """
        query_data = form_data
        query_data['title'] = "Coastal Change Query" if 'title' not in form_data or form_data[
            'title'] == '' else form_data['title']
        query_data['description'] = "None" if 'description' not in form_data or form_data[
            'description'] == '' else form_data['description']

        valid_query_fields = [field.name for field in cls._meta.get_fields()]
        query_data = {key: query_data[key] for key in valid_query_fields if key in query_data}

        try:
            query = cls.objects.get(**query_data)
            return query, False
        except cls.DoesNotExist:
            query = cls(**query_data)
            query.save()
            return query, True
```

Django models contain all of the information and parameters required to perform your operation and create output products. This includes where to save the output products, how to split data for processing, and the Python function that should be used to create the output products. All input and output parameters should be enumerated here.

Celery tasks
------
Celery tasks perform all processing for the algorithms. Tasks use information found on the models to separate data chunks into manageable sizes, perform analysis functions, and create output products.

```
@task(name="coastal_change.perform_task_chunking")
def perform_task_chunking(parameters, task_id):
    """Chunk parameter sets into more manageable sizes

    Uses functions provided by the task model to create a group of
    parameter sets that make up the arg.

    Args:
        parameters: parameter stream containing all kwargs to load data

    Returns:
        parameters with a list of geographic and time ranges

    """

    if parameters is None:
        return None

    task = CoastalChangeTask.objects.get(pk=task_id)
    dc = DataAccessApi(config=task.config_path)

    dates = dc.list_acquisition_dates(**parameters)
    task_chunk_sizing = task.get_chunk_size()

    geographic_chunks = create_geographic_chunks(
        longitude=parameters['longitude'],
        latitude=parameters['latitude'],
        geographic_chunk_size=task_chunk_sizing['geographic'])

    grouped_dates = group_datetimes_by_year(dates)
    # we need to pair these with the first year - subsequent years.
    time_chunks = None
    if task.animated_product.animation_id == 'none':
        # first and last only
        time_chunks = [[grouped_dates[task.time_start], grouped_dates[task.time_end]]]
    else:
        initial_year = grouped_dates.pop(task.time_start)
        time_chunks = [[initial_year, grouped_dates[year]] for year in grouped_dates]
    print("Time chunks: {}, Geo chunks: {}".format(len(time_chunks), len(geographic_chunks)))

    dc.close()
    task.update_status("WAIT", "Chunked parameter set.")

    return {'parameters': parameters, 'geographic_chunks': geographic_chunks, 'time_chunks': time_chunks}


@task(name="coastal_change.start_chunk_processing")
def start_chunk_processing(chunk_details, task_id):
    """Create a fully asyncrhonous processing pipeline from paramters and a list of chunks.

    The most efficient way to do this is to create a group of time chunks for each geographic chunk,
    recombine over the time index, then combine geographic last.
    If we create an animation, this needs to be reversed - e.g. group of geographic for each time,
    recombine over geographic, then recombine time last.

    The full processing pipeline is completed, then the create_output_products task is triggered, completing the task.

    """

    if chunk_details is None:
        return None

    parameters = chunk_details.get('parameters')
    geographic_chunks = chunk_details.get('geographic_chunks')
    time_chunks = chunk_details.get('time_chunks')

    task = CoastalChangeTask.objects.get(pk=task_id)
    task.total_scenes = len(geographic_chunks) * len(time_chunks) * (task.get_chunk_size()['time'] if
                                                                     task.get_chunk_size()['time'] is not None else 1)
    task.scenes_processed = 0
    task.update_status("WAIT", "Starting processing.")

    print("START_CHUNK_PROCESSING")

    processing_pipeline = group([
        group([
            processing_task.s(
                task_id=task_id,
                geo_chunk_id=geo_index,
                time_chunk_id=time_index,
                geographic_chunk=geographic_chunk,
                time_chunk=time_chunk,
                **parameters) for geo_index, geographic_chunk in enumerate(geographic_chunks)
        ]) | recombine_geographic_chunks.s(task_id=task_id) for time_index, time_chunk in enumerate(time_chunks)
    ]) | recombine_time_chunks.s(task_id=task_id)

    processing_pipeline = (processing_pipeline | create_output_products.s(task_id=task_id)).apply_async()
    return True
```

The Celery tasks open models by their id and parse out the required information. All actual processing is done in the tasks.py for the app - from data fetching and chunking to processing output products. It is in tasks.py where the actual algorithm will be implemented.

The processing pipeline in tasks.py is organized so that each task operates independently of one another - the process is fully asynchronous and non-blocking. The tasks are also arranged so that you work down the page as the task executes, and each task completes a single function.

* Parameters are parsed out from the task model
* Parameters are verified and validated
* Parameters are chunked into smaller, more manageable pieces for parallelized processing
* A processing pipeline is created from the parameter chunks and submitted for processing - this involves both geographic and time based chunks
* Each chunk is processed, with the results being saved to disk. Metadata is collected here and passed forward
* The chunks are combined both geographically and over time, combining metadata as well
* The output products are generated and the model is updated

<a name="base_classes"></a> Base Classes
=================
Django models and views allow for standard Python inheritance, allowing us to simply subclass a common dc_algorithm base to quickly create new apps. Take some time to look through the files in `apps/dc_algorithm` - the docstrings explain exactly what each view and model does and what attributes are required.

The main portion of the dc_algorithm base app lies within `views.py` and `models/abstract_base_models.py`.

Below is the base class for task submission. You'll notice the extensive docstrings outlining all required attributes and parameters. Additionally, there are 'getter' functions that raise a NotImplementedError when a required attribute is not present. Compare this class to the implementation in <a name="basic_components">Basic Components</a> - Only the required attributes are defined, and everything else lies within the base class.

```
class SubmitNewRequest(View, ToolClass):
    """Submit a new request for processing using a task created with form data

    REST API Endpoint for submitting a new request for processing. This is a POST only view,
    so only the post function is defined. Form data is used to create a Task model which is
    then submitted for processing via celery.

    Abstract properties and methods are used to define the required attributes for an implementation.
    Inheriting SubmitNewRequest without defining the required abstracted elements will throw an error.
    Due to some complications with django and ABC, NotImplementedErrors are manually raised.

    Required Attributes:
        tool_name: Descriptive string name for the tool - used to identify the tool in the database.
        celery_task_func: A celery task called with .delay() with the only parameter being the pk of a task model
        task_model_name: Name of the model that represents your task - see models.Task for more information
        form_list: list [] of form classes (e.g. AdditionalOptionsForm, GeospatialForm) to be used to validate all provided input.

    """

    celery_task_func = None
    form_list = None

    @method_decorator(login_required)
    def post(self, request):
        """Generate a task object and start a celery task using POST form data

        Decorated as login_required so the username is fetched without checking.
        A full form set is submitted in one POST request including all of the forms
        associated with a satellite. This formset is generated using the
        ToolView.generate_form_dict function and should be the forms for a single satellite.
        using the form_list, each form is validated and any errors are returned.

        Args:
            POST data including a full form set described above

        Returns:
            JsonResponse containing:
                A 'status' with either OK or ERROR
                A Json representation of the task object created from form data.
        """

        user_id = request.user.id

        response = {'status': "OK"}
        task_model = self._get_tool_model(self._get_task_model_name())
        forms = [form(request.POST) for form in self._get_form_list()]
        #validate all forms, print any/all errors
        full_parameter_set = {}
        for form in forms:
            if form.is_valid():
                full_parameter_set.update(form.cleaned_data)
            else:
                for error in form.errors:
                    return JsonResponse({'status': "ERROR", 'message': form.errors[error][0]})

        task, new_task = task_model.get_or_create_query_from_post(full_parameter_set)
        #associate task w/ history
        history_model, __ = self._get_tool_model('userhistory').objects.get_or_create(user_id=user_id, task_id=task.pk)
        if new_task:
            self._get_celery_task_func().delay(task.pk)
        response.update(model_to_dict(task))

        return JsonResponse(response)

    def _get_celery_task_func(self):
        """Gets the celery task function and raises an error if it is not defined.

        Checks if celery_task_func property is None, otherwise return the function.
        The celery_task_func must be a function callable with .delay() with the only
        parameters being the pk of a task model.

        """
        if self.celery_task_func is None:
            raise NotImplementedError(
                "You must specify a celery_task_func in classes that inherit SubmitNewRequest. See the SubmitNewRequest docstring for more details."
            )
        return self.celery_task_func

    def _get_form_list(self):
        """Gets the list of forms used to validate post data and raises an error if it is not defined.

        Checks if form_list property is None, otherwise return the function.
        The celery_task_func must be a function callable with .delay() with the only
        parameters being the pk of a task model.

        """
        if self.form_list is None:
            raise NotImplementedError(
                "You must specify a form_list in classes that inherit SubmitNewRequest. See the SubmitNewRequest docstring for more details."
            )
        return self.form_list
```

Model base classes work in the same way - common attributes are defined, and users are free to add or remove fields in child classes.

<a name="base_files"></a> Generating Base Files
=================
Two manage.py commands are provided to easily create appliations - one for simple algorithms (band math, any application that should be run on a mosaic) and a more flexible base used for more complex concepts.

```
python manage.py start_bandmath_app app_name
python manage.py start_dc_algorithm_app app_name
```

These commands do a few things:

* Copy the associated base files to apps/app_name
* Rename all of the templated values for app_name in all of the Python files, models, views, forms, tasks, etc.
* Create a dc_algorithm.models.Application model for your new app
* Provides instructions on next steps to get your application working

The instructions include to run the migrations and to initialize the database with your new models. These base files contain a few `TODO:` statements within the files, marking where inputs are required. To integrate a new algorithm, generate an app using the command above, grep/search for instance of `TODO:` and follow the instructions there.

Apps come in two main classes - Band math-like apps and more complex apps. Band math apps perform compositing over the selected time and geographic area then perform some function on the resulting mosaic. The dc_algorithm app is set up to be more general and will require more input. As a general rule, if an algorithm doesn't have a time series component, you can use the band math app.

For example, fractional cover involves creating a mosaic and running a computationally intensive function on the resulting data, so the band math base app was used. Coastal change involves non standard time chunking, animation generation, etc. so the more generalized app was used.

<a name="band_math_app"></a> Basic Applications
=================
For a basic application, there are very few changes required to have a functional app. After generating the base files, run the migrations commands as seen below.

```
python manage.py makemigrations
python manage.py migrate
```

Now you will have all of the base tables generated in the database and are ready to implement your algorithm. If you search for `TODO` in that directory, there will only be one occurrence in `tasks.py` and one in models.

tasks.py
```
  def _apply_band_math(dataset):
      #TODO: apply your band math here!
      return (dataset.nir - dataset.red) / (dataset.nir + dataset.red)

  dataset = xr.open_dataset(chunk[0])
  dataset['band_math'] = _apply_band_math(dataset)
```

Replace the expression above with your band math-like algorithm. If it is somewhat more complicated, like fractional cover, the snippet will look like the snippet below:

```
  def _apply_band_math(dataset):
      clear_mask = create_cfmask_clean_mask(dataset.cf_mask) if 'cf_mask' in dataset else create_bit_mask(
          dataset.pixel_qa, [1, 2])
      # mask out water manually. Necessary for frac. cover.
      wofs = wofs_classify(dataset, clean_mask=clear_mask, mosaic=True)
      clear_mask[wofs.wofs.values == 1] = False

      return frac_coverage_classify(dataset, clean_mask=clear_mask)

  dataset = xr.open_dataset(chunk[0])
  dataset = xr.merge([dataset, _apply_band_math(dataset)])
```

Now that you've implemented your algorithm, you'll need to handle the output. The base application will produce a single true color mosaic and the result of your band math. To do this, a color scale needs to be provided. The default color scale is a simple red->green scale for 0%->100% - to replace this, create a [GDALDEM compatible color scale](http://www.gdal.org/gdaldem.html#gdaldem_color_relief) and name it the same as your app (app_name) and place it in utils/color_scales.

```
-0.40 172 21 14
-0.30 247 103 50
-0.20 249 133 20
-0.10 255 204 37
0.0 255 255 255
0.08 124 250 127
0.16 39 216 64
0.24 16 165 1
0.32 51 98 54
0.40 3 49 2
nan 0 0 0
```

Now that this is all complete, you can see your working application by:

* Restarting Apache2
* Restarting Celery workers
* Go to your site and select your application under Tools, choose your area, and submit a task.

<a name="complex_app"></a> Complex Applications
=================
The process for implementing an advanced application is similar to the band math app. Generate the base application using the manage.py command, but don't run the migrations yet. You can start by Grepping/Searching for all instance of `TODO` and filling in the information that you're able to.

Determine what additional input parameters are required. Add these input parameters to the form in the app's forms.py. It is at this step that you can also extend the base DataSelectionForm to change parameters as wel, e.g. for coastal change, we override time start and time end to be years rather than dates.

```
class AdditionalOptionsForm(forms.Form):
    """
    Django form to be created for selecting information and validating input for:
        result_type
        band_selection
        title
        description
    Init function to initialize dynamic forms.
    """

    animated_product = forms.ModelChoiceField(
        queryset=None,
        to_field_name="id",
        empty_label=None,
        help_text='Generate a .gif containing coastal change over time.',
        label='Generate Time Series Animation',
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, *args, **kwargs):
        datacube_platform = kwargs.pop('datacube_platform', None)
        super(AdditionalOptionsForm, self).__init__(*args, **kwargs)
        self.fields["animated_product"].queryset = AnimationType.objects.all().order_by('pk')
```

Grep/search for `TODO` in `models.py` and follow the instructions at each step - this is a little more involved, so more base knowledge will be required. Ensure that each new form element is found in the Query class, and the validation is handled in the `get_or_create_query_from_post` function. Enumerate all of your output products in the Result model, and make note of them for later use in tasks.py.

Now that your models.py has been updated with all unused fields removed, you can now run the migrations to initialize the database.

In tasks.py, implement your algorithm by filling in all the `TODO` blocks. Add all of your result paths in the final task and create images/data products from the outputs.

A few general tips/tricks:

* Only a single NetCDF storage unit is passed from task to task, along with a metadata dict and some general chunk details. If you have multiple data products, merge them into a single NetCDF before writing to disk.
* The main Celery processing pipeline may seem confusing, but due to some weird issues with how Celery interprets/unrolls groups and chords it can't be helped. If you want to add additional steps, do so with the '|' like the combination functions are added. 

<a name="templates"></a> Template Changes
=================
Template changes are the last step in the app development process. The base apps include only the common features - time start/end, execution times, geographic bounds. Make the following changes to add more data to your template.

* In all the templates (there should be four of them), add any additional query parameters (fields you added to Query in models.py)
* In output_list.html, modify the entries in the Data Guide section so that they are accurate to your output products. Additionally, ensure that the options cover all of the output products in the download_options block
* In results_list.html, in the task_table_rows block add checkbox inputs for any additional image outputs that should be displayed on the map. Make sure that the function in the functions_block handles this - removing old images, adding new, highlighting.
* In results_list.html in the meta_table_rows block, add any additional 'full task' metadata that exists on the task model.
* In results_list.html in the metadata_dl_block, ensure that the zipped fields corresponds with the fields enumerated on your Metadata model.
