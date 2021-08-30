#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='odc-gee',
      version='2.24',
      description='Google Earth Engine indexing tools for Open Data Cube',
      author='Andrew Lubawy',
      author_email='andrew.m.lubawy@ama-inc.com',
      install_requires=[
          "google-auth>=1.11.0,<=1.32.0"
          "click-plugins>=1.1.1",
          "click>=7.1.2",
          "datacube>=1.8.3",
          "earthengine-api>=0.1.24",
          "numpy>=1.18.4",
          "rasterio>=1.1.8",
          ],
      packages=find_packages(),
      scripts=['scripts/index_gee', 'scripts/new_product'],)
