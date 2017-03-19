from django.db import models
import uuid


class Activation(models.Model):
    username = models.CharField(max_length=30)
    url = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time = models.DateTimeField()


class Reset(models.Model):
    username = models.CharField(max_length=30)
    url = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time = models.DateTimeField()
