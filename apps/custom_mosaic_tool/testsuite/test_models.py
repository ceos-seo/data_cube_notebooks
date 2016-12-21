# Unit test dependencies
from django.test import TestCase

# Other dependencies
from ..models import Query, ResultType, Metadata
from ..forms import DataSelectForm, GeospatialForm
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core import management

import unittest

class TestQuery(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def test_query_info_with_database(self):
        query = Query.objects.get(id = 1)
        self.assertEqual(query.query_type, "true_color")

    def test_get_query_id(self):
        query = Query.objects.get(id = 1)
        self.assertEqual(query.generate_query_id(), "2005-01-01-2006-01-01-1.0-0.0-35.0-34.0-blue-LANDSAT_7-ls7_ledaps-true_color")
        
    def test_get_type_name(self):
        query = Query.objects.get(id = 1)
        result_type = query.get_type_name()
        self.assertEqual(result_type, "True color")

class TestMetadata(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)
    
    def test_acquisition_list_as_list(self):
        metadata = Metadata.objects.get(id = 1)
        actual_acquisition_list = metadata.acquisition_list_as_list()
        acquisition_list_string = "01/07/2005,01/23/2005,02/24/2005,03/12/2005,03/28/2005,04/13/2005,05/15/2005,05/31/2005,06/16/2005,07/02/2005,08/03/2005,09/04/2005,09/20/2005,10/06/2005,"
        expected_acquisition_list = acquisition_list_string.rstrip(',').split(',')
        self.assertEqual(actual_acquisition_list, expected_acquisition_list)
        self.assertTrue(actual_acquisition_list)

    def test_clean_pixels_list_as_list(self):
        metadata = Metadata.objects.get(id = 1)
        actual_clean_pixel_list = metadata.clean_pixels_list_as_list()
        clean_pixels_string = "7354,0,16194,88,5813,0,5699,1989,0,0,9011,617,3385,3419,"
        expected_clean_pixel_list = clean_pixels_string.rstrip(',').split(',')
        self.assertEqual(actual_clean_pixel_list,expected_clean_pixel_list)
        self.assertTrue(actual_clean_pixel_list)

    def test_clean_pixels_precentages_as_list(self):
        metadata = Metadata.objects.get(id = 1)
        actual_clean_pixel_percentage_list = metadata.clean_pixels_percentages_as_list()
        clean_pixel_percentage_string = "0.0533712888303,0.0,0.11752714867,0.000638655618312,0.0421875580596,0.0,0.0413602087359,0.0144350684639,0.0,0.0,0.0653968838251,0.00447784677839,0.0245664689544,0.0248132222614,"
        expected_clean_pixel_percentage_list = clean_pixel_percentage_string.rstrip(',').split(',')
        self.assertEqual(actual_clean_pixel_percentage_list, expected_clean_pixel_percentage_list)
        self.assertTrue(actual_clean_pixel_percentage_list)

    # TODO(map) : Not sure how to test yet.  Returning a ZIP that could be hard to test values for.
    def test_acquisitions_dates_with_pixels_percentages(self):
        metadata = Metadata.objects.get(id = 1)
        actual_aquisition_dates_list = metadata.acquisitions_dates_with_pixels_percentages()
        self.assertTrue(actual_aquisition_dates_list)

class TestResult(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def stubbed_method(self):
        self.assertTrue(True)
        
class TestSatellite(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def stubbed_method(self):
        self.assertTrue(True)
        
class TestSatelliteBand(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def stubbed_method(self):
        self.assertTrue(True)
        
class TestResultTYpe(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def stubbed_method(self):
        self.assertTrue(True)
        
class TestArea(TestCase):
    
    # Used to show for diffs greater than certain characters.
    maxDiff = None

    def setUp(self):
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def stubbed_method(self):
        self.assertTrue(True)
