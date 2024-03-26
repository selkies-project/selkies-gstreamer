# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

ARG DISTRIB_RELEASE=22.04
FROM ubuntu:${DISTRIB_RELEASE}

ARG DEBIAN_FRONTEND=noninteractive

# Install essential dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        ca-certificates \
        curl \
        git \
        pkg-config \
        tar \
        vim \
        xz-utils && \
    rm -rf /var/lib/apt/lists/*

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
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
        libvdpau-dev && \
    rm -rf /var/lib/apt/lists/*

# Install GST-Python dependencies, Meson, and Ninja
RUN apt-get update && apt-get install --no-install-recommends -y \
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
ARG GSTREAMER_VERSION=1.24.1
RUN curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    cargo install cargo-c && \
    git clone -b "${GSTREAMER_VERSION}" --single-branch --depth 1 "https://gitlab.freedesktop.org/gstreamer/gstreamer.git" && cd gstreamer && \
    mkdir -p /opt/gstreamer && \
    meson setup --prefix /opt/gstreamer -Dbuildtype=release -Dpython=enabled -Drs=enabled -Dgpl=enabled -Dbad=enabled -Dugly=enabled -Dlibav=enabled -Dgst-plugins-good:vpx=enabled -Dgst-plugins-bad:qsv=enabled -Dgst-plugins-bad:va=enabled -Dgst-plugins-bad:nvcodec=enabled -Dgst-plugins-good:v4l2=enabled -Dgst-plugins-bad:v4l2codecs=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-ugly:x264=enabled -Ddoc=disabled -Dexamples=disabled -Dtests=disabled builddir && \
    ninja -C builddir -j "$(nproc)" && \
    meson install -C builddir && \
    rm -rf builddir && rustup self uninstall

# Extract NVRTC dependency, https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/LICENSE.txt
RUN NVRTC_VERSION="11.4.152" && \
    NVRTC_ARCH="$(dpkg --print-architecture | sed -e 's/arm64/sbsa/' -e 's/ppc64el/ppc64le/' -e 's/i.*86/x86/' -e 's/amd64/x86_64/' -e 's/unknown/x86_64/')" && \
    cd /tmp && curl -fsSL "https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/linux-${NVRTC_ARCH}/cuda_nvrtc-linux-${NVRTC_ARCH}-${NVRTC_VERSION}-archive.tar.xz" | tar -xJf - -C /tmp && mv -f cuda_nvrtc* cuda_nvrtc && cd cuda_nvrtc/lib && chmod 755 libnvrtc* && mv -f libnvrtc* /opt/gstreamer/lib/$(dpkg --print-architecture | sed -e 's/arm64/aarch64-linux-gnu/' -e 's/armhf/arm-linux-gnueabihf/' -e 's/riscv64/riscv64-linux-gnu/' -e 's/ppc64el/powerpc64le-linux-gnu/' -e 's/s390x/s390x-linux-gnu/' -e 's/i.*86/i386-linux-gnu/' -e 's/amd64/x86_64-linux-gnu/' -e 's/unknown/x86_64-linux-gnu/')/ && cd /tmp && rm -rf /tmp/*

# Generate environment file
RUN MULTI_ARCH="$(gcc -print-multiarch | sed -e 's/i.*86/i386/')" && \
    echo "export GSTREAMER_PATH=\${GSTREAMER_PATH:-/opt/gstreamer}\n\
export PATH=\${GSTREAMER_PATH}/bin:\${PATH}\n\
export LD_LIBRARY_PATH=\${GSTREAMER_PATH}/lib/${MULTI_ARCH}:\${LD_LIBRARY_PATH}\n\
export GI_TYPELIB_PATH=\${GSTREAMER_PATH}/lib/${MULTI_ARCH}/girepository-1.0:/usr/lib/${MULTI_ARCH}/girepository-1.0:\${GI_TYPELIB_PATH}\n\
GST_PY_PATH=\$(find \${GSTREAMER_PATH}/lib -type d -name \"python3.*\")\n\
export PYTHONPATH=\${GST_PY_PATH}/site-packages:\${GSTREAMER_PATH}/lib/python3/dist-packages:\${PYTHONPATH}\n\
" > /opt/gstreamer/gst-env

# Bundle build result to tarball
RUN cd /opt && tar -cJvf selkies-gstreamer-latest.tar.xz gstreamer
