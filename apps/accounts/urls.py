from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^registration', views.registration, name='registration'),
    url(r'^(?P<uuid>[^/]+)/activate', views.activate, name='activate'),
    url(r'^lost_password', views.lost_password, name='lost_password'),
    url(r'^(?P<uuid>[^/]+)/reset', views.reset, name='reset'),
    url(r'^password_change', views.password_change, name='password_change'),
    url(r'^login', views.login, name='login'),
    url(r'^logout', views.logout, name='logout'),
]
