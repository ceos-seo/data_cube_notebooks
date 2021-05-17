#!/bin/sh
mkdir -p config && echo "\
[datacube] \n\
db_hostname: ${ODC_DB_HOSTNAME} \n\
db_database: ${ODC_DB_DATABASE} \n\
db_username: ${ODC_DB_USER} \n\
db_password: ${ODC_DB_PASSWORD} \n" > config/datacube.conf
cp config/datacube.conf /etc/datacube.conf
export DATACUBE_CONFIG_PATH=${BUILD_DIR}/config/datacube.conf