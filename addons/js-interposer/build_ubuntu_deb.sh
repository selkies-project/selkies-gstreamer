#!/bin/bash

set -ex

PKG_DIR="/opt/${PKG_NAME?missing env}_${PKG_VERSION?missing env}"
mkdir -p "${PKG_DIR}/DEBIAN"

DEST_DIR="${PKG_DIR}/usr/lib/$(gcc -print-multiarch | sed -e 's/i.*86/i386/')/${PKG_NAME?missing env}"
mkdir -p "${DEST_DIR}"
gcc -shared -fPIC -o joystick_interposer.so joystick_interposer.c -ldl
mv -f joystick_interposer.so "${DEST_DIR}/joystick_interposer.so"

if [ "$(dpkg --print-architecture)" = "amd64" ]; then
  DEST_DIR="${PKG_DIR}/usr/lib/$(gcc -m32 -print-multiarch | sed -e 's/i.*86/i386/')/${PKG_NAME?missing env}"
  mkdir -p "${DEST_DIR}"
  gcc -m32 -shared -fPIC -o joystick_interposer_x86.so joystick_interposer.c -ldl
  mv -f joystick_interposer_x86.so "${DEST_DIR}/joystick_interposer.so"
fi

PKG_SIZE="$(du -s "${PKG_DIR}/usr" | awk '{print $1}' | xargs)"

cat - > ${PKG_DIR}/DEBIAN/control <<EOF
Package: ${PKG_NAME?missing env}
Version: ${PKG_VERSION}
Section: custom
Priority: optional
Architecture: $(dpkg --print-architecture)
Essential: no
Installed-Size: ${PKG_SIZE?missing env}
Maintainer: ${DEBFULLNAME?missing env} <${DEBEMAIL?missing env}>
Description: Joystick device interposer for Selkies GStreamer project
EOF

dpkg-deb --build ${PKG_DIR}
