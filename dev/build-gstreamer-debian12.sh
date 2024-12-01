#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname $0))
BUILD_DIR=${SCRIPT_DIR?}/../addons/gstreamer

# Change this to set the base debian image
BASE_IMAGE=debian:12

IMAGE_TAG=gstreamer:latest-debian${BASE_IMAGE//*:/}

(cd ${BUILD_DIR?} && docker build --cache-from ${IMAGE_TAG?} --build-arg=BASE_IMAGE=${BASE_IMAGE?} -t ${IMAGE_TAG?} -f Dockerfile.debian .)

(
    cd ${SCRIPT_DIR?}/..
    # for image in dist web test; do
    for image in dist web; do
        echo "image = $image"
        echo $PWD
        GSTREAMER_BASE_IMAGE=gstreamer GSTREAMER_BASE_IMAGE_RELEASE=latest TEST_IMAGE=selkies-gstreamer-example:${IMAGE_TAG//*:/} DISTRIB_RELEASE=${BASE_IMAGE//*:/} docker-compose build ${image}
    done
)

#if [ ! -d dist ]; then
#    mkdir dist
#fi

cd $BUILD_DIR
if [ "$1" = "-c" ]; then
    sudo rm -f ./dist/*
fi


NAME=gst-web
GIT_TAG=$(git describe --tag)
DOCKER_TAG=latest
I=$(set -x; docker images $NAME:$DOCKER_TAG --format "{{.ID}}")
(set -x; docker run -it -v ./dist:/dist $I sh -c "cp /opt/gst-web.tar.gz /dist/selkies-gstreamer-web_${GIT_TAG}.tar.gz")

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
    ARCH=amd64
fi
NAME=gstreamer
GIT_TAG=$(git describe --tag)
DOCKER_TAG=latest-debian${BASE_IMAGE//*:/}
I=$(set -x; docker images $NAME:$DOCKER_TAG --format "{{.ID}}")
(set -x; docker run -it -v ./dist:/dist $I sh -c "cp /opt/selkies-gstreamer-latest.tar.gz /dist/gstreamer-selkies_gpl_${GIT_TAG}_debian${BASE_IMAGE//*:/}_$ARCH.tar.gz")
sudo chown $USER:$USER -R $BUILD_DIR/dist/
ls -la $BUILD_DIR/dist/
