#!/bin/bash

# Run startup initialization.
CONTAINER_STARTED="/etc/container_started"
if [ ! -e $CONTAINER_STARTED ]; then
    cd $BUILD_DIR
    bash native/odc_conf.sh
    touch $CONTAINER_STARTED
    cd $NOTEBOOK_ROOT
    nohup /bin/tini -s -- jupyter lab --allow-root --ip='0.0.0.0' \
      --NotebookApp.token=$NBK_SERVER_PASSWORD &> notebook_server_logs.txt &
fi

exec "$@"
