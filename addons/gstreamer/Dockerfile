ARG BASE_IMAGE=ubuntu:20.04
FROM ${BASE_IMAGE} as build

# Install essentials
RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        ca-certificates \
        git \
        vim && \
    rm -rf /var/lib/apt/lists/*

# Install build deps
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
        libgirepository1.0-dev \
        libwebrtc-audio-processing-dev \
        libssl-dev \
        libsrtp2-dev \
        libx264-dev && \
    rm -rf /var/lib/apt/lists/*

# Install meson and ninja
RUN \
    apt-get update && apt install -y \
        python3-pip \
        python-gi-dev \
        ninja-build && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install meson

WORKDIR /src

###
# GStreamer monorepo build with prefix for standalone install.
###
ENV GSTREAMER_VERSION=1.20
RUN git clone https://gitlab.freedesktop.org/gstreamer/gstreamer.git && cd gstreamer && git checkout ${GSTREAMER_VERSION}
COPY config/gstwebrtcbin-rtx-time.patch /src/gstreamer/
RUN cd /src/gstreamer && patch -p1 < gstwebrtcbin-rtx-time.patch
RUN cd /src/gstreamer && \
    mkdir -p /opt/gstreamer && \
    meson --prefix /opt/gstreamer -Dgpl=enabled -Dugly=enabled -Dgst-plugins-ugly:x264=enabled builddir && \
    ninja -C builddir && \
    meson install -C builddir

# Bundle build output to tarball
COPY config/gst-env /opt/gstreamer/
RUN \
    cd /opt && tar zcvf selkies-gstreamer-latest.tgz gstreamer