#!/bin/bash
set -e

echo "Activating feature 'Selkies GStreamer'"
echo "The provided release version is: ${RELEASE:-missing env}"
echo "The provided web port is: ${WEB_PORT:-missing env}"
echo "The provided xserver is: ${XSERVER:-missing env}"

# Install base dependencies
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-setuptools \
    python3-wheel \
    udev \
    wmctrl \
    libaa1 \
    bzip2 \
    libgcrypt20 \
    libegl1 \
    libgl1 \
    libgles1 \
    libglvnd0 \
    libglx0 \
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
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxkbcommon0 \
    libxdamage1 \
    libxfixes3 \
    libxtst6 \
    libxext6 \
    xclip \
    x11-utils \
    xdotool \
    x11-xserver-utils \
    xserver-xorg-core \
    wayland-protocols \
    libwayland-dev \
    libwayland-egl1 \
    libdrm2 \
    alsa-utils \
    libasound2 \
    jackd2 \
    libjack-jackd2-0 \
    libjpeg-turbo8 \
    libnice10 \
    libogg0 \
    libopenjp2-7 \
    libopus0 \
    pulseaudio \
    libpulse0 \
    libsrtp2-1 \
    libvorbis-dev \
    libvpx-dev \
    libwebp-dev \
    libwebrtc-audio-processing1 \
    x264 \
    x265 && \
rm -rf /var/lib/apt/lists/*

# Install system dependencies
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    xvfb \
    coturn && \
rm -rf /var/lib/apt/lists/*

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
