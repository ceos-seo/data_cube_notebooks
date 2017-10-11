#!/usr/bin/bash

bash scripts/initial_migrations.sh
cp config/.datacube.conf ~/.datacube.conf
sudo cp config/dc_ui.conf /etc/apache2/sites-available/dc_ui.conf
sudo a2dissite 000-default.conf
sudo a2ensite dc_ui.conf
sudo service apache2 restart

mkdir /datacube/{ui_results,ui_results_temp}

sudo cp config/celeryd_conf /etc/default/data_cube_ui && sudo cp config/celeryd /etc/init.d/data_cube_ui
sudo chmod 777 /etc/init.d/data_cube_ui
sudo chmod 644 /etc/default/data_cube_ui
sudo /etc/init.d/data_cube_ui start

sudo cp config/celerybeat_conf /etc/default/celerybeat && sudo cp config/celerybeat /etc/init.d/celerybeat
sudo chmod 777 /etc/init.d/celerybeat
sudo chmod 644 /etc/default/celerybeat
sudo /etc/init.d/celerybeat start

sudo cp config/.pgpass ~/.pgpass
sudo chmod 600 ~/.pgpass 
