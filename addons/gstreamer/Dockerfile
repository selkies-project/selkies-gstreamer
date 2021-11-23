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
        libsrtp2-dev && \
    rm -rf /var/lib/apt/lists/*

# Install meson and ninja
RUN \
    apt-get update && apt install -y \
        python3-pip \
        python-gi-dev \
        ninja-build && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install meson

WORKDIR /opt

# Clone gst-build repo
ENV GST_BUILD_VERSION=f75713f07038762f6fd09e199886dd4b6c00284c
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-build.git && cd gst-build && git checkout ${GST_BUILD_VERSION}

# Add usrsctp patch to gst-build
COPY config/usrsctp.wrap /opt/gst-build/subprojects/
COPY config/gst-build-add-usrsctp.patch /opt/gst-build/
RUN cd /opt/gst-build && patch -p1 < gst-build-add-usrsctp.patch

ENV GST_VERSION=1.19.1

WORKDIR /opt/gst-build

# Check out the gstreamer version and build
RUN ./gst-worktree.py add gst-build-${GST_VERSION} ${GST_VERSION} && \
    mkdir -p /opt/gstreamer && \
    meson --prefix /opt/gstreamer builddir && \
    ninja -C builddir && \
    meson install -C builddir

WORKDIR /opt

# Bundle build output to tarball
COPY config/gst-env /opt/gstreamer/
RUN \
    cd /opt && tar zcvf selkies-gstreamer-latest.tgz gstreamer