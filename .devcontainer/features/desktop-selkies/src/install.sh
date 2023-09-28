#!/bin/bash
set -e

export SCRIPT_DIR=$(dirname $(readlink -f "$0"))

# Set default input parameter values.
export RELEASE=${RELEASE:-latest}
export WEB_PORT=${WEB_PORT:-6080}
export DESKTOP=${DESKTOP:-xfce}

echo "Activating feature 'Selkies GStreamer'"
echo "The provided release version is: ${RELEASE?missing env}"
echo "The provided web port is: ${WEB_PORT?missing env}"
echo "The provided desktop environment is: ${DESKTOP?xfce}"

# Install base dependencies
apt-get update && apt-get install --no-install-recommends -y \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-setuptools \
    python3-wheel \
    udev \
    wmctrl \
    jq \
    gdebi-core \
    glib-networking \
    libopus0 \
    libgdk-pixbuf2.0-0 \
    libgtk2.0-bin \
    libgl-dev \
    libgles-dev \
    libglvnd-dev \
    libgudev-1.0-0 \
    xclip \
    x11-utils \
    xdotool \
    x11-xserver-utils \
    xserver-xorg-core \
    wayland-protocols \
    libwayland-dev \
    libwayland-egl-backend-dev \
    libx11-xcb1 \
    libxkbcommon0 \
    libxdamage1 \
    libxml2-dev \
    libwebrtc-audio-processing1 \
    libsrtp2-1 \
    libcairo-gobject2 \
    pulseaudio \
    libpulse0 \
    libpangocairo-1.0-0 \
    libgirepository1.0-dev \
    libjpeg-dev \
    libwebp-dev \
    libvpx-dev \
    zlib1g-dev \
    x264 \
    xvfb \
    coturn

sudo systemctl stop coturn || true
sudo systemctl disable coturn || true

[[ -f /etc/lsb-release ]] && . /etc/lsb-release
if [ "${DISTRIB_RELEASE:-20.04}" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt; fi

# Install desktop environment
${SCRIPT_DIR}/install-desktop-environment.sh ${DESKTOP?missing env}

SELKIES_RELEASE_TAG=${RELEASE}
if [[ "${RELEASE}" == "latest" ]]; then
    # Automatically fetch the latest selkies-gstreamer version and install the components
    SELKIES_RELEASE_TAG=$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name')
else
    # Check for tagged release
    if ! curl -fsSL -o /dev/null "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/tags/${RELEASE}"; then
        echo "ERROR: could not find selkies-gstreamer release ${RELEASE}"
        exit 1
    fi
fi
# Remove leading 'v' to get semver number.
SELKIES_VERSION=${SELKIES_RELEASE_TAG:1}

(cd /opt
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-${SELKIES_RELEASE_TAG}-ubuntu${DISTRIB_RELEASE}.tgz" | tar -zxf - && \
curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && pip3 install --force-reinstall "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && \
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-web-${SELKIES_RELEASE_TAG}.tgz" | tar -zxf - && \
curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-js-interposer-${SELKIES_RELEASE_TAG}-ubuntu${DISTRIB_RELEASE}.deb" && apt-get install -y ./selkies-js-interposer*.deb)

# Link cuda libraries if they are present.
if [[ -d /usr/local/cuda ]]; then
    (cd /usr/local/cuda/lib64 && sudo find . -maxdepth 1 -type l -name "*libnvrtc.so.*" -exec sh -c 'ln -snf $(basename {}) libnvrtc.so' \;)
fi

# Copy turnserver script
cp ${SCRIPT_DIR}/start-turnserver.sh /usr/local/bin/start-turnserver.sh
chmod +x /usr/local/bin/start-turnserver.sh &

# Copy the startup script
cp ${SCRIPT_DIR}/start-selkies.sh /usr/local/bin/start-selkies.sh
chmod +x /usr/local/bin/start-selkies.sh
