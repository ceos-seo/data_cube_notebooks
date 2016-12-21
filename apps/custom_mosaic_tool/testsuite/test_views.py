# Unit test dependencies
from django.test import TestCase, RequestFactory
from django.test.client import Client

# Other dependencies
from django.core.urlresolvers import reverse
from django.core import management
from django.utils.encoding import force_text
from ..views import build_headers_dictionary, format_headers
from ..models import Query
from django.contrib.auth.models import User
from collections import OrderedDict

class TestViews(TestCase):

    # Used to show for diffs greater than certain characters.
    maxDiff = None
    
    def setUp(self):
        self.client = Client()
        management.call_command('loaddata', 'db_backups/data_dump.json', verbosity=0)

    def test_custom_mosaic_tool_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('custom_mosaic_tool',kwargs={'area_id':'kenya'}))
        self.assertEqual(response.status_code, 200)

    def test_custom_mosaic_tool_logged_out(self):
        response = self.client.get(reverse('custom_mosaic_tool',kwargs={'area_id':'kenya'}))
        expected_url_redirect = reverse('login') + "?next=" + reverse('custom_mosaic_tool',kwargs={'area_id':'kenya'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url_redirect)
        
    def test_submit_new_request_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'time_start': "01/01/2005", 'time_end': "01/01/2006",'band_selection': "1", 'platform': "LANDSAT_7", 'result_type': "true_color", 'latitude_max': "1", 'latitude_min': "0", 'longitude_max': "35", 'longitude_min': "34", 'title': "Sample Title", 'description': "Sample Description", 'area_id': "kenya"}
        response = self.client.post(reverse('submit_new_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'OK', 'request_id': '2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color'})
        
    def test_submit_new_request_logged_in_no_title_no_description(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'time_start': "01/01/2005", 'time_end': "01/01/2006",'band_selection': "1", 'platform': "LANDSAT_7", 'result_type': "true_color", 'latitude_max': "1", 'latitude_min': "0", 'longitude_max': "35", 'longitude_min': "34", 'area_id': "kenya"}
        response = self.client.post(reverse('submit_new_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'OK', 'request_id': '2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color'})
        
    def test_submit_new_request_logged_in_no_data_error(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.post(reverse('submit_new_request'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'ERROR'})
        
    def test_submit_new_request_logged_in_no_post_error(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('submit_new_request'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'ERROR'})

    def test_submit_new_request_logged_out(self):
        response = self.client.post('submit_new_request')
        self.assertEqual(response.status_code, 404)
        
    def test_submit_new_single_request_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color', 'date': '01/01/2005'}
        response = self.client.post(reverse('submit_new_single_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'OK', 'request_id': '2005-01-01-2005-01-02-1.0-0.0-35.0-34.0-blue-LANDSAT_7-ls7_ledaps-true_color'})
    
    def test_submit_new_single_request_logged_in_no_query(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '', 'date': '01/01/2005'}
        response = self.client.post(reverse('submit_new_single_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'ERROR'})
    
    def test_submit_new_single_request_logged_in_not_post(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('submit_new_single_request'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'ERROR'})
    
    def test_submit_new_single_request_logged_out(self):
        response = self.client.post(reverse('submit_new_single_request'))
        self.assertEqual(response.status_code, 302)

    def test_cancel_request_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '2011-01-01-2012-01-01-1-0.4-37-35-green,red,swir2-LANDSAT_7--nir_red_green', 'user_id': 'localuser'}
        response = self.client.post(reverse('cancel_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg':'OK'})

    def test_cancel_request_logged_in_no_query(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'user_id': 'localuser'}
        response = self.client.post(reverse('cancel_request'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'ERROR'})
        
    def test_submit_new_request_logged_in_not_post_error(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('cancel_request'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content),{'msg': 'ERROR'})
        
    def test_cancel_request_logged_out(self):
        response = self.client.post('cancel_request')
        self.assertEqual(response.status_code, 404)

    def test_get_result_logged_in_result_ok(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color'}
        response = self.client.post(reverse('get_result'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'OK', 'result': {'data': '/tilestore/result/2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color.tif', 'result': '/tilestore/result/2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color.png', 'result_filled': '/tilestore/result/2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color_filled.png', 'min_lat': 0.0, 'max_lat': 1.0, 'min_lon': 34.0, 'max_lon': 35.0, 'total_scenes': 14, 'scenes_processed': 14}})        

    def test_get_result_logged_in_result_wait(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '2011-01-01-2012-01-01-1-0.4-37-35-green,red,swir2-LANDSAT_7--nir_red_green'}
        response = self.client.post(reverse('get_result'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'WAIT', 'result': {'total_scenes': 8, 'scenes_processed': 8}})
        
    def test_get_result_logged_in_result_error(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': '2009-01-01-2010-01-01-0.8-0.6-36.4-36.2-swir2-LANDSAT_7--nir_swir_swir'}
        response = self.client.post(reverse('get_result'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'ERROR', 'error_msg': '/tilestore/result/2009-01-01-2010-01-01-0.8-0.6-36.4-36.2-swir2-LANDSAT_7--nir_swir_swir.png'})
        
    def test_get_result_logged_in_no_query_id(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'something_else': 'some data'}
        response = self.client.post(reverse('get_result'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'ERROR'})
        
    def test_get_result_logged_in_no_result_found(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_id': 'deliberately wrong id'}
        response = self.client.post(reverse('get_result'), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'WAIT'})
        
    def test_get_result_logged_in_not_post(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_result'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_text(response.content), {'msg': 'ERROR'})
        
    def test_get_result_logged_out(self):
        response = self.client.get(reverse('get_result'))
        self.assertEqual(response.status_code, 302)
        
    def test_get_query_history_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_query_history', kwargs={'area_id':'kenya'}))
        self.assertEqual(len(response.context['query_history']), 4)

    def test_get_query_history_logged_out(self):
        response = self.client.get(reverse('get_query_history', kwargs={'area_id':'kenya'}))
        self.assertEqual(response.status_code, 302)

    def test_build_headers_dictionary(self):
        actual_dictionary = build_headers_dictionary(Query())
        expected_dictionary = {'Query': ['area_id','title','query_start','query_end','query_type','platform','product','measurements','time_start','time_end','latitude_min','latitude_max','longitude_min','longitude_max','complete','id']}
        self.assertEqual(actual_dictionary, expected_dictionary)
        
    def test_format_headers(self):
        unformatted_dictionary = build_headers_dictionary(Query())
        actual_list = format_headers(unformatted_dictionary)
        expected_list = ['Area Id','Title','Query Start','Query End','Query Type','Platform','Product','Measurements','Time Start','Time End','Latitude Min','Latitude Max','Longitude Min','Longitude Max','Complete','Id']
        self.assertEqual(actual_list, expected_list)
        
    def test_get_task_manager_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_task_manager'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context[-1]['data_dictionary'])
        self.assertTrue(response.context[-1]['formatted_headers_dictionary'])

    def test_get_task_manager_logged_out(self):
        response = self.client.get(reverse('get_task_manager'))
        self.assertEqual(response.status_code, 302)
        expected_url_redirect = reverse('login') + "?next=" + reverse('get_task_manager')
        self.assertRedirects(response, expected_url_redirect)

    def test_get_query_details_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_query_details', args=(1,)))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context[-1]['query'])
        self.assertTrue(response.context[-1]['metadata'])
        self.assertTrue(response.context[-1]['result'])
        
    def test_get_query_details_logged_out(self):
        response = self.client.get(reverse('get_query_details', args=(1,)))
        self.assertEqual(response.status_code, 302)
        expected_url_redirect = reverse('login') + "?next=" + reverse('get_query_details', args=(1,))
        self.assertRedirects(response, expected_url_redirect)

    def test_get_results_list_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_ids[]': ['2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color', '2006-01-01-2007-01-01-0.2-0-35.2-35-green-LANDSAT_7--true_color', '2007-01-01-2008-01-01-0.4-0.2-35.4-35.2-red,nir,swir1-LANDSAT_7--true_color']}
        response = self.client.post(reverse('get_results_list', kwargs={'area_id':'kenya'}), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['queries'])
        self.assertTrue(response.context['metadata_entries'])
        
    def test_get_results_list_logged_in_not_post(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_results_list', kwargs={'area_id':'kenya'}))
        self.assertEqual(response.content, b'Invalid Request.')
        
    def test_get_results_list_logged_out(self):
        response = self.client.post(reverse('get_results_list', kwargs={'area_id':'kenya'}))
        self.assertEqual(response.status_code, 302)

    def test_get_output_list_logged_in(self):
        self.client.login(username='localuser', password='amadev12')
        json_data = {'query_ids[]': ['2005-01-01-2006-01-01-1-0-35-34-blue-LANDSAT_7--true_color', '2006-01-01-2007-01-01-0.2-0-35.2-35-green-LANDSAT_7--true_color', '2007-01-01-2008-01-01-0.4-0.2-35.4-35.2-red,nir,swir1-LANDSAT_7--true_color']}
        response = self.client.post(reverse('get_output_list', kwargs={'area_id':'kenya'}), json_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['data'])
        
    def test_get_output_list_logged_in_not_post(self):
        self.client.login(username='localuser', password='amadev12')
        response = self.client.get(reverse('get_output_list', kwargs={'area_id':'kenya'}))
        self.assertEqual(response.content, b'Invalid Request.')
        
    def test_get_output_list_logged_out(self):
        response = self.client.post(reverse('get_output_list', kwargs={'area_id':'kenya'}))
        self.assertEqual(response.status_code, 302)
