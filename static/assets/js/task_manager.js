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


$(document).ready(function() {
    $('#query-list-table-full')
    	.on('draw.dt', function() {applyEvenAndOddClasses();})
	.DataTable( {
	    "order": [[1, "asc"]],
	    "bLengthChange": false,
	    "bPaginate": true
	});
});

function applyEvenAndOddClasses() {
    var table = document.getElementById("query-list-table-full");
    for (var i = 0, row; row = table.rows[i]; i++) {
	if (i != 0 && i % 2 == 0) {
	    for (var j = 0, col; col = row.cells[j]; j++) {
		col.className='even';
	    }
	}
	else if (i != 0 && i % 2 != 0) {
	    for (var j = 0, col; col = row.cells[j]; j++) {
		col.className='odd';
	    }
	}
    }
}
