# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

ARG DISTRIB_IMAGE=ubuntu
ARG DISTRIB_RELEASE=24.04
FROM ${DISTRIB_IMAGE}:${DISTRIB_RELEASE}

ARG DEBIAN_FRONTEND=noninteractive
# Install essential dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        apt-utils \
        build-essential \
        ca-certificates \
        curl \
        git \
        gzip \
        pkg-config \
        tar \
        xz-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        autopoint \
        autoconf \
        automake \
        autotools-dev \
        binutils \
        bison \
        flex \
        gettext \
        khronos-api \
        libtool-bin \
        nasm \
        valgrind \
        yasm \
        libgmp-dev \
        libgsl-dev \
        libgcrypt20-dev \
        libgirepository1.0-dev \
        glib-networking \
        libglib2.0-dev \
        libgudev-1.0-dev \
        libasound2-dev \
        libjack-jackd2-dev \
        libopus-dev \
        libpulse-dev \
        libssl-dev \
        libva-dev \
        libvpx-dev \
        libx264-dev \
        libx265-dev \
        libdrm-dev \
        libegl-dev \
        libgl-dev \
        libopengl-dev \
        libgles-dev \
        libglvnd-dev \
        libglx-dev \
        wayland-protocols \
        libwayland-dev \
        libwayland-egl-backend-dev \
        libx11-xcb-dev \
        libxcb-dri3-dev \
        libxdamage-dev \
        libxfixes-dev \
        libxv-dev \
        libxtst-dev \
        libxext-dev && \
    if { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "ubuntu" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "20.04" ]; } || { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "debian" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "11" ]; }; then apt-get update && apt-get install --no-install-recommends -y libopenh264-dev svt-av1 libsvtav1enc-dev libsvtav1dec-dev aom-tools libaom-dev; fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

# Install GST-Python dependencies, Meson, and Ninja
ARG PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && apt-get install --no-install-recommends -y \
        python3-pip \
        python3-dev \
        python-gi-dev && \
    pip3 install --no-cache-dir cmake meson ninja gitlint tomli && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

# GStreamer monorepo build with prefix for standalone install
WORKDIR /src
ARG GSTREAMER_VERSION=1.24.10
RUN if { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "ubuntu" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "20.04" ]; } || { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "debian" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "11" ]; }; then export GSTREAMER_EXTRA_ARGS="-Dgst-plugins-bad:aom=enabled ${GSTREAMER_EXTRA_ARGS}"; else export GSTREAMER_EXTRA_ARGS="${GSTREAMER_EXTRA_ARGS}"; fi && \
    if { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "ubuntu" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "22.04" ]; } || { [ "$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" = "debian" ] && [ "$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "12" ]; }; then export GSTREAMER_EXTRA_ARGS="-Dgst-plugins-bad:svtav1=enabled ${GSTREAMER_EXTRA_ARGS}"; fi && \
    curl --proto '=https' --tlsv1.2 -fsSL "https://sh.rustup.rs" | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    cargo install cargo-c && \
    git clone --single-branch --depth 1 --branch "${GSTREAMER_VERSION}" "https://gitlab.freedesktop.org/gstreamer/gstreamer.git" && cd gstreamer && \
    mkdir -p /opt/gstreamer && \
    meson setup --prefix /opt/gstreamer --buildtype=release -Dauto_features=disabled -Dpython=enabled -Dgst-python:plugin=enabled -Dgstreamer:coretracers=enabled -Dgstreamer:ptp-helper-permissions=none -Dintrospection=enabled -Dorc=enabled -Dwebrtc=enabled -Dgst-plugins-bad:webrtcdsp=enabled -Dtls=enabled -Dgst-plugins-bad:dtls=enabled -Dgst-plugins-good:rtp=enabled -Dgst-plugins-bad:rtp=enabled -Dgst-plugins-good:rtpmanager=enabled -Dgst-plugins-bad:srtp=enabled -Dgst-plugins-bad:sctp=enabled -Dgst-plugins-bad:sdp=enabled -Dlibnice=enabled -Dtools=enabled -Dgpl=enabled -Dbase=enabled -Dgood=enabled -Dbad=enabled -Dugly=enabled -Drs=enabled -Dlibav=disabled -Dgst-plugins-base:gl=enabled -Dgst-plugins-base:gl-graphene=enabled -Dgst-plugins-bad:gl=enabled -Dgst-plugins-base:app=enabled -Dgst-plugins-base:audioconvert=enabled -Dgst-plugins-base:audiotestsrc=enabled -Dgst-plugins-base:compositor=enabled -Dgst-plugins-base:drm=enabled -Dgst-plugins-base:encoding=enabled -Dgst-plugins-base:gio=enabled -Dgst-plugins-base:gio-typefinder=enabled -Dgst-plugins-base:overlaycomposition=enabled -Dgst-plugins-base:playback=enabled -Dgst-plugins-base:rawparse=enabled -Dgst-plugins-base:subparse=enabled -Dgst-plugins-base:tcp=enabled -Dgst-plugins-good:udp=enabled -Dgst-plugins-good:soup=enabled -Dgst-plugins-good:asm=enabled -Dgst-plugins-base:typefind=enabled -Dgst-plugins-base:videoconvertscale=enabled -Dgst-plugins-base:videorate=enabled -Dgst-plugins-base:videotestsrc=enabled -Dgst-plugins-base:volume=enabled -Dgst-plugins-base:opus=enabled -Dgst-plugins-bad:opus=enabled -Dgst-plugins-good:pulse=enabled -Dgst-plugins-base:alsa=enabled -Dgst-plugins-good:jack=enabled -Dgst-plugins-base:x11=enabled -Dgst-plugins-bad:x11=enabled -Dgst-plugins-base:xi=enabled -Dgst-plugins-base:xshm=enabled -Dgst-plugins-good:ximagesrc=enabled -Dgst-plugins-good:ximagesrc-xshm=enabled -Dgst-plugins-good:ximagesrc-xfixes=enabled -Dgst-plugins-good:ximagesrc-xdamage=enabled -Dgst-plugins-good:ximagesrc-navigation=enabled -Dgst-plugins-bad:qsv=enabled -Dgst-plugins-bad:va=enabled -Dgst-plugins-bad:drm=enabled -Dgst-plugins-bad:udev=enabled -Dgst-plugins-bad:nvcodec=enabled -Dgst-plugins-good:v4l2=enabled -Dgst-plugins-good:v4l2-gudev=enabled -Dgst-plugins-bad:v4l2codecs=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-good:vpx=enabled -Dgst-plugins-ugly:x264=enabled -Dgst-plugins-bad:x265=enabled -Dgst-plugins-rs:webrtc=enabled -Dgst-plugins-rs:webrtchttp=enabled -Dgst-plugins-rs:rtp=enabled -Dgst-plugins-rs:rav1e=enabled -Dqt5=disabled -Dqt6=disabled -Ddoc=disabled -Ddevtools=disabled -Dexamples=disabled -Dgst-examples=disabled -Dnls=disabled -Dtests=disabled ${GSTREAMER_EXTRA_ARGS} builddir && \
    ninja -C builddir && \
    meson install -C builddir && \
    rm -rf builddir && rustup self uninstall -y

# Extract NVRTC dependency, https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/LICENSE.txt
RUN NVRTC_VERSION="11.4.152" && \
    NVRTC_ARCH="$(dpkg --print-architecture | sed -e 's/arm64/sbsa/' -e 's/ppc64el/ppc64le/' -e 's/i.*86/x86/' -e 's/amd64/x86_64/' -e 's/unknown/x86_64/')" && \
    cd /tmp && curl -fsSL "https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/linux-${NVRTC_ARCH}/cuda_nvrtc-linux-${NVRTC_ARCH}-${NVRTC_VERSION}-archive.tar.xz" | tar -xJf - -C /tmp && mv -f cuda_nvrtc* cuda_nvrtc && cd cuda_nvrtc/lib && chmod -f 755 libnvrtc* && mv -f libnvrtc* /opt/gstreamer/lib/$(dpkg --print-architecture | sed -e 's/arm64/aarch64-linux-gnu/' -e 's/armhf/arm-linux-gnueabihf/' -e 's/riscv64/riscv64-linux-gnu/' -e 's/ppc64el/powerpc64le-linux-gnu/' -e 's/s390x/s390x-linux-gnu/' -e 's/i.*86/i386-linux-gnu/' -e 's/amd64/x86_64-linux-gnu/' -e 's/unknown/x86_64-linux-gnu/')/ && cd /tmp && rm -rf /tmp/cuda_nvrtc

# Generate environment file
RUN MULTI_ARCH="$(gcc -print-multiarch | sed -e 's/i.*86/i386/')" && \
    echo "#!/bin/bash\n\
export GSTREAMER_PATH=\"\${GSTREAMER_PATH:-\$(cd \$(dirname \${BASH_SOURCE[0]:-\${(%):-%x}}) && pwd)}\"\n\
export PATH=\"\${GSTREAMER_PATH}/bin\${PATH:+:\${PATH}}\"\n\
export LD_LIBRARY_PATH=\"\${GSTREAMER_PATH}/lib/${MULTI_ARCH}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}\"\n\
export GST_PLUGIN_PATH=\"\${GSTREAMER_PATH}/lib/${MULTI_ARCH}/gstreamer-1.0\${GST_PLUGIN_PATH:+:\${GST_PLUGIN_PATH}}\"\n\
export GST_PLUGIN_SYSTEM_PATH=\"\${XDG_DATA_HOME:-\${HOME:-~}/.local/share}/gstreamer-1.0/plugins:/usr/lib/${MULTI_ARCH}/gstreamer-1.0\${GST_PLUGIN_SYSTEM_PATH:+:\${GST_PLUGIN_SYSTEM_PATH}}\"\n\
export GI_TYPELIB_PATH=\"\${GSTREAMER_PATH}/lib/${MULTI_ARCH}/girepository-1.0:/usr/lib/${MULTI_ARCH}/girepository-1.0\${GI_TYPELIB_PATH:+:\${GI_TYPELIB_PATH}}\"\n\
export PYTHONPATH=\"\${GSTREAMER_PATH}/lib/python3/dist-packages\${PYTHONPATH:+:\${PYTHONPATH}}\"\n\
" > /opt/gstreamer/gst-env

# Bundle build result to tarball
RUN cd /opt && tar -czvf selkies-gstreamer-latest.tar.gz gstreamer
