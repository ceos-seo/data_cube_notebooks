/* Author: AHDS
   Creation date: 2016-06-23
   Modified by:
   Last modified date:
*/
/*
Copyright 2016 United States Government as represented by the Administrator
of the National Aeronautics and Space Administration. All Rights Reserved.

Portion of this code is Copyright Geoscience Australia, Licensed under the
Apache License, Version 2.0 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the License
at

   http://www.apache.org/licenses/LICENSE-2.0

The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
*/

//Datacube webworker
"use strict";
var tool_name = "";
var csrftoken = null;
var query_obj = {};

// only messages being posted are to start tasks. Tasks are either new or from history.
self.addEventListener("message", function(e) {
	tool_name = e.data.tool_name;
	if(e.data.msg == "NEW") {
		getNewResult(e);
	} else if(e.data.msg == "HISTORY") {
		getResultFromHistory(e);
	} else if(e.data.msg == "SINGLE") {
		getSingleResult(e);
	}
}, false);

//used to load a single scene from a query.
function getSingleResult(e) {
	csrftoken = e.data.csrf;
	query_obj['query_type'] = e.data.result_type;

	var request = new XMLHttpRequest();
	request.open("POST", '/' + tool_name + '/submit_single', false);
	//request.timeout = 100;
	request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	request.setRequestHeader("X-CSRFToken", csrftoken);
	request.send('query_id=' + e.data.query_id + '&date=' + e.data.date);

	if (request.status != 200) {
			error("There was a problem submitting your task, please check your connection");
			return;
	} else {
			var response = JSON.parse(request.response);
			if(response.msg == "ERROR") {
				error("There was a problem submitting your task, please try again.");
				return;
			}
			query_obj['query_id'] = response.request_id;
			postMessage({
					'msg': "START",
					'query': query_obj
			});
			setTimeout(checkQuery, 3000);
	}
}

//Used to load a result using the query history box.
function getResultFromHistory(e) {
	query_obj['query_id'] = e.data.query_id;
	query_obj['query_type'] = e.data.result_type;
	csrftoken = e.data.csrf;
	postMessage({
			'msg': "START",
			'query': query_obj
	});
	checkQuery();
}

//uses form data to generate a new query.
function getNewResult(e) {
	query_obj['query_data'] = e.data.form_data;
	query_obj['query_type'] = e.data.result_type;
	csrftoken = e.data.csrf;
	addNewQuery();
}

//starts the query and sets the checkquery interval timer. Posts info used
//to init a loading bar.
function addNewQuery() {
    var request = new XMLHttpRequest();
    request.open("POST", '/' + tool_name + '/submit', false);
    //request.timeout = 100;
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("X-CSRFToken", csrftoken);
    request.send(query_obj['query_data']);
		query_obj['query_id'] = -1;
    if (request.status != 200) {
        error("There was a problem submitting your task, please check your connection");
				return;
    } else {
        var response = JSON.parse(request.response);
				if(response.msg == "ERROR") {
					error("There was a problem submitting your task, please try again.");
					return;
				}
        query_obj['query_id'] = response.request_id;
				postMessage({
            'msg': "START",
						'query': query_obj
        });
        setTimeout(checkQuery, 3000);
    }
}

//uses the query_obj values to check on the status of the submitted query.
// When waiting for a result, post messsages with progress updates.
function checkQuery() {
    var request = new XMLHttpRequest();
    request.open("POST", '/' + tool_name + '/result', false);
    //request.timeout = 100;
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("X-CSRFToken", csrftoken);
    request.send("query_id=" + query_obj['query_id']);
    if (request.status != 200) {
				error("There was a problem submitting your task, please check your connection");
				return;
    } else {
        var response = JSON.parse(request.response);
				if(response.msg == "ERROR") {
					if(response.error_msg)
						error(response.error_msg);
					else
						error("There was a problem with your task, please try again.");
						return;
				}
        console.log(request.response);
        if (response.msg == "WAIT") {
						if(response.result) {
							if(!isNaN(response.result.total_scenes) && !isNaN(response.result.scenes_processed)) {
								postMessage({
						        'msg': "UPDATE",
						        'query_id': query_obj['query_id'],
										'value': (response.result.scenes_processed / response.result.total_scenes)*100,
						    });
							}
						}
            setTimeout(checkQuery, 3000);
        } else {
						//just pass in all the attributes from the result obj.
						for(var attr in response.result)
							query_obj[attr] = response.result[attr];
            //query_obj['image_url'] = response.result.result;
						//query_obj['image_filled_url'] = response.result.result_filled;
            //query_obj['data_url'] = response.result.data;
						//query_obj['latitude'] = [response.result.min_lat, response.result.max_lat];
						//query_obj['longitude'] = [response.result.min_lon, response.result.max_lon];
            //upper and lower bounds?
            postResult();
        }
    }
}

//just in case we want to do/add more to this in the future.
function postResult() {
    postMessage({
        'msg': "RESULT",
        'query': query_obj
    });
		close();
}

function error(msg) {
	postMessage({
			'msg': "ERROR",
			'query_id': query_obj['query_id'],
			'error_msg': msg
	});
	close();
}
