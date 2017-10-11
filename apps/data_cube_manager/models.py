from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import Q
from django.conf import settings

from dateutil.parser import parse
from collections import Iterable
from glob import glob
import uuid


class Dataset(models.Model):
    id = models.UUIDField(primary_key=True)  # This field type is a guess.
    metadata_type_ref = models.ForeignKey('MetadataType', models.CASCADE, db_column='metadata_type_ref')
    dataset_type_ref = models.ForeignKey('DatasetType', models.CASCADE, db_column='dataset_type_ref')
    metadata = JSONField()  # This field type is a guess.
    archived = models.DateTimeField(blank=True, null=True)
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset'

    @classmethod
    def filter_datasets(cls, cleaned_form_data):
        """Custom filtering based on form data found in forms.DatasetFilterForm

        dataset_type_ref and is optional and can be null, so that needs to be checked.
        Uses Django Q objects to combine and/or operations on queries. Does a BB intersection
        and time query to filter datasets.

        Args:
            dict representing cleaned form data from forms.DatasetFilterForm

        Returns:
            Queryset of Datasets

        """
        base_query = Q()
        if 'dataset_type_ref' in cleaned_form_data:
            dataset_type_ref = cleaned_form_data['dataset_type_ref'] if isinstance(
                cleaned_form_data['dataset_type_ref'], Iterable) else [cleaned_form_data['dataset_type_ref']]
            base_query &= Q(dataset_type_ref__in=dataset_type_ref)
        """
        bool doOverlap(Point l1, Point r1, Point l2, Point r2)
            {
                // If one rectangle is on left side of other
                if (l1.x > r2.x || l2.x > r1.x)
                    return false;

                // If one rectangle is above other
                if (l1.y < r2.y || l2.y < r1.y)
                    return false;

                return true;
            }
        """

        longitude_query = ~Q(
            Q(metadata__extent__coord__ul__lon__gt=cleaned_form_data['longitude_max']) | Q(
                metadata__extent__coord__lr__lon__lt=cleaned_form_data['longitude_min']))

        latitude_query = ~Q(
            Q(metadata__extent__coord__ul__lat__lt=cleaned_form_data['latitude_min']) | Q(
                metadata__extent__coord__lr__lat__gt=cleaned_form_data['latitude_max']))

        time_query = Q(metadata__extent__center_dt__lte=cleaned_form_data['end_date'].isoformat(),
                       metadata__extent__center_dt__gte=cleaned_form_data['start_date'].isoformat())
        base_query &= latitude_query & longitude_query & time_query

        return cls.objects.using('agdc').filter(base_query)

    def get_dataset_table_columns(self):
        """Returns the metadata columns specified in the datasets.html template

        id, platform, instrument, product type, upper left/lower right, center dt, format

        """
        return [
            self.id, self.metadata['platform']['code'], self.metadata['instrument']['name'],
            self.metadata['product_type'], "{:.2f}, {:.2f}".format(self.metadata['extent']['coord']['ul']['lon'],
                                                                   self.metadata['extent']['coord']['ul']['lat']),
            "{:.2f}, {:.2f}".format(self.metadata['extent']['coord']['lr']['lon'],
                                    self.metadata['extent']['coord']['lr']['lat']),
            self.metadata['extent']['center_dt'], self.metadata['format']['name']
        ]


class DatasetLocation(models.Model):
    dataset_ref = models.ForeignKey(Dataset, models.CASCADE, db_column='dataset_ref')
    uri_scheme = models.TextField()
    uri_body = models.TextField()
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_location'
        unique_together = (('dataset_ref', 'uri_scheme', 'uri_body'),)


class DatasetSource(models.Model):
    dataset_ref = models.ForeignKey(
        Dataset, models.CASCADE, db_column='dataset_ref', related_name='dataset_ref', primary_key=True)
    classifier = models.TextField()
    source_dataset_ref = models.ForeignKey(
        Dataset, models.CASCADE, db_column='source_dataset_ref', related_name='source_dataset_ref')

    class Meta:
        managed = False
        db_table = 'dataset_source'
        unique_together = (('source_dataset_ref', 'dataset_ref'), ('dataset_ref', 'classifier'),)


class DatasetType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.TextField(unique=True)
    metadata = JSONField()  # This field type is a guess.
    metadata_type_ref = models.ForeignKey('MetadataType', models.CASCADE, db_column='metadata_type_ref')
    definition = JSONField()  # This field type is a guess.
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_type'

    def __str__(self):
        return self.name + (" - Ingested only" if 'managed' in self.definition else " - Source only")

    def get_description(self):
        return self.definition['description']

    def get_platform(self):
        return self.metadata['platform']['code']

    def get_instrument(self):
        return self.metadata['instrument']['name']

    def get_processing_level(self):
        return self.metadata['product_type']


class MetadataType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.TextField(unique=True)
    definition = JSONField()  # This field type is a guess.
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'metadata_type'


class IngestionRequest(models.Model):
    """Ingestion subset request model class containing all data required to ingest a sample cube.

    This model will be submitted to the tasks processing pipeline that will create a db with the user,
    ingest data based on the start/end date + geographic bounds query, and create a bulk download script.

    total storage units and storage units processed will be updated by the task/update_storage_unit count with
    current progress.

    """

    user = models.CharField(max_length=50)
    db_name = models.CharField(max_length=50, default=uuid.uuid4)

    # this can't be a fk since the agdc schema isn't managed by Django
    dataset_type_ref = models.SmallIntegerField()
    ingestion_definition = JSONField()

    start_date = models.DateField('start_date')
    end_date = models.DateField('end_date')
    latitude_min = models.FloatField()
    latitude_max = models.FloatField()
    longitude_min = models.FloatField()
    longitude_max = models.FloatField()

    total_storage_units = models.IntegerField(default=0)
    storage_units_processed = models.IntegerField(default=0)
    download_script_path = models.CharField(max_length=100, default="")

    status = models.CharField(max_length=50, default="WAIT")
    message = models.CharField(max_length=150, default="Please wait while your Data Cube is created.")

    def __str__(self):
        return self.user

    def update_status(self, status, message):
        self.status = status
        self.message = message
        self.save()

    def get_database_name(self):
        return self.user + str(self.pk)

    def get_database_dump_path(self):
        return "{}/datacube_dump".format(self.ingestion_definition['location'])

    def get_base_data_path(self):
        return self.ingestion_definition['location']

    def update_storage_unit_count(self):
        self.storage_units_processed = len(glob(self.get_base_data_path() + "/*.nc"))
        self.save()


class IngestionDetails(models.Model):
    """Acts as a cached version of the Data Cube ingested datasets details

    Updated by a celery task that runs periodically, then served to the visualization tool
    as a json response.

    """
    dataset_type_ref = models.IntegerField(primary_key=True)
    product = models.CharField(max_length=100)
    platform = models.CharField(max_length=100, default="")
    global_dataset = models.BooleanField(default=False)

    start_date = models.DateField('start_date', blank=True, null=True)
    end_date = models.DateField('end_date', blank=True, null=True)
    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    pixel_count = models.BigIntegerField(default=0)
    scene_count = models.BigIntegerField(default=0)

    def __str__(self):
        return "{} - {}".format(self.product, self.platform)

    def get_serialized_response(self):
        """Returns json serializable data as required by the visualization tool

        {
    		"product": "ls5_ledaps_bangladesh",
    		"time_extents": "1990-01-23 03:46:40 - 2011-09-30 04:12:38",
    		"lon_extents": [89.405167326, 92.233509888],
    		"lat_extents": [23.524819572000002, 26.002656],
    		"pixel_count": 87756764,
    		"scene_count": 186
    	}

        """

        return {
            'dataset_type_ref': self.dataset_type_ref,
            'product': self.product,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'latitude_min': self.latitude_min,
            'latitude_max': self.latitude_max,
            'longitude_min': self.longitude_min,
            'longitude_max': self.longitude_max,
            'pixel_count': self.pixel_count,
            'scene_count': self.scene_count
        }

    def update_with_query_metadata(self, metadata_dict):
        """Update this model using a DataAccessApi.get_query_metadata call

        {
            'lat_extents': (0, 0),
            'lon_extents': (0, 0),
            'time_extents': (0, 0),
            'scene_count': 0,
            'pixel_count': 0,
            'tile_count': 0,
            'storage_units': {}
        }

        """
        self.start_date = metadata_dict['time_extents'][0]
        self.end_date = metadata_dict['time_extents'][1]
        self.latitude_min = metadata_dict['lat_extents'][0]
        self.latitude_max = metadata_dict['lat_extents'][1]
        self.longitude_min = metadata_dict['lon_extents'][0]
        self.longitude_max = metadata_dict['lon_extents'][1]

        self.pixel_count = metadata_dict['pixel_count']
        self.scene_count = metadata_dict['tile_count']

        self.save()
