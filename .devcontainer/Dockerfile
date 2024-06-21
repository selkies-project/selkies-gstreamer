ARG IMAGE_TAG=jammy
FROM mcr.microsoft.com/devcontainers/base:${IMAGE_TAG}

ARG DEBIAN_FRONTEND=noninteractive

# Install base dependencies
RUN sudo apt-get update && sudo apt-get install --no-install-recommends -y \
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
    sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

RUN . /etc/lsb-release; if [ "${DISTRIB_RELEASE}" \> "20.04" ]; then \
        sudo apt-get update && \
        sudo apt-get install --no-install-recommends -y xcvt && \
        sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*; \
    fi

# Download and extract latest GStreamer component
RUN cd /opt && . /etc/lsb-release && SELKIES_VERSION=$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g') && \
    curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-v${SELKIES_VERSION}-ubuntu${DISTRIB_RELEASE}.tar.gz" | sudo tar -xzf -

# Install development dependencies
ARG PIP_BREAK_SYSTEM_PACKAGES=1
RUN sudo apt-get update && sudo apt-get install --no-install-recommends -y \
        xvfb \
        coturn \
        nginx \
        imagemagick \
        python3-venv && \
    sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/* && \
    sudo python3 -m pip install --no-cache-dir --upgrade build

# Install desktop environment
ARG DESKTOP=xfce
COPY ./features/desktop-selkies/src/install-desktop-environment.sh /tmp/
RUN /tmp/install-desktop-environment.sh ${DESKTOP}

# Install Chrome browser
RUN cd /tmp && curl -fsSL -o ./google-chrome-stable.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    sudo apt-get update && sudo apt-get install --no-install-recommends -y xdg-utils ./google-chrome-stable.deb && \
    sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/* && \
    sudo rm -f google-chrome-stable.deb && \
    xdg-settings set default-web-browser google-chrome.desktop

# Install other development utilities
RUN sudo apt-get update && sudo apt-get install --no-install-recommends -y \
        jstest-gtk \
        netcat && \
    sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*
