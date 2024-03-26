#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname $0))

# Change this to set the ubuntu version
UBUNTU_VERSION=22.04

(
    cd ${SCRIPT_DIR?}/.. && \
    PYTHON_BASE=/usr/local/lib/python3.10 GSTREAMER_BASE_IMAGE=gstreamer TEST_IMAGE=selkies-gstreamer-example:latest-ubuntu${UBUNTU_VERSION} DISTRIB_RELEASE=${UBUNTU_VERSION} docker-compose run --service-ports test
)