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
    sudo rm -rf /var/lib/apt/lists/*

RUN . /etc/lsb-release; if [ "${DISTRIB_RELEASE}" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt; fi

# Download and extract latest GStreamer component
RUN cd /opt && . /etc/lsb-release && SELKIES_VERSION=$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g') && \
    curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-v${SELKIES_VERSION}-ubuntu${DISTRIB_RELEASE}.tgz" | tar -zxf -

# Install development dependencies
RUN sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        xvfb \
        coturn \
        nginx \
        imagemagick \
        python3-venv && \
    sudo rm -rf /var/lib/apt/lists/* && \
    sudo python3 -m pip install --upgrade build

# Install desktop environment
ARG DESKTOP=xfce
COPY ./features/desktop-selkies/src/install-desktop-environment.sh /tmp/
RUN /tmp/install-desktop-environment.sh ${DESKTOP}

# Install Chrome browser
RUN cd /tmp && curl -fsSL -o ./google-chrome-stable.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y xdg-utils ./google-chrome-stable.deb && \
    sudo rm -rf /var/lib/apt/lists/* && \
    sudo rm -f google-chrome-stable.deb && \
    xdg-settings set default-web-browser google-chrome.desktop

# Install other development utilities
RUN sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        jstest-gtk \
        netcat && \
    sudo rm -rf /var/lib/apt/lists/*
