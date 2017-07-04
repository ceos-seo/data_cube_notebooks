from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import Q
from django.conf import settings

from dateutil.parser import parse
from collections import Iterable
from glob import glob

from apps.data_cube_manager.templates.bulk_downloader import base_downloader_script, static_script


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

        dataset_type_ref and managed are optional and can be null, so those need to be checked.
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
        if 'managed' in cleaned_form_data:
            base_query &= Q(dataset_type_ref__definition__managed=cleaned_form_data['managed'])
        # range intersections done like:
        #   if x1[0] > x2[0] and x1[0] < x2[1] or x1[1] > x2[0] and x1[1] < x2[1]: return True
        latitude_query = Q(metadata__extent__coord__lr__lat__gte=cleaned_form_data['latitude_min'],
                           metadata__extent__coord__lr__lat__lt=cleaned_form_data['latitude_max']) | Q(
                               metadata__extent__coord__ul__lat__gt=cleaned_form_data['latitude_min'],
                               metadata__extent__coord__ul__lat_lt=cleaned_form_data['latitude_max']) | Q(
                                   metadata__extent__coord__lr__lat__lt=cleaned_form_data['latitude_max'],
                                   metadata__extent__coord__ul__lat_gt=cleaned_form_data['latitude_min'])

        longitude_query = Q(metadata__extent__coord__ul__lon__gt=cleaned_form_data['longitude_min'],
                            metadata__extent__coord__ul__lon__lt=cleaned_form_data['longitude_max']) | Q(
                                metadata__extent__coord__lr__lon__gt=cleaned_form_data['longitude_min'],
                                metadata__extent__coord__lr__lon_lt=cleaned_form_data['longitude_max']) | Q(
                                    metadata__extent__coord__ul__lon__lt=cleaned_form_data['longitude_max'],
                                    metadata__extent__coord__lr__lon_gt=cleaned_form_data['longitude_min'])

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
    user = models.CharField(max_length=50)

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
    message = models.CharField(max_length=100, default="Please wait while your Data Cube is created.")

    def update_status(self, status, message):
        self.status = status
        self.message = message
        self.save()

    def get_database_dump_path(self):
        return "{}/datacube_dump".format(self.ingestion_definition['location'])

    def get_base_data_path(self):
        return self.ingestion_definition['location']

    def update_storage_unit_count(self):
        self.storage_units_processed = len(glob(self.get_base_data_path() + "/*.nc"))
        if self.storage_units_processed == self.total_storage_units:
            self.generate_download_script()
            self.update_status("OK", "Please follow the directions on the right side panel to download your cube.")

    def generate_download_script(self):
        self.download_script_path = self.get_base_data_path() + "/bulk_downloader.py"

        file_list = ",".join('"{}"'.format(path) for path in glob(self.get_base_data_path() + '/*.nc'))
        download_script = base_downloader_script.format(
            file_list=file_list,
            database_dump_file=self.get_database_dump_path(),
            base_host=settings.BASE_HOST,
            base_data_path=self.get_base_data_path()) + static_script

        with open(self.download_script_path, "w+") as downloader:
            downloader.write(download_script)
