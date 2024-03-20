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
        bison \
        cmake \
        flex \
        gettext \
        gtk-doc-tools \
        khronos-api \
        nasm \
        valgrind \
        libaa1-dev \
        libbz2-dev \
        libgcrypt20-dev \
        libgl-dev \
        libgles-dev \
        libglvnd-dev \
        libgmp-dev \
        libgudev-1.0-dev \
        libgirepository1.0-dev \
        libgtk2.0-dev \
        libgsl-dev \
        libtool-bin \
        libx11-xcb-dev \
        libxcb-dri3-dev \
        libxkbcommon-dev \
        wayland-protocols \
        libvulkan-dev \
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
        libx265-dev \
        libvpx-dev \
        libvdpau-dev \
        libva-dev \
        libmfx-dev \
        i965-va-driver-shaders \
        intel-media-va-driver-non-free \
        va-driver-all && \
    curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    cargo install cargo-c && \
    rm -rf /var/lib/apt/lists/*

# Install GST-Python dependencies, Meson, and Ninja
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        libglib2.0-dev \
        libjson-glib-dev \
        libxml2-dev \
        python3-libxml2 \
        python3-pip \
        python3-dev \
        python-gi-dev && \
    pip3 install meson ninja gitlint hotdoc tomli && \
    rm -rf /var/lib/apt/lists/*

# GStreamer monorepo build with prefix for standalone install
WORKDIR /src
ARG GSTREAMER_VERSION=1.24.0
RUN git clone -b "${GSTREAMER_VERSION}" --single-branch --depth 1 "https://gitlab.freedesktop.org/gstreamer/gstreamer.git" && cd gstreamer && \
    mkdir -p /opt/gstreamer && \
    . "$HOME/.cargo/env" && \
    meson setup --prefix /opt/gstreamer -Dbuildtype=release -Dpython=enabled -Drs=enabled -Dgpl=enabled -Dbad=enabled -Dugly=enabled -Dlibav=enabled -Dgst-plugins-bad:qsv=enabled -Dgst-plugins-bad:va=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-ugly:x264=enabled -Ddoc=disabled -Dexamples=disabled -Dtests=disabled builddir && \
    ninja -C builddir -j "$(nproc)" && \
    meson install -C builddir

# Bundle build result to tarball
COPY config/gst-env /opt/gstreamer/
RUN cd /opt && tar -zcvf selkies-gstreamer-latest.tgz gstreamer
