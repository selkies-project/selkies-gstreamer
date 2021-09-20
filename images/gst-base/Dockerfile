# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:20.04

# Use GCE apt servers
ARG GCE_REGION=us-west1
RUN cp /etc/apt/sources.list /etc/apt/sources.list.orig && \
    sed -i "s/archive.ubuntu.com/${GCE_REGION}.gce.archive.ubuntu.com/g" /etc/apt/sources.list

# Install essentials
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        ca-certificates \
        git \
        python3-pip

WORKDIR /opt

# Checkout hashed commits with CUDA buffer support.
# This can be removed once MR 1633 is on a release tag:
#   https://gitlab.freedesktop.org/gstreamer/gst-plugins-bad/merge_requests/1633
ARG GSTREAMER_VERSION=b6147e6037202503c133eb1fad1d936bd9269cef
ARG GST_PLUGINS_BASE_VERSION=f6aea043f93729db41187e19574bb1d1b96587db
ARG GST_PLUGINS_GOOD_VERSION=2c69544d0c60b1aa43b43f67fa5a887698d735c4
ARG GST_PLUGINS_BAD_VERSION=4f0b619023cb58e4be7cd4d01368f780f271bcf5
ARG GST_PLUGINS_UGLY_VERSION=fbe2ea6e3868850388d06e66ef2681419e27f2fa
ARG GST_PYTHON_VERSION=f9eac69d5409982e23ac5cd401f65fc5a07e92cb

# Clone each gstreamer module
RUN git clone https://gitlab.freedesktop.org/gstreamer/gstreamer.git && cd gstreamer && git checkout ${GSTREAMER_VERSION}
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-base.git && cd gst-plugins-base && git checkout ${GST_PLUGINS_BASE_VERSION}
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-good && cd gst-plugins-good && git checkout ${GST_PLUGINS_GOOD_VERSION}
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-bad && cd gst-plugins-bad && git checkout ${GST_PLUGINS_BAD_VERSION}
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-ugly && cd gst-plugins-ugly && git checkout ${GST_PLUGINS_UGLY_VERSION}
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-python && cd gst-python && git checkout ${GST_PYTHON_VERSION}

WORKDIR /opt

# Install base build deps
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        autopoint \
        autoconf \
        automake \
        autotools-dev \
        libtool \
        gettext \
        bison \
        flex \
        gtk-doc-tools \
        libtool-bin \
        libgtk2.0-dev \
        libgl1-mesa-dev \
        libopus-dev \
        libpulse-dev \
        libgirepository1.0-dev

# Install meson build deps
RUN \
    apt-get update && apt install -y python3-pip python-gi-dev ninja-build && \
    pip3 install meson

# Install debian package deps
RUN \
    apt-get update && apt install -y \
        fakeroot \
        debhelper \
        dh-make

ARG GST_VERSION=1.19.1
ENV DEB_BUILD_OPTIONS='nocheck'

# Build libgstreamer1.0
RUN \
    cd /opt/gstreamer && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p libgstreamer1.0-0_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo libgstreamer1.0-0_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Build gstreamer1.0-plugins-base
RUN \
    cd /opt/gst-plugins-base && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p gstreamer1.0-plugins-base_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo gstreamer1.0-plugins-base_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Install deps for gst-plugins-good
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libvpx-dev \
        libvpx6

# Build gstreamer1.0-plugins-good
RUN \
    cd /opt/gst-plugins-good && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p gstreamer1.0-plugins-good_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo gstreamer1.0-plugins-good_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Install deps for gst-plugins-bad
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libwebrtc-audio-processing-dev \
        libssl-dev \
        libsrtp2-dev

# Install usrsctp from source
ARG USRSCTP_VERSION=0.9.5.0
RUN \
    git clone https://github.com/sctplab/usrsctp.git && \
    cd usrsctp && git checkout ${USRSCTP_VERSION} && \
    ./bootstrap && ./configure --prefix=/usr && \
    USER=root dh_make --createorig -p usrsctp_${USRSCTP_VERSION} --single --yes && \
    dh_auto_configure && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo usrsctp_${USRSCTP_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Install libnice from source
ARG LIBNICE_VERSION=4401e346a7517614d9ff51bdaec5adaaf55c2f5e
RUN \
    git clone https://gitlab.freedesktop.org/libnice/libnice.git && \
    cd libnice && git checkout ${LIBNICE_VERSION} && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p libnice_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo libnice_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Build gstreamer1.0-plugins-bad
RUN \
    cd /opt/gst-plugins-bad && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p gstreamer1.0-plugins-bad_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo gstreamer1.0-plugins-bad_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Install deps for gst-python
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-dev

# Build gst-python1.0
RUN \
    cd /opt/gst-python && \
    meson build --prefix=/usr \
        -Dpygi-overrides-dir=/usr/lib/python3/dist-packages/gi/overrides && \
    USER=root dh_make --createorig -p gst-python1.0_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo gst-python1.0_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Build and install gst-plugins-ugly from source
# This package includes the x264 encoder for non-nvenc accelerated pipelines.
RUN \
    apt-get update && apt install -y libx264-155 libx264-dev

# Build gstreamer1.0-plugins-ugly
RUN \
    cd /opt/gst-plugins-ugly && \
    meson build --prefix=/usr && \
    USER=root dh_make --createorig -p gstreamer1.0-plugins-ugly_${GST_VERSION} --single --yes && \
    dh_auto_configure --buildsystem=meson && \
    dpkg-buildpackage -rfakeroot -us -uc -b
RUN echo gstreamer1.0-plugins-ugly_${GST_VERSION}-1_amd64.deb | tee -a /opt/debs.txt | xargs -I{} dpkg -i /opt/{}

# Bundle all debian packages into tarball and create install script.
RUN \
    DEB_FILES=$(cat debs.txt | tr "\n" " " | xargs) && \
    echo '#!/bin/bash' > /opt/selkies-gstreamer-install.sh && \
    echo 'for f in '${DEB_FILES}'; do echo "Installing: $f"; gdebi -n $f; done' >> /opt/selkies-gstreamer-install.sh && \
    chmod +x /opt/selkies-gstreamer-install.sh
RUN \
    cd /opt && tar zcvf gstreamer-debs.tgz *.deb selkies-gstreamer-install.sh

# Build a python package for the webrtc app.
WORKDIR /opt/pypi
COPY . .
RUN apt-get update && apt-get install -y python3-venv && \
    python3 -m pip install --upgrade build
RUN python3 -m build

WORKDIR /opt