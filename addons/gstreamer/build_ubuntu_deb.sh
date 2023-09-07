#!/bin/bash

set -ex

PKG_DIR=/opt/selkies-gst-gstreamer-${GSTREAMER_VERSION?missing env}_${SELKIES_VERSION?missing env}
mkdir -p ${PKG_DIR}/DEBIAN

# Copy gstreamer to package dir
DEST_DIR=${PKG_DIR}/usr/local/share/selkies-gst-gstreamer-${GSTREAMER_VERSION}
mkdir -p ${DEST_DIR}
cp -R /opt/gstreamer/* ${DEST_DIR}/

PKG_SIZE=$(du -s /opt/gstreamer | awk '{print $1}' | xargs)

cat - > ${PKG_DIR}/DEBIAN/control <<EOF
Package: selkies-gst-gstreamer-${GSTREAMER_VERSION}
Version: ${SELKIES_VERSION}
Section: custom
Priority: optional
Architecture: amd64
Essential: no
Installed-Size: ${PKG_SIZE?missing env}
Maintainer: ${DEBFULLNAME?missing env} <${DEBEMAIL?missing env}>
Description: Custom gstreamer build for selkies-gstreamer
Depends: libopus0, libpulse0, libglib2.0-0, libwebrtc-audio-processing1, libgudev-1.0-0, libsrtp2-1, libegl1, libgudev-1.0-0, libxdamage1, x264
EOF

dpkg-deb --build $(basename ${PKG_DIR})
