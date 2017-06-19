from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField


class Dataset(models.Model):
    id = models.UUIDField(primary_key=True)  # This field type is a guess.
    metadata_type_ref = models.ForeignKey('MetadataType', models.DO_NOTHING, db_column='metadata_type_ref')
    dataset_type_ref = models.ForeignKey('DatasetType', models.DO_NOTHING, db_column='dataset_type_ref')
    metadata = JSONField()  # This field type is a guess.
    archived = models.DateTimeField(blank=True, null=True)
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset'


class DatasetLocation(models.Model):
    dataset_ref = models.ForeignKey(Dataset, models.DO_NOTHING, db_column='dataset_ref')
    uri_scheme = models.TextField()
    uri_body = models.TextField()
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_location'
        unique_together = (('dataset_ref', 'uri_scheme', 'uri_body'),)


class DatasetSource(models.Model):
    dataset_ref = models.ForeignKey(Dataset, models.DO_NOTHING, db_column='dataset_ref', related_name='dataset_ref')
    classifier = models.TextField()
    source_dataset_ref = models.ForeignKey(
        Dataset, models.DO_NOTHING, db_column='source_dataset_ref', related_name='source_dataset_ref')

    class Meta:
        managed = False
        db_table = 'dataset_source'
        unique_together = (('source_dataset_ref', 'dataset_ref'), ('dataset_ref', 'classifier'),)


class DatasetType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.TextField(unique=True)
    metadata = JSONField()  # This field type is a guess.
    metadata_type_ref = models.ForeignKey('MetadataType', models.DO_NOTHING, db_column='metadata_type_ref')
    definition = JSONField()  # This field type is a guess.
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_type'


class MetadataType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.TextField(unique=True)
    definition = JSONField()  # This field type is a guess.
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'metadata_type'
