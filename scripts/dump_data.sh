#!/usr/bin/bash
python manage.py dumpdata dc_algorithm custom_mosaic_tool coastal_change fractional_cover ndvi_anomaly slip tsm water_detection cloud_coverage urbanization spectral_indices > db_backups/init_database.json
