#!/usr/bin/bash

bash scripts/initial_migrations.sh
cp config/.datacube.conf ~/.datacube.conf
sudo cp config/dc_ui.conf /etc/apache2/sites-available/dc_ui.conf
sudo a2dissite 000-default.conf
sudo a2ensite dc_ui.conf
sudo service apache2 restart

mkdir /datacube/{ui_results,ui_results_temp}
