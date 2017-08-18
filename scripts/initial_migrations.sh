#!/usr/bin/bash
python manage.py makemigrations
python manage.py makemigrations {dc_algorithm,accounts,coastal_change,custom_mosaic_tool,fractional_cover,ndvi_anomaly,slip,task_manager,tsm,water_detection,cloud_coverage,urbanization,nazeer_chlorophyll,watanabe_chlorophyll,spectral_indices}
python manage.py migrate

python manage.py loaddata db_backups/init_database.json
