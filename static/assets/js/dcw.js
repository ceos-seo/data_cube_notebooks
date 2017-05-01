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
var task_obj = {};

// only messages being posted are to start tasks. Tasks are either new or from history.
self.addEventListener("message", function(e) {
    tool_name = e.data.tool_name;
    switch (e.data.status) {
        case "NEW":
            getNewResult(e);
            break;
        case "HISTORY":
            getResultFromHistory(e);
            break;
        case "SINGLE":
            getSingleResult(e);
            break;
        default:
            close();
            break;
    }
}, false);


//Used to load a result using the task history box.
function getResultFromHistory(e) {
    task_obj['id'] = e.data.id;
    task_obj['title'] = e.data.title;
    csrftoken = e.data.csrf;
    postMessage({
        'status': "START",
        'task': task_obj
    });
    checktask();
}

//uses form data to generate a new task.
function getNewResult(e) {
    task_obj['task_data'] = e.data.form_data;
    csrftoken = e.data.csrf;
    addNewtask();
}

//starts the task and sets the checktask interval timer. Posts info used
//to init a loading bar.
function addNewtask() {
    var request = new XMLHttpRequest();
    request.open("POST", '/' + tool_name + '/submit', false);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("X-CSRFToken", csrftoken);
    request.send(task_obj['task_data']);
    task_obj['id'] = -1;
    if (request.status != 200) {
        error("There was a problem submitting your task, please check your connection.");
        return;
    } else {
        var response = JSON.parse(request.response);
        if (response.status == "ERROR") {
            if (response.message)
                error(response.message);
            else
                error("There was a problem with your task, please try again.");
            return;
        }
        task_obj['id'] = response.id;
        task_obj['title'] = response.title;
        postMessage({
            'status': "START",
            'task': task_obj
        });
        setTimeout(checktask, 3000);
    }
}

//used to load a single scene from a task.
function getSingleResult(e) {
    csrftoken = e.data.csrf;

    var request = new XMLHttpRequest();
    request.open("POST", '/' + tool_name + '/submit_single', false);
    //request.timeout = 100;
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("X-CSRFToken", csrftoken);
    request.send('id=' + e.data.id + '&date=' + e.data.date);

    if (request.status != 200) {
        error("There was a problem submitting your task, please check your connection.");
        return;
    } else {
        var response = JSON.parse(request.response);
        if (response.status == "ERROR") {
            if (response.message)
                error(response.message);
            else
                error("There was a problem with your task, please try again.");
            return;
        }
        task_obj['id'] = response.id;
        task_obj['title'] = response.title;
        postMessage({
            'status': "START",
            'task': task_obj
        });
        setTimeout(checktask, 3000);
    }
}

//uses the task_obj values to check on the status of the submitted task.
// When waiting for a result, post messsages with progress updates.
function checktask() {
    var request = new XMLHttpRequest();
    var parameters = "?id=" + task_obj['id']
    request.open("GET", '/' + tool_name + '/result' + parameters, false);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("X-CSRFToken", csrftoken);
    request.send();
    if (request.status != 200) {
        error("There was a problem submitting your task, please check your connection.");
        return;
    } else {
        var response = JSON.parse(request.response);
        if (response.status == "ERROR") {
            if (response.message)
                error(response.message);
            else
                error("There was a problem with your task, please try again.");
            return;
        }
        if (response.status == "WAIT") {
            if (response.progress) {
                postMessage({
                    'status': "UPDATE",
                    'id': task_obj['id'],
                    'value': response.progress,
                });
            }
            setTimeout(checktask, 3000);
        } else {
            //just pass in all the attributes from the result obj.
            for (var attr in response)
                task_obj[attr] = response[attr];
            postResult();
        }
    }
}

//just in case we want to do/add more to this in the future.
function postResult() {
    postMessage({
        'status': "RESULT",
        'task': task_obj
    });
    close();
}

function error(message) {
    postMessage({
        'status': "ERROR",
        'id': task_obj['id'],
        'message': message
    });
    close();
}
