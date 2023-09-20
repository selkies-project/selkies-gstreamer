#!/bin/bash

set -ex

PKG_DIR=/opt/${PKG_NAME?missing env}_${PKG_VERSION?missing env}
mkdir -p ${PKG_DIR}/DEBIAN

DEST_DIR=${PKG_DIR}/usr/local/lib/${PKG_NAME?missing env}
mkdir -p ${DEST_DIR}

make -e PREFIX=${PKG_DIR}/usr/local install

PKG_SIZE=$(du -s ${DEST_DIR} | awk '{print $1}' | xargs)

cat - > ${PKG_DIR}/DEBIAN/control <<EOF
Package: ${PKG_NAME?missing env}
Version: ${PKG_VERSION}
Section: custom
Priority: optional
Architecture: amd64
Essential: no
Installed-Size: ${PKG_SIZE?missing env}
Maintainer: ${DEBFULLNAME?missing env} <${DEBEMAIL?missing env}>
Description: Joystick device interposer for Selkies GStreamer project
EOF

dpkg-deb --build ${PKG_DIR}
