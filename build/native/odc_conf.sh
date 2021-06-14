#!/bin/sh
mkdir -p config && echo """\
[datacube]
db_hostname: ${ODC_DB_HOSTNAME}
db_database: ${ODC_DB_DATABASE}
db_username: ${ODC_DB_USER}
db_password: ${ODC_DB_PASSWORD}""" > config/datacube.conf
cp config/datacube.conf /etc/datacube.conf
export DATACUBE_CONFIG_PATH=/etc/datacube.conf
