#!/usr/bin/bash

python manage.py flush --no-input
python manage.py loaddata db_backups/testing_inputs.json
python manage.py run_test_cases
