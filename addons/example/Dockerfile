# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Supported base images: Ubuntu 24.04, 22.04, 20.04
ARG DISTRIB_RELEASE=24.04
ARG GSTREAMER_BASE_IMAGE=ghcr.io/selkies-project/selkies-gstreamer/gstreamer
ARG GSTREAMER_BASE_IMAGE_RELEASE=main
ARG PY_BUILD_IMAGE=ghcr.io/selkies-project/selkies-gstreamer/py-build:main
ARG WEB_IMAGE=ghcr.io/selkies-project/selkies-gstreamer/gst-web:main
ARG JS_BASE_IMAGE=ghcr.io/selkies-project/selkies-gstreamer/js-interposer
ARG JS_BASE_IMAGE_RELEASE=main
FROM ${GSTREAMER_BASE_IMAGE}:${GSTREAMER_BASE_IMAGE_RELEASE}-ubuntu${DISTRIB_RELEASE} AS selkies-gstreamer
FROM ${PY_BUILD_IMAGE} AS selkies-build
FROM ${WEB_IMAGE} AS selkies-web
FROM ${JS_BASE_IMAGE}:${JS_BASE_IMAGE_RELEASE}-ubuntu${DISTRIB_RELEASE} AS selkies-js-interposer
FROM ubuntu:${DISTRIB_RELEASE}
ARG DISTRIB_RELEASE

LABEL maintainer="https://github.com/danisla,https://github.com/ehfd"

ARG DEBIAN_FRONTEND=noninteractive
# Configure rootless user environment for constrained conditions without escalated root privileges inside containers
ARG TZ=UTC
ENV PASSWD=mypasswd
RUN apt-get clean && apt-get update && apt-get dist-upgrade -y && apt-get install --no-install-recommends -y \
        apt-utils \
        dbus-user-session \
        fakeroot \
        locales \
        ssl-cert \
        sudo \
        udev \
        tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/* && \
    locale-gen en_US.UTF-8 && \
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && echo "$TZ" > /etc/timezone && \
    # Only use sudo-root for root-owned directory (/dev, /proc, /sys) or user/group permission operations, not for apt-get installation or file/directory operations
    mv -f /usr/bin/sudo /usr/bin/sudo-root && \
    ln -snf /usr/bin/fakeroot /usr/bin/sudo && \
    groupadd -g 1000 ubuntu || echo 'Failed to add ubuntu group' && \
    useradd -ms /bin/bash ubuntu -u 1000 -g 1000 || echo 'Failed to add ubuntu user' && \
    usermod -a -G adm,audio,cdrom,dialout,dip,fax,floppy,games,input,lp,plugdev,render,ssl-cert,sudo,tape,tty,video,voice ubuntu && \
    echo "ubuntu ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "ubuntu:${PASSWD}" | chpasswd && \
    chown -R -f --no-preserve-root ubuntu:ubuntu / || echo 'Failed to set filesystem ownership to ubuntu user'

# Set locales
ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US:en"
ENV LC_ALL="en_US.UTF-8"

USER 1000
# Use BUILDAH_FORMAT=docker in buildah
SHELL ["/usr/bin/fakeroot", "--", "/bin/sh", "-c"]

# Install Selkies-GStreamer system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        # System dependencies
        build-essential \
        curl \
        gdebi-core \
        gnupg \
        software-properties-common \
        jq \
        # GStreamer dependencies
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
        libxext6 \
        # Graphics driver dependencies
        mesa-va-drivers \
        libva2 \
        vainfo \
        vdpau-driver-all \
        libvdpau-va-gl1 \
        vdpauinfo \
        mesa-vulkan-drivers \
        vulkan-tools \
        radeontop && \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then apt-get install --no-install-recommends -y intel-gpu-tools nvtop va-driver-all i965-va-driver-shaders intel-media-va-driver-non-free; fi && \
    if [ "$(grep VERSION_ID= /etc/os-release | cut -d= -f2 | tr -d '\"')" \> "20.04" ]; then apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools; else apt-get install --no-install-recommends -y mesa-utils-extra; fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/* && \
    echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf && \
    # Configure OpenCL manually
    mkdir -pm755 /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && \
    # Configure Vulkan manually
    VULKAN_API_VERSION=$(dpkg -s libvulkan1 | grep -oP 'Version: [0-9|\.]+' | grep -oP '[0-9]+(\.[0-9]+)(\.[0-9]+)') && \
    mkdir -pm755 /etc/vulkan/icd.d/ && echo "{\n\
    \"file_format_version\" : \"1.0.0\",\n\
    \"ICD\": {\n\
        \"library_path\": \"libGLX_nvidia.so.0\",\n\
        \"api_version\" : \"${VULKAN_API_VERSION}\"\n\
    }\n\
}" > /etc/vulkan/icd.d/nvidia_icd.json && \
    # Configure EGL manually
    mkdir -pm755 /usr/share/glvnd/egl_vendor.d/ && echo "{\n\
    \"file_format_version\" : \"1.0.0\",\n\
    \"ICD\": {\n\
        \"library_path\": \"libEGL_nvidia.so.0\"\n\
    }\n\
}" > /usr/share/glvnd/egl_vendor.d/10_nvidia.json
# Expose NVIDIA libraries and paths
ENV PATH="/usr/local/nvidia/bin${PATH:+:${PATH}}"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+${LD_LIBRARY_PATH}:}/usr/local/nvidia/lib:/usr/local/nvidia/lib64"
# Make all NVIDIA GPUs visible by default
ENV NVIDIA_VISIBLE_DEVICES=all
# All NVIDIA driver capabilities should preferably be used, check `NVIDIA_DRIVER_CAPABILITIES` inside the container if things do not work
ENV NVIDIA_DRIVER_CAPABILITIES=all
# Disable VSYNC for NVIDIA GPUs
ENV __GL_SYNC_TO_VBLANK=0
# Set default DISPLAY environment
ENV DISPLAY=":20"

# Install VirtualGL and make libraries available for preload
ENV VGL_DISPLAY=egl
RUN cd /tmp && VIRTUALGL_VERSION="$(curl -fsSL "https://api.github.com/repos/VirtualGL/virtualgl/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g')" && \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
    dpkg --add-architecture i386 && \
    curl -fsSL -O "https://github.com/VirtualGL/virtualgl/releases/download/${VIRTUALGL_VERSION}/virtualgl_${VIRTUALGL_VERSION}_amd64.deb" && \
    curl -fsSL -O "https://github.com/VirtualGL/virtualgl/releases/download/${VIRTUALGL_VERSION}/virtualgl32_${VIRTUALGL_VERSION}_amd64.deb" && \
    apt-get update && apt-get install -y --no-install-recommends "./virtualgl_${VIRTUALGL_VERSION}_amd64.deb" "./virtualgl32_${VIRTUALGL_VERSION}_amd64.deb" && \
    rm -f "virtualgl_${VIRTUALGL_VERSION}_amd64.deb" "virtualgl32_${VIRTUALGL_VERSION}_amd64.deb" && \
    chmod u+s /usr/lib/libvglfaker.so /usr/lib/libvglfaker-nodl.so /usr/lib/libvglfaker-opencl.so /usr/lib/libdlfaker.so /usr/lib/libgefaker.so && \
    chmod u+s /usr/lib32/libvglfaker.so /usr/lib32/libvglfaker-nodl.so /usr/lib32/libvglfaker-opencl.so /usr/lib32/libdlfaker.so /usr/lib32/libgefaker.so && \
    chmod u+s /usr/lib/i386-linux-gnu/libvglfaker.so /usr/lib/i386-linux-gnu/libvglfaker-nodl.so /usr/lib/i386-linux-gnu/libvglfaker-opencl.so /usr/lib/i386-linux-gnu/libdlfaker.so /usr/lib/i386-linux-gnu/libgefaker.so; \
    elif [ "$(dpkg --print-architecture)" = "arm64" ]; then \
    curl -fsSL -O "https://github.com/VirtualGL/virtualgl/releases/download/${VIRTUALGL_VERSION}/virtualgl_${VIRTUALGL_VERSION}_arm64.deb" && \
    apt-get update && apt-get install -y --no-install-recommends ./virtualgl_${VIRTUALGL_VERSION}_arm64.deb && \
    rm -f "virtualgl_${VIRTUALGL_VERSION}_arm64.deb" && \
    chmod u+s /usr/lib/libvglfaker.so /usr/lib/libvglfaker-nodl.so /usr/lib/libdlfaker.so /usr/lib/libgefaker.so; fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

WORKDIR /opt

# Install test dependencies
RUN mkdir -pm755 /etc/apt/preferences.d && echo "Package: firefox*\n\
Pin: version 1:1snap*\n\
Pin-Priority: -1" > /etc/apt/preferences.d/firefox-nosnap && \
    mkdir -pm755 /etc/apt/trusted.gpg.d && curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x0AB215679C571D1C8325275B9BDB3D89CE49EC21" | gpg --dearmor -o /etc/apt/trusted.gpg.d/mozillateam-ubuntu-ppa.gpg && \
    mkdir -pm755 /etc/apt/sources.list.d && echo "deb https://ppa.launchpadcontent.net/mozillateam/ppa/ubuntu $(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"') main" > "/etc/apt/sources.list.d/mozillateam-ubuntu-ppa-$(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"').list" && \
    mkdir -pm755 /etc/apt/trusted.gpg.d && curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xFC43B7352BCC0EC8AF2EEB8B25088A0359807596" | gpg --dearmor -o /etc/apt/trusted.gpg.d/pipewire-debian-ubuntu-pipewire-upstream.gpg && \
    mkdir -pm755 /etc/apt/sources.list.d && echo "deb https://ppa.launchpadcontent.net/pipewire-debian/pipewire-upstream/ubuntu $(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"') main" > "/etc/apt/sources.list.d/pipewire-debian-ubuntu-pipewire-upstream-$(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"').list" && \
    mkdir -pm755 /etc/apt/sources.list.d && echo "deb https://ppa.launchpadcontent.net/pipewire-debian/wireplumber-upstream/ubuntu $(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"') main" > "/etc/apt/sources.list.d/pipewire-debian-ubuntu-wireplumber-upstream-$(grep UBUNTU_CODENAME= /etc/os-release | cut -d= -f2 | tr -d '\"').list" && \
    apt-get update && apt-get install --no-install-recommends -y \
        # PipeWire and WirePlumber
        pipewire \
        pipewire-alsa \
        pipewire-audio-client-libraries \
        pipewire-jack \
        pipewire-locales \
        pipewire-v4l2 \
        pipewire-libcamera \
        gstreamer1.0-pipewire \
        libpipewire-0.3-modules \
        libpipewire-module-x11-bell \
        libspa-0.2-jack \
        libspa-0.2-modules \
        wireplumber \
        wireplumber-locales \
        gir1.2-wp-0.4 \
        # Example packages
        git \
        tmux \
        nano \
        vim \
        wget \
        zip \
        unzip \
        supervisor \
        xvfb \
        xfce4 \
        xfce4-goodies \
        xfce4-terminal \
        mesa-utils \
        adwaita-icon-theme-full \
        dbus-x11 \
        x11-apps \
        firefox \
        pavucontrol \
        jstest-gtk \
        coturn \
        # NGINX web server
        nginx \
        apache2-utils && \
    # Sanitize NGINX path
    sed -i -e 's/\/var\/log\/nginx\/access\.log/\/dev\/stdout/g' -e 's/\/var\/log\/nginx\/error\.log/\/dev\/stderr/g' -e 's/\/run\/nginx\.pid/\/tmp\/nginx\.pid/g' /etc/nginx/nginx.conf && \
    echo "error_log /dev/stderr;" >> /etc/nginx/nginx.conf && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/* && \
    # Prevent dialogs at Xfce4 desktop environment start
    cp -rf /etc/xdg/xfce4/panel/default.xml /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

# Install GStreamer distribution
COPY --chown=1000:1000 --from=selkies-gstreamer /opt/gstreamer ./gstreamer

# Install web application
COPY --chown=1000:1000 --from=selkies-web /usr/share/nginx/html ./gst-web

# Install Joystick Interposer
COPY --chown=1000:1000 --from=selkies-js-interposer /opt/*.deb /opt/selkies-js-interposer.deb
RUN apt-get update && apt-get install --no-install-recommends -y /opt/selkies-js-interposer.deb && rm -f /opt/selkies-js-interposer.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/debconf/* /var/log/* /tmp/* /var/tmp/*

# Install Selkies-GStreamer Python application
ARG PYPI_PACKAGE=selkies_gstreamer
ARG PACKAGE_VERSION=0.0.0.dev0
ARG PIP_BREAK_SYSTEM_PACKAGES=1
COPY --chown=1000:1000 --from=selkies-build /opt/pypi/dist/${PYPI_PACKAGE}-${PACKAGE_VERSION}-py3-none-any.whl .
RUN pip3 install --no-cache-dir --force-reinstall /opt/${PYPI_PACKAGE}-${PACKAGE_VERSION}-py3-none-any.whl

# Copy scripts and configurations used to start the container
COPY --chown=1000:1000 entrypoint.sh /etc/entrypoint.sh
RUN chmod 755 /etc/entrypoint.sh
COPY --chown=1000:1000 selkies-gstreamer-entrypoint.sh /etc/selkies-gstreamer-entrypoint.sh
RUN chmod 755 /etc/selkies-gstreamer-entrypoint.sh
COPY --chown=1000:1000 supervisord.conf /etc/supervisord.conf
RUN chmod 755 /etc/supervisord.conf

# Configure coTURN script
RUN echo "#!/bin/bash\n\
set -e\n\
turnserver \
    --verbose \
    --listening-ip=\"0.0.0.0\" \
    --listening-ip=\"::\" \
    --listening-port=\"\${SELKIES_TURN_PORT:-3478}\" \
    --realm=\"\${TURN_REALM:-example.com}\" \
    --external-ip=\"\${SELKIES_TURN_HOST:-\$(curl -fsSL checkip.amazonaws.com)}\" \
    --min-port=\"\${TURN_MIN_PORT:-49152}\" \
    --max-port=\"\${TURN_MAX_PORT:-65535}\" \
    --channel-lifetime=\"\${TURN_CHANNEL_LIFETIME:--1}\" \
    --lt-cred-mech \
    --user \"selkies:\${TURN_RANDOM_PASSWORD}\" \
    --no-cli \
    --cli-password=\"\${TURN_RANDOM_PASSWORD:-\$(tr -dc 'A-Za-z0-9' < /dev/urandom 2>/dev/null | head -c 24)}\" \
    --allow-loopback-peers \
    \${TURN_EXTRA_ARGS} \$@\
" > /etc/start-turnserver.sh && chmod 755 /etc/start-turnserver.sh

# Configure bashrc to show /etc/motd and /etc/issue
RUN echo "[ ! -z \"\$TERM\" -a -r /etc/motd ] && echo \"\$(grep PRETTY_NAME= /etc/os-release | cut -d= -f2 | tr -d '\\\"')\" && cat /etc/motd" >> /etc/bash.bashrc && \
    echo "==============================================\n\
= Selkies-GStreamer Example Docker Container =\n\
==============================================\n\
\n\
To test the package:\n\
\n\
'/etc/entrypoint.sh' and '/etc/selkies-gstreamer-entrypoint.sh'\n\
\n\
To test the standalone signaling server:\n\
\n\
python3 signalling_web.py --port 8080 --web_root=/opt/gst-web &\
" > /etc/motd

SHELL ["/bin/sh", "-c"]

USER 0
# Enable sudo through sudo-root with uid 0
RUN if [ -d "/usr/libexec/sudo" ]; then SUDO_LIB="/usr/libexec/sudo"; else SUDO_LIB="/usr/lib/sudo"; fi && \
    chown -R -f --no-preserve-root root:root /usr/bin/sudo-root /etc/sudo.conf /etc/sudoers /etc/sudoers.d /etc/sudo_logsrvd.conf "${SUDO_LIB}" || echo 'Failed to provide root permissions to sudo' && \
    chmod -f 4755 /usr/bin/sudo-root || echo 'Failed to set chmod to sudo-root'
USER 1000

ENV PIPEWIRE_LATENCY="32/48000"
ENV XDG_RUNTIME_DIR=/tmp/runtime-ubuntu
ENV PIPEWIRE_RUNTIME_DIR="${PIPEWIRE_RUNTIME_DIR:-${XDG_RUNTIME_DIR:-/tmp}}"
ENV PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}"
ENV PULSE_SERVER="${PULSE_SERVER:-unix:${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}/native}"

# dbus-daemon to the below address is required during startup
ENV DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR:-/tmp}/dbus-session-${DISPLAY#*:}"

USER 1000
ENV SHELL=/bin/bash
ENV USER=ubuntu
ENV HOME=/home/ubuntu
WORKDIR /home/ubuntu

EXPOSE 8080

ENTRYPOINT ["/usr/bin/supervisord"]
