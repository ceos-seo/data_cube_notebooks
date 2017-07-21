from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

from . import views

#url(r'^(?P<url>.*/)$', views.flatpage),

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^workshop', views.workshop, name="workshop"),
    url(r'^submit_feedback', views.submit_feedback, name='submit_feedback'),
]
