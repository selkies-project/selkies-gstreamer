#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname $0))
BUILD_DIR=${SCRIPT_DIR?}/../addons/gstreamer

# Change this to set the base ubuntu image
BASE_IMAGE=ubuntu:22.04

IMAGE_TAG=gstreamer:latest-ubuntu${BASE_IMAGE//*:/}

(cd ${BUILD_DIR?} && docker build --cache-from ${IMAGE_TAG?} --build-arg=BASE_IMAGE=${BASE_IMAGE?} -t ${IMAGE_TAG?} .)

(
    cd ${SCRIPT_DIR?}/..
    for image in dist web test; do
        GSTREAMER_BASE_IMAGE=gstreamer GSTREAMER_BASE_IMAGE_RELEASE=latest TEST_IMAGE=selkies-gstreamer-example:${IMAGE_TAG//*:/} DISTRIB_RELEASE=${BASE_IMAGE//*:/} docker-compose build ${image}
    done
)