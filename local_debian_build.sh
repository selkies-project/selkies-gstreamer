#!/bin/bash

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
    ARCH=amd64
fi

# py3-none-any
NAME=selkies-gstreamer
GIT_TAG=$(git describe --tag)
echo "selkies_gstreamer-${GIT_TAG#v}-py3-none-any.whl"

docker build --build-arg PACKAGE_VERSION=${GIT_TAG#v} . -t $NAME
DOCKER_TAG=latest
I=$(set -x; docker images $NAME:$DOCKER_TAG --format "{{.ID}}")
if [ ! -d dist ]; then
    mkdir dist
fi
(set -x; docker run -v $PWD/dist:/dist $I bash -c "cp /opt/pypi/dist/* /dist/")

# selkies-js-interposer
echo "selkies-js-interposer_${GIT_TAG}_debian12_$ARCH.deb"
cd addons/js-interposer/
./build_debian.sh
ls -1 addons/js-interposer/

cd -

# web
echo "selkies-gstreamer-web_${GIT_TAG}.tar.gz"
# gpl
echo "gstreamer-selkies_gpl_${GIT_TAG}_debian12_$ARCH.tar.gz"
cd dev
./build-gstreamer-debian12.sh

cd ..
[ "$(ls -A ./addons/gstreamer/dist)" ] && mv addons/gstreamer/dist/* dist/
[ "$(ls -A ./addons/js-interposer/dist)" ] && mv addons/js-interposer/dist/* dist/
ls -1 dist/
