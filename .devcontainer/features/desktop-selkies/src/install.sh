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
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-${SELKIES_RELEASE_TAG}-ubuntu${DISTRIB_RELEASE}.tar.xz" | tar -xJf -
curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && pip3 install "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/${SELKIES_RELEASE_TAG}/selkies-gstreamer-web-${SELKIES_RELEASE_TAG}.tar.xz" | tar -xJf -

# Extract NVRTC dependency, https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/LICENSE.txt
NVRTC_VERSION="11.4.152"
NVRTC_ARCH="$(dpkg --print-architecture | sed -e 's/arm64/sbsa/' -e 's/ppc64el/ppc64le/' -e 's/i.*86/x86/' -e 's/amd64/x86_64/' -e 's/unknown/x86_64/')"
cd /tmp && curl -fsSL "https://developer.download.nvidia.com/compute/cuda/redist/cuda_nvrtc/linux-${NVRTC_ARCH}/cuda_nvrtc-linux-${NVRTC_ARCH}-${NVRTC_VERSION}-archive.tar.xz" | tar -xJf - -C /tmp && mv -f cuda_nvrtc* cuda_nvrtc && cd cuda_nvrtc/lib && chmod 755 libnvrtc* && mv -f libnvrtc* /opt/gstreamer/lib/$(dpkg --print-architecture | sed -e 's/arm64/aarch64-linux-gnu/' -e 's/armhf/arm-linux-gnueabihf/' -e 's/riscv64/riscv64-linux-gnu/' -e 's/ppc64el/powerpc64le-linux-gnu/' -e 's/s390x/s390x-linux-gnu/' -e 's/i.*86/i386-linux-gnu/' -e 's/amd64/x86_64-linux-gnu/' -e 's/unknown/x86_64-linux-gnu/')/ && cd /tmp && rm -rf /tmp/cuda_nvrtc
mkdir -pm755 /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# Copy turnserver script
cp start-turnserver.sh /usr/local/bin/start-turnserver.sh
chmod +x /usr/local/bin/start-turnserver.sh &

# Copy the startup script
cp start-selkies.sh /usr/local/bin/start-selkies.sh
chmod +x /usr/local/bin/start-selkies.sh
