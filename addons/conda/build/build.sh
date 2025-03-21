#!/bin/bash
set -e -x

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

mkdir -pm755 build
pushd build

export XDG_DATA_DIRS="${XDG_DATA_DIRS}:${PREFIX}/share:${BUILD_PREFIX}/share"
export PKG_CONFIG_PATH="${PKG_CONFIG_PATH}:${PREFIX}/lib/pkgconfig:${BUILD_PREFIX}/lib/pkgconfig"
export PKG_CONFIG="$(which pkg-config)"

# Build and install GStreamer
export EXTRA_FLAGS="${EXTRA_FLAGS}"

meson setup ${MESON_ARGS} -Dauto_features=disabled -Ddoc=disabled -Ddevtools=disabled -Dexamples=disabled -Dgst-examples=disabled -Dnls=disabled -Dtests=disabled -Dqt5=disabled -Dqt6=disabled -Dpython=enabled -Dgst-python:plugin=enabled -Dgst-python:libpython-dir="lib" -Dgstreamer:coretracers=enabled -Dgstreamer:ptp-helper-permissions=none -Dintrospection=enabled -Dorc=enabled -Dwebrtc=enabled -Dgst-plugins-bad:webrtcdsp=enabled -Dtls=enabled -Dgst-plugins-bad:dtls=enabled -Dgst-plugins-good:rtp=enabled -Dgst-plugins-bad:rtp=enabled -Dgst-plugins-good:rtpmanager=enabled -Dgst-plugins-bad:srtp=enabled -Dgst-plugins-bad:sctp=enabled -Dgst-plugins-bad:sdp=enabled -Dlibnice=enabled -Dtools=enabled -Dgpl=enabled -Dbase=enabled -Dgood=enabled -Dbad=enabled -Dugly=enabled -Drs=enabled -Dlibav=disabled -Dgst-plugins-base:gl=enabled -Dgst-plugins-base:gl-graphene=enabled -Dgst-plugins-bad:gl=enabled -Dgst-plugins-base:app=enabled -Dgst-plugins-base:audioconvert=enabled -Dgst-plugins-base:audiotestsrc=enabled -Dgst-plugins-base:compositor=enabled -Dgst-plugins-base:drm=enabled -Dgst-plugins-base:encoding=enabled -Dgst-plugins-base:gio=enabled -Dgst-plugins-base:gio-typefinder=enabled -Dgst-plugins-base:overlaycomposition=enabled -Dgst-plugins-base:playback=enabled -Dgst-plugins-base:rawparse=enabled -Dgst-plugins-base:subparse=enabled -Dgst-plugins-base:tcp=enabled -Dgst-plugins-good:udp=enabled -Dgst-plugins-good:soup=enabled -Dgst-plugins-good:asm=enabled -Dgst-plugins-base:typefind=enabled -Dgst-plugins-base:videoconvertscale=enabled -Dgst-plugins-base:videorate=enabled -Dgst-plugins-base:videotestsrc=enabled -Dgst-plugins-base:volume=enabled -Dgst-plugins-base:opus=enabled -Dgst-plugins-bad:opus=enabled -Dgst-plugins-good:pulse=enabled -Dgst-plugins-base:alsa=enabled -Dgst-plugins-good:jack=enabled -Dgst-plugins-base:x11=enabled -Dgst-plugins-bad:x11=enabled -Dgst-plugins-base:xi=enabled -Dgst-plugins-base:xshm=enabled -Dgst-plugins-good:ximagesrc=enabled -Dgst-plugins-good:ximagesrc-xshm=enabled -Dgst-plugins-good:ximagesrc-xfixes=enabled -Dgst-plugins-good:ximagesrc-xdamage=enabled -Dgst-plugins-good:ximagesrc-navigation=enabled -Dgst-plugins-bad:qsv=enabled -Dgst-plugins-bad:va=enabled -Dgst-plugins-bad:drm=enabled -Dgst-plugins-bad:udev=enabled -Dgst-plugins-bad:wayland=enabled -Dgst-plugins-bad:nvcodec=enabled -Dgst-plugins-good:v4l2=enabled -Dgst-plugins-good:v4l2-gudev=enabled -Dgst-plugins-bad:v4l2codecs=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-good:vpx=enabled -Dgst-plugins-ugly:x264=enabled -Dgst-plugins-bad:x265=enabled -Dgst-plugins-bad:aom=enabled -Dgst-plugins-bad:svtav1=enabled -Dgst-plugins-rs:webrtc=enabled -Dgst-plugins-rs:webrtchttp=enabled -Dgst-plugins-rs:rtp=enabled -Dgst-plugins-rs:rav1e=enabled ${EXTRA_FLAGS} .. || { cat ./meson-logs/meson-log.txt; exit 1; }

ninja
ninja install

rm -rf "${PREFIX}/share/gdb"
rm -rf "${PREFIX}/share/gstreamer-1.0/gdb"

popd

rm -rf build

# Install Selkies Python components with dependencies because of python-xlib patch
export PIP_NO_DEPENDENCIES="False"
export PIP_NO_BUILD_ISOLATION="True"
export PIP_NO_INDEX="False"
# C_INCLUDE_PATH is for building evdev
C_INCLUDE_PATH="${CONDA_BUILD_SYSROOT}/usr/include" ${PYTHON} -m pip install -v "${SELKIES_SOURCE}/${PYPI_PACKAGE}-${PACKAGE_VERSION}-py3-none-any.whl"
# Install web interface components
cp -rf "${SELKIES_SOURCE}/gst-web" "${PREFIX}/share/selkies-web"
# Install startup scripts
cp -rf "${SELKIES_BUILD}/selkies-gstreamer-run" "${PREFIX}/bin/selkies-gstreamer-run"
chmod -f +x "${PREFIX}/bin/selkies-gstreamer-run"
ln -snf "${PREFIX}/bin/selkies-gstreamer-run" "${PREFIX}"
cp -rf "${SELKIES_BUILD}/selkies-gstreamer-resize-run" "${PREFIX}/bin/selkies-gstreamer-resize-run"
chmod -f +x "${PREFIX}/bin/selkies-gstreamer-resize-run"
ln -snf "${PREFIX}/bin/selkies-gstreamer-resize-run" "${PREFIX}"
