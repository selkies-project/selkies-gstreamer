#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname $0))

# Change this to set the Linux distribution and version
DISTRIB_IMAGE=ubuntu
DISTRIB_RELEASE=22.04

(
    cd ${SCRIPT_DIR?}/.. && \
    GSTREAMER_BASE_IMAGE=gstreamer TEST_IMAGE=selkies-gstreamer-example:latest-${DISTRIB_IMAGE}${DISTRIB_RELEASE} DISTRIB_IMAGE=${DISTRIB_IMAGE} DISTRIB_RELEASE=${DISTRIB_RELEASE} docker-compose run --service-ports test
)