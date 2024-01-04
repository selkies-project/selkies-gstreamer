# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

ARG UBUNTU_RELEASE=22.04
FROM ubuntu:${UBUNTU_RELEASE}

# Install essential dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        build-essential \
        ca-certificates \
        curl \
        git \
        vim && \
    rm -rf /var/lib/apt/lists/*

# Install build dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        autopoint \
        autoconf \
        automake \
        autotools-dev \
        gettext \
        bison \
        flex \
        nasm \
        gtk-doc-tools \
        libgl-dev \
        libgles-dev \
        libglvnd-dev \
        libgudev-1.0-dev \
        libgirepository1.0-dev \
        libgtk2.0-dev \
        libtool-bin \
        libx11-xcb-dev \
        libxkbcommon-dev \
        wayland-protocols \
        libwayland-dev \
        libwayland-egl-backend-dev \
        libdrm-dev \
        libmp3lame-dev \
        libopus-dev \
        libpulse-dev \
        libwebrtc-audio-processing-dev \
        libsoup2.4-dev \
        libsoup-gnome2.4-dev \
        libsrtp2-dev \
        libssl-dev \
        libjpeg-dev \
        libopenjp2-7-dev \
        libwebp-dev \
        libx264-dev \
        libvpx-dev \
        libva-dev && \
    rm -rf /var/lib/apt/lists/*

# Install GST-Python dependencies, Meson, and Ninja
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        python3-pip \
        python3-dev \
        python-gi-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install meson ninja

# GStreamer monorepo build with prefix for standalone install
WORKDIR /src
ARG GSTREAMER_VERSION=1.22.8
RUN git clone "https://gitlab.freedesktop.org/gstreamer/gstreamer.git" && cd gstreamer && git checkout "${GSTREAMER_VERSION}" && \
    mkdir -p /opt/gstreamer && \
    meson setup --prefix /opt/gstreamer -Dbuildtype=release -Db_lto=true -Dpython=enabled -Dgpl=enabled -Dbad=enabled -Dugly=enabled -Dgst-plugins-bad:qsv=enabled -Dgst-plugins-bad:va=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-ugly:x264=enabled builddir && \
    ninja -C builddir -j "$(nproc)" && \
    meson install -C builddir

# Bundle build result to tarball
COPY config/gst-env /opt/gstreamer/
RUN cd /opt && tar -zcvf selkies-gstreamer-latest.tgz gstreamer
