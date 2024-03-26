#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname $0))

# Change this to set the ubuntu version
UBUNTU_VERSION=20.04

(
    cd ${SCRIPT_DIR?}/.. && \
    GSTREAMER_BASE_IMAGE=gstreamer TEST_IMAGE=selkies-gstreamer-example:latest-ubuntu${UBUNTU_VERSION} DISTRIB_RELEASE=${UBUNTU_VERSION} docker-compose run --service-ports test
)