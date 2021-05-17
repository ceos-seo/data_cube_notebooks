#!/bin/bash

# Run startup initialization.
CONTAINER_STARTED="/tmp/container_started"
if [ ! -e $CONTAINER_STARTED ]; then
    bash build/native/odc_conf.sh
    touch $CONTAINER_STARTED
fi

/bin/tini -- "$@"