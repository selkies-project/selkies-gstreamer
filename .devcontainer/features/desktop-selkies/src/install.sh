#!/bin/bash
set -e

echo "Activating feature 'Selkies GStreamer'"
echo "The provided release version is: ${RELEASE:-missing env}"
echo "The provided web port is: ${WEB_PORT:-missing env}"
echo "The provided xserver is: ${XSERVER:-missing env}"

export DEBIAN_FRONTEND=noninteractive

# Install base dependencies
apt-get update && apt-get install --no-install-recommends -y \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-setuptools \
    python3-wheel \
    libaa1 \
    bzip2 \
    libgcrypt20 \
    libcairo-gobject2 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libsoup2.4-1 \
    libsoup-gnome2.4-1 \
    libgirepository-1.0-1 \
    glib-networking \
    libglib2.0-0 \
    libjson-glib-1.0-0 \
    libgudev-1.0-0 \
    alsa-utils \
    jackd2 \
    libjack-jackd2-0 \
    libpulse0 \
    libogg0 \
    libopus0 \
    libvorbis-dev \
    libjpeg-turbo8 \
    libopenjp2-7 \
    libvpx-dev \
    libwebp-dev \
    x264 \
    x265 \
    libdrm2 \
    libegl1 \
    libgl1 \
    libopengl0 \
    libgles1 \
    libgles2 \
    libglvnd0 \
    libglx0 \
    wayland-protocols \
    libwayland-dev \
    libwayland-egl1 \
    wmctrl \
    xsel \
    xdotool \
    x11-utils \
    x11-xkb-utils \
    x11-xserver-utils \
    xserver-xorg-core \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxkbcommon0 \
    libxdamage1 \
    libxfixes3 \
    libxv1 \
    libxtst6 \
    libxext6 && \
if [ "$(grep VERSION_ID= /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools; else apt-get install --no-install-recommends -y mesa-utils-extra; fi && \
apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

# Install system dependencies
apt-get update && apt-get install --no-install-recommends -y \
    xvfb \
    coturn && \
apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

. /etc/lsb-release
if [ "${DISTRIB_RELEASE}" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt; fi

# Install desktop environment
./install-desktop-environment.sh ${DESKTOP}

SELKIES_RELEASE_TAG=${RELEASE}
if [ "${RELEASE}" = "latest" ]; then
    # Automatically fetch the latest selkies-gstreamer version and install the components
    SELKIES_RELEASE_TAG=$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g')
else
    # Check for tagged release
    if ! curl -fsSL -o /dev/null "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/tags/${RELEASE}"; then
        echo "ERROR: could not find selkies-gstreamer release ${RELEASE}"
        exit 1
    fi
fi
# Remove leading 'v' to get semver number.
SELKIES_VERSION=${SELKIES_RELEASE_TAG:1}

cd /opt
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-${SELKIES_RELEASE_TAG}-ubuntu${DISTRIB_RELEASE}.tar.gz" | tar -xzf -
curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-web-${SELKIES_RELEASE_TAG}.tar.gz" | tar -xzf -

mkdir -pm755 /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# Copy turnserver script
cp start-turnserver.sh /usr/local/bin/start-turnserver.sh
chmod +x /usr/local/bin/start-turnserver.sh &

# Copy the startup script
cp start-selkies.sh /usr/local/bin/start-selkies.sh
chmod +x /usr/local/bin/start-selkies.sh
