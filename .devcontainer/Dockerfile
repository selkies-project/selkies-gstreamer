ARG IMAGE_TAG=jammy
FROM mcr.microsoft.com/devcontainers/base:${IMAGE_TAG}

# Install base dependencies
RUN sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
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

RUN . /etc/lsb-release; if [ "${DISTRIB_RELEASE}" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt; fi

# Download and extract latest gstreamer component
RUN cd /opt && . /etc/lsb-release && SELKIES_VERSION=$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g') && \
    curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-v${SELKIES_VERSION}-ubuntu${DISTRIB_RELEASE}.tgz" | tar -zxf -

# Install dev dependencies
RUN sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
        nginx \
        imagemagick \
        python3-venv && \
    sudo python3 -m pip install --upgrade build

# Install desktop environment
ARG DESKTOP=xfce
COPY ./features/desktop-selkies/src/install-desktop-environment.sh /tmp/
RUN /tmp/install-desktop-environment.sh ${DESKTOP}

# Install browser
RUN cd /tmp && sudo apt-get update && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xdg-utils ./google-chrome-stable_current_amd64.deb && \
    sudo rm -f google-chrome-stable_current_amd64.deb && \
    xdg-settings set default-web-browser google-chrome.desktop
