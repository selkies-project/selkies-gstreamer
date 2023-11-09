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
    jq \
    gdebi-core \
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
    libwayland-egl1 \
    libx11-xcb1 \
    libxkbcommon0 \
    libxdamage1 \
    libsoup2.4-1 \
    libsoup-gnome2.4-1 \
    libsrtp2-1 \
    lame \
    libopus0 \
    libwebrtc-audio-processing1 \
    pulseaudio \
    libpulse0 \
    libcairo-gobject2 \
    libpangocairo-1.0-0 \
    libgirepository-1.0-1 \
    libopenjp2-7 \
    libjpeg-dev \
    libwebp-dev \
    libvpx-dev \
    zlib1g-dev \
    x264 && \
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
if [[ "${RELEASE}" == "latest" ]]; then
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
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-${SELKIES_RELEASE_TAG}-ubuntu${DISTRIB_RELEASE}.tgz" | tar -zxf -
curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && pip3 install "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-web-${SELKIES_RELEASE_TAG}.tgz" | tar -zxf -

# Extract NVRTC dependency, https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/LICENSE.txt
cd /tmp && curl -fsSL -o nvidia_cuda_nvrtc_linux_x86_64.whl "https://developer.download.nvidia.com/compute/redist/nvidia-cuda-nvrtc/nvidia_cuda_nvrtc-11.0.221-cp36-cp36m-linux_x86_64.whl" && unzip -joq -d ./nvrtc nvidia_cuda_nvrtc_linux_x86_64.whl && cd nvrtc && chmod 755 libnvrtc* && find . -maxdepth 1 -type f -name "*libnvrtc.so.*" -exec sh -c 'ln -snf $(basename {}) libnvrtc.so' \; && mv -f libnvrtc* /opt/gstreamer/lib/x86_64-linux-gnu/ && cd /tmp && rm -rf /tmp/*

# Copy turnserver script
cp start-turnserver.sh /usr/local/bin/start-turnserver.sh
chmod +x /usr/local/bin/start-turnserver.sh &

# Copy the startup script
cp start-selkies.sh /usr/local/bin/start-selkies.sh
chmod +x /usr/local/bin/start-selkies.sh
