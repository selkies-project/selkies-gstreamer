![Selkies WebRTC](logo/horizontal-480.png)

![Build](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_all_images.yaml/badge.svg)

[![Discord](https://img.shields.io/discord/798699922223398942?logo=discord)](https://discord.gg/wDNGDeSW5F)

**Please read [Troubleshooting](#troubleshooting) first, then use [Discord](https://discord.gg/wDNGDeSW5F) or [GitHub Discussions](https://github.com/selkies-project/selkies-gstreamer/discussions) for support questions. Please only use [Issues](https://github.com/selkies-project/selkies-gstreamer/issues) for technical inquiries or bug reports.**

## What is `selkies-gstreamer`?

`selkies-gstreamer` is a modern open-source low-latency Linux WebRTC HTML5 remote desktop, first started out as a [project by Google engineers](https://web.archive.org/web/20210310083658/https://cloud.google.com/solutions/gpu-accelerated-streaming-using-webrtc) and later maintained by the community.

`selkies-gstreamer` streams a Linux X11 desktop or a Docker/Kubernetes container to a recent web browser using WebRTC with hardware or software acceleration from the server or the client. Linux Wayland, Mac, and Windows support is planned.

This project is adequate as a high-performance replacement to most Linux remote desktop solutions, providing similar performance (at least 30 FPS at 720p with software encoding or at least 60 FPS at Full HD with an NVIDIA GPU) to popular game streaming applications like [Parsec](https://parsec.app), [Moonlight](https://github.com/moonlight-stream) + [Sunshine](https://github.com/LizardByte/Sunshine), [Steam Remote Play](https://store.steampowered.com/remoteplay), [NICE DCV](https://aws.amazon.com/hpc/dcv/), and [FastX](https://www.starnet.com/fastx/). It is also adequate to be used in place of [noVNC](https://github.com/novnc/noVNC) or [Apache Guacamole](https://guacamole.apache.org). You may create a self-hosted version of Shadow, NVIDIA GeForce NOW, Google Stadia, or Xbox Cloud Gaming, running on a Linux host with a web-based client from any operating system.

There are several strengths of `selkies-gstreamer` compared to other game streaming or remote desktop solutions. 

First, `selkies-gstreamer` is much more flexible to be used across various types of environments compared to other services or projects. Its focus on a single web interface instead of multiple native client implementations allow any operating system with a recent web browser to work as a client. Either the built-in HTTP basic authentication feature of `selkies-gstreamer` or any HTTP web server may provide protection to the web interface. Compared to many remote desktop or game streaming applications requiring multiple ports open to stream your desktop across the internet, `selkies-gstreamer` only requires one HTTP web server or reverse proxy which supports WebSocket, or a single TCP port from the server. A TURN server for actual traffic relaying can be flexibly configured within any location at or between the server and the client.

Second, `selkies-gstreamer` can utilize H.264 hardware acceleration of GPUs, as well as falling back to software acceleration with the H.264, VP8, VP9, and AV1 codecs. Audio streaming from the server is supported using the Opus codec. WebRTC ensures minimum latency from the server to the HTML5 web client interface. Any other video encoder, video converter, screen capturing interface, or protocol may be contributed from the community easily. NVIDIA GPUs are currently fully supported with NVENC and AMD, Intel GPUs are supported with VA-API, with progress on supporting other GPU hardware.

Third, `selkies-gstreamer` was designed not only for desktops and bare metal servers, but also for unprivileged Docker and Kubernetes containers. Unlike other similar Linux solutions, there are no dependencies that require access to special devices not available inside containers by default, and is also not dependent on `systemd`. This enables virtual desktop infrastructure (VDI) using containers instead of virtual machines (VMs) which have high overhead. Root permissions are also not required at all, and all components can be installed completely to the userspace.

Fourth, `selkies-gstreamer` is easy to use and expand to various usage cases, attracting users and developers from diverse backgrounds, as it uses [GStreamer](https://gstreamer.freedesktop.org). GStreamer allows pluggable components to be mixed and matched like LEGO blocks to form arbitrary pipelines, providing an easier interface with more comprehensive documentation compared to [FFmpeg](https://ffmpeg.org). Therefore, `selkies-gstreamer` is meant from the start to be a community-built project, where developers from all backgrounds can easily contribute to or expand upon. `selkies-gstreamer` mainly uses [`gst-python`](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/tree/main/subprojects/gst-python), the [Python](https://www.python.org) bindings for GStreamer, [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html), which provides the ability to send a WebRTC remote desktop stream to web browsers from GStreamer, and many more community plugins provided by GStreamer.

# NOTE: PLEASE GO TO v1.5.2. The below instructions are intended for v1.6.0 and will break with the current release.

## How do I get started?

Three components are required to run `selkies-gstreamer`: the [standalone build of GStreamer](addons/gstreamer) with the most recent version, the [Python package](src/selkies_gstreamer) including the signaling server, and the [HTML5 web interface](addons/gst-web). Currently, Ubuntu 24.04 (Mint 22), 22.04 (Mint 21), 20.04 (Mint 20) are supported, but other operating systems should also work if using your own GStreamer build of the newest version (contributions for build workflows of more operating systems are welcome).

All three of the components are built and packaged [every release](https://github.com/selkies-project/selkies-gstreamer/releases). In addition, every latest commit gets built and is made available in container forms [`ghcr.io/selkies-project/selkies-gstreamer/gstreamer`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgstreamer), [`ghcr.io/selkies-project/selkies-gstreamer/py-build`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fpy-build), and [`ghcr.io/selkies-project/selkies-gstreamer/gst-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-web).

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container, or in other cases where the HTML5 web interface loads but the connection fails. This is required for all WebRTC applications, especially since `selkies-gstreamer` is self-hosted, unlike other proprietary services which provide a TURN server for you. Follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

Example Google Compute Engine/Google Kubernetes Engine deployment configurations of all components are available in the [`infra/gce`](infra/gce) and [`infra/gke`](infra/gke) directories. Support in self-hosted Kubernetes clusters is planned.

### Example Docker container

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if you use this in a container WITHOUT host networking (add `--network=host` to the Docker command to enable host networking and work around this requirement if your server is not behind NAT). Follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

An example image [`ghcr.io/selkies-project/selkies-gstreamer/gst-py-example`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-py-example) from the base [example Dockerfile](./Dockerfile.example) is available.

Run the Docker container built from the [`Dockerfile.example`](./Dockerfile.example), then connect to port **8080** of your Docker host to access the web interface (**change `DISTRIB_RELEASE` to `24.04`, `22.04`, or `20.04`, then replace `main` to `latest` for the release build instead of the development build**):

```bash
docker run --pull=always --name selkies -it --rm -p 8080:8080 -p 3478:3478 ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:main-ubuntu${DISTRIB_RELEASE}
```

Repositories [`selkies-vdi`](https://github.com/selkies-project/selkies-vdi) or [`selkies-examples`](https://github.com/selkies-project/selkies-examples) from the [Selkies Project](https://github.com/selkies-project) provide containerized virtual desktop infrastructure (VDI) templates.

[`docker-nvidia-glx-desktop`](https://github.com/selkies-project/docker-nvidia-glx-desktop) and [`docker-nvidia-egl-desktop`](https://github.com/selkies-project/docker-nvidia-egl-desktop) are expandable ready-to-go zero-configuration batteries-included containerized remote desktop implementations of `selkies-gstreamer` supporting hardware acceleration on NVIDIA and other GPUs.

### Install the packaged version on a standalone machine or cloud instance

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

While this instruction assumes that you are installing this project systemwide, it is possible to install and run all components completely within the userspace. Dependencies may also be installed without root permissions if you use [`conda`](https://conda.io) or other userspace package management systems. Documentation contributions for such instructions are welcome.

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq python3-pip python3-dev python3-gi python3-setuptools python3-wheel udev wmctrl libaa1 bzip2 libgcrypt20 libegl1 libgl1 libgles1 libglvnd0 libglx0 libcairo-gobject2 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libsoup2.4-1 libsoup-gnome2.4-1 libgirepository-1.0-1 glib-networking libglib2.0-0 libjson-glib-1.0-0 libgudev-1.0-0 libx11-xcb1 libxcb-dri3-0 libxkbcommon0 libxdamage1 libxfixes3 libxtst6 libxext6 xclip x11-utils xdotool x11-xserver-utils xserver-xorg-core wayland-protocols libwayland-dev libwayland-egl1 libdrm2 alsa-utils jackd2 libjack-jackd2-0 libjpeg-turbo8 libnice10 libogg0 libopenjp2-7 libopus0 pulseaudio libpulse0 libsrtp2-1 libvorbis-dev libvpx-dev libwebp-dev libwebrtc-audio-processing1 x264 x265
```

Install additional packages if using Ubuntu ≥ 22.04 (Mint 21) or a higher equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools dav1d
```

If using supported NVIDIA GPUs, install NVENC (bundled with the GPU driver). If using AMD or Intel GPUs, install its graphics and VA-API drivers, as well as `libva2`. The bundled VA-API driver in the AMDGPU Pro graphics driver is recommended for AMD GPUs and the `i965-va-driver-shaders` or `intel-media-va-driver-non-free` packages are recommended depending on your Intel GPU generation. Optionally install `vainfo`, `intel-gpu-tools`, `radeontop` for GPU monitoring.

2. Unpack the GStreamer components of `selkies-gstreamer` (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`), using your own GStreamer build on any architecture may work **as long as it is the most recent stable version with the required plugins included**:

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/gstreamer-selkies_gpl_${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_amd64.tar.gz" | sudo tar -xzf -
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`. GStreamer builds for ARMv8 are not provided but can be built following procedures in the [GStreamer Dockerfile](addons/gstreamer/Dockerfile).

3. Install the Python components of `selkies-gstreamer` (this component is pure Python and any operating system is compatible, fill in `SELKIES_VERSION`):

```bash
cd /tmp && curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && && sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir --force-reinstall "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
```

4. Unpack the HTML5 components of `selkies-gstreamer`:

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-web_${SELKIES_VERSION}.tar.gz" | sudo tar -xzf -
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `SELKIES_WEB_ROOT` or add the command-line option `--web_root` to `selkies-gstreamer`. Note that you should change `manifest.json` and `cacheName` in `sw.js` to rebrand the web interface to a different name.

5. Install the Joystick Interposer to process gamepad input (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`, and `ARCH` of either `amd64` for x86_64, and `arm64` for ARMv8):

```bash
cd /tmp && curl -o selkies-js-interposer.deb -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-js-interposer_${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_arm64.deb" && sudo apt-get update && sudo apt-get install --no-install-recommends -y ./selkies-js-interposer.deb && rm -f selkies-js-interposer.deb
```

6. Run `selkies-gstreamer` after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY="${DISPLAY:-:0}"
# Configure the Joystick Interposer
export LD_PRELOAD="selkies_joystick_interposer.so${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
sudo mkdir -pm755 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3
# Commented sections are optional
# Start a virtual X11 server, skip this line if an X server already exists or you are already using a display
# Xvfb -screen :0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -noreset -shmem >/tmp/Xvfb.log 2>&1 &
# Ensure the X server is ready
# until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done && echo 'X Server is ready'
# Initialize PulseAudio (set PULSE_SERVER to unix:/run/pulse/native if your user is in the pulse-access group and pulseaudio is triggered with sudo/root), omit the below lines if a PulseAudio server is already running
# export PULSE_SERVER=unix:/tmp/pulse/native
# sudo /usr/bin/pulseaudio -k >/dev/null 2>&1
# /usr/bin/pulseaudio --daemonize --verbose --log-target=file:/tmp/pulseaudio.log --disallow-exit -L 'module-native-protocol-tcp auth-ip-acl=127.0.0.0/8 port=4713 auth-anonymous=1'
# Replace this line with your desktop environment session or skip this line if already running, use VirtualGL `vglrun +wm xfce4-session` here if needed
# [ "${START_XFCE4:-true}" = "true" ] && rm -rf ~/.config/xfce4 && xfce4-session &

# Initialize the GStreamer environment after setting GSTREAMER_PATH to the path of your GStreamer directory
export GST_DEBUG="*:2"
export GSTREAMER_PATH=/opt/gstreamer
. /opt/gstreamer/gst-env
# Replace to your resolution if using without resize, skip if there is a physical display
# selkies-gstreamer-resize 1920x1080

# Choose your video encoder, change to x264enc/vp8enc/vp9enc for software encoding or other encoders for different hardware
# Do not set enable_resize to true if there is a physical display
# Starts the remote desktop process
selkies-gstreamer --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=password --encoder=nvcudah264enc --enable_resize=false &
```

### Install the latest build on a standalone machine or cloud instance

**Build artifacts for every commit are available as an after logging into GitHub in [Actions](https://github.com/selkies-project/selkies-gstreamer/actions), and you do not need Docker to download them.**

Otherwise, Docker (or an equivalent) may be used if you are to use builds from the latest commit. Refer to the above section for more granular informations. This method can be also used when building a new container image with the `FROM [--platform=<platform>] <image> [AS <name>]` and `COPY [--from=<name>] <src_path> <dest_path>` instruction instead of using the `docker` CLI. Change `main` to `latest` if you want the latest release version instead of the latest development version.

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

While this instruction assumes that you are installing this project systemwide, it is possible to install and run all components completely within the userspace. Dependencies may also be installed without root permissions if you use [`conda`](https://conda.io) or other userspace package management systems. Documentation contributions for such instructions are welcome.

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq python3-pip python3-dev python3-gi python3-setuptools python3-wheel udev wmctrl libaa1 bzip2 libgcrypt20 libegl1 libgl1 libgles1 libglvnd0 libglx0 libcairo-gobject2 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libsoup2.4-1 libsoup-gnome2.4-1 libgirepository-1.0-1 glib-networking libglib2.0-0 libjson-glib-1.0-0 libgudev-1.0-0 libx11-xcb1 libxcb-dri3-0 libxkbcommon0 libxdamage1 libxfixes3 libxtst6 libxext6 xclip x11-utils xdotool x11-xserver-utils xserver-xorg-core wayland-protocols libwayland-dev libwayland-egl1 libdrm2 alsa-utils jackd2 libjack-jackd2-0 libjpeg-turbo8 libnice10 libogg0 libopenjp2-7 libopus0 pulseaudio libpulse0 libsrtp2-1 libvorbis-dev libvpx-dev libwebp-dev libwebrtc-audio-processing1 x264 x265
```

Install additional packages if using Ubuntu ≥ 22.04 (Mint 21) or a higher equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools dav1d
```

If using supported NVIDIA GPUs, install NVENC (bundled with the GPU driver). If using AMD or Intel GPUs, install its graphics and VA-API drivers, as well as `libva2`. The bundled VA-API driver in the AMDGPU Pro graphics driver is recommended for AMD GPUs and the `i965-va-driver-shaders` or `intel-media-va-driver-non-free` packages are recommended depending on your Intel GPU generation. Optionally install `vainfo`, `intel-gpu-tools`, `radeontop` for GPU monitoring.

2. Copy the GStreamer build from the container image and move it to `/opt/gstreamer` (fill in the OS version `DISTRIB_RELEASE`):

```bash
docker create --platform="linux/amd64" --name gstreamer ghcr.io/selkies-project/selkies-gstreamer/gstreamer:main-ubuntu${DISTRIB_RELEASE}
sudo docker cp gstreamer:/opt/gstreamer /opt/gstreamer
docker rm gstreamer
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`. GStreamer builds for ARMv8 are not provided but can be built following procedures in the [GStreamer Dockerfile](addons/gstreamer/Dockerfile).

3. Copy the Python Wheel file from the container image and install it (DO NOT change the platform in ARMv8, install [binfmt](https://github.com/tonistiigi/binfmt) instead):

```bash
docker create --platform="linux/amd64" --name selkies-py ghcr.io/selkies-project/selkies-gstreamer/py-build:main
docker cp selkies-py:/opt/pypi/dist/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
docker rm selkies-py
sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir --force-reinstall /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
rm -f /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
```

4. Install the HTML5 components to the container image (DO NOT change the platform in ARMv8, install [binfmt](https://github.com/tonistiigi/binfmt) instead):

```bash
docker create --platform="linux/amd64" --name gst-web ghcr.io/selkies-project/selkies-gstreamer/gst-web:main
sudo docker cp gst-web:/usr/share/nginx/html /opt/gst-web
docker rm gst-web
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `SELKIES_WEB_ROOT` or add the command-line option `--web_root` to `selkies-gstreamer`. Note that you should change `manifest.json` and `cacheName` in `sw.js` to rebrand the web interface to a different name.

5. Install the Joystick Interposer to process gamepad input (fill in the OS version `DISTRIB_RELEASE` and set platform to `linux/arm64` in ARMv8):

```bash
docker create --platform="linux/amd64" --name js-interposer ghcr.io/selkies-project/selkies-gstreamer/js-interposer:main-ubuntu${DISTRIB_RELEASE}
docker cp js-interposer:/opt/selkies-js-interposer_0.0.0.deb /tmp/selkies-js-interposer.deb
docker rm js-interposer
sudo apt-get update && sudo apt-get install --no-install-recommends -y /tmp/selkies-js-interposer.deb
rm -f /tmp/selkies-js-interposer.deb
```

6. Run `selkies-gstreamer` after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY="${DISPLAY:-:0}"
# Configure the Joystick Interposer
export LD_PRELOAD="selkies_joystick_interposer.so${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
sudo mkdir -pm755 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3
# Commented sections are optional
# Start a virtual X11 server, skip this line if an X server already exists or you are already using a display
# Xvfb -screen :0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -noreset -shmem >/tmp/Xvfb.log 2>&1 &
# Ensure the X server is ready
# until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done && echo 'X Server is ready'
# Initialize PulseAudio (set PULSE_SERVER to unix:/run/pulse/native if your user is in the pulse-access group and pulseaudio is triggered with sudo/root), omit the below lines if a PulseAudio server is already running
# export PULSE_SERVER=unix:/tmp/pulse/native
# sudo /usr/bin/pulseaudio -k >/dev/null 2>&1
# /usr/bin/pulseaudio --daemonize --verbose --log-target=file:/tmp/pulseaudio.log --disallow-exit -L 'module-native-protocol-tcp auth-ip-acl=127.0.0.0/8 port=4713 auth-anonymous=1'
# Replace this line with your desktop environment session or skip this line if already running, use VirtualGL `vglrun +wm xfce4-session` here if needed
# [ "${START_XFCE4:-true}" = "true" ] && rm -rf ~/.config/xfce4 && xfce4-session &

# Initialize the GStreamer environment after setting GSTREAMER_PATH to the path of your GStreamer directory
export GST_DEBUG="*:2"
export GSTREAMER_PATH=/opt/gstreamer
. /opt/gstreamer/gst-env
# Replace to your resolution if using without resize, skip if there is a physical display
# selkies-gstreamer-resize 1920x1080

# Choose your video encoder, change to x264enc/vp8enc/vp9enc for software encoding or other encoders for different hardware
# Do not set enable_resize to true if there is a physical display
# Starts the remote desktop process
selkies-gstreamer --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=password --encoder=nvcudah264enc --enable_resize=false &
```

## Usage

### Locking the cursor and fullscreen mode

The cursor can be locked into the web interface using `Control + Shift + Left Click` in web browsers supporting the Pointer Lock API. Press `Escape` to exit this remote cursor mode. This remote cursor capability is useful for most games or graphics applications where the cursor must be confined to the remote screen. Fullscreen mode is available with the shortcut `Control + Shift + F`, or by pressing the fullscreen button in the configuration menu. Press `Escape` for a long time to exit fullscreen mode. The configuration menu is available by clicking the small button on the right of the interface with fullscreen turned off, or by using the shortcut `Control + Shift + M`.

### Command-line options and environment variables

Use `selkies-gstreamer --help` for all command-line options, after sourcing `gst-env`. Environment variables for command-line options are available as capitalizations of the options prepended by `SELKIES_` (such as `SELKIES_VIDEO_BITRATE` for `--video_bitrate`).

### GStreamer components

Below are GStreamer components which are implemented and therefore may be used with `selkies-gstreamer`. Some include environment variables or command-line options which may be used select one type of component, and others are chosen automatically based on the operating system or configuration. This section is to be continuously updated.

This table specifies the currently implemented video encoders and their corresponding codecs, which may be set using the environment variable `SELKIES_ENCODER` or the command-line option `--encoder`.

**GStreamer ≥ 1.22 is the current strict requirement. No support will be provided for older versions.**

| Plugin (set `SELKIES_ENCODER` to) | Codec | Acceleration | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`nvcudah264enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvcudah264enc.html) | H.264 AVC | NVIDIA GPU | All | All Major | NVRTC, `libnvidia-encode` | [Requires NVENC - Encoding H.264 (AVCHD)](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) |
| [`vah264enc`](https://gstreamer.freedesktop.org/documentation/va/vah264enc.html) | H.264 AVC | AMD, Intel GPU | All | All Major | VA-API Driver, `libva` | Requires supported GPU |
| [`x264enc`](https://gstreamer.freedesktop.org/documentation/x264/index.html) | H.264 AVC | Software | All | All Major | `x264` | N/A |
| [`openh264enc`](https://gstreamer.freedesktop.org/documentation/openh264/openh264enc.html) | H.264 AVC | Software | All | All Major | `openh264` | N/A |
| [`nvcudah265enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvcudah265enc.html) | H.265 HEVC | NVIDIA GPU | All | Safari ≥ 17.9 | NVRTC, `libnvidia-encode` | [Requires NVENC - Encoding H.265 (HEVC)](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) |
| [`vah265enc`](https://gstreamer.freedesktop.org/documentation/va/vah265enc.html) | H.265 HEVC | AMD, Intel GPU | All | Safari ≥ 17.9 | VA-API Driver, `libva` | Requires supported GPU |
| [`x265enc`](https://gstreamer.freedesktop.org/documentation/x265/index.html) | H.265 HEVC | Software | All | Safari ≥ 17.9 | `x265` | N/A |
| [`vp8enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp8enc.html) | VP8 | Software | All | All Major | `libvpx` | N/A |
| [`vavp9enc`](https://gstreamer.freedesktop.org/documentation/va/vavp9enc.html) | VP9 | AMD, Intel GPU | All | All Major | VA-API Driver, `libva` | Requires supported GPU and GStreamer ≥ 1.25 |
| [`vp9enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp9enc.html) | VP9 | Software | All | All Major | `libvpx` | N/A |
| [`vaav1enc`](https://gstreamer.freedesktop.org/documentation/va/vaav1enc.html) | AV1 | AMD, Intel GPU | All | Chromium-based, Safari | VA-API Driver, `libva`, [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Requires supported GPU and GStreamer ≥ 1.24 |
| [`rav1enc`](https://gstreamer.freedesktop.org/documentation/rav1e/index.html) | AV1 | Software | All | Chromium-based, Safari | [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Performance Issues |

This table specifies the currently implemented video frame converters used to convert the YUV formats from `BGRx` to `I420` or `NV12`, which are automatically decided based on the encoder types.

| Plugin | Encoders | Acceleration | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`cudaconvert`](https://gstreamer.freedesktop.org/documentation/nvcodec/cudaconvert.html) | `nvcudah264enc`, `nvcudah265enc` | NVIDIA GPU | All | NVRTC | N/A |
| [`vapostproc`](https://gstreamer.freedesktop.org/documentation/va/vapostproc.html) | `vah264enc`, `vah265enc`, `vavp9enc`, `vaav1enc` | AMD, Intel GPU | All | VA-API Driver, `libva` | N/A |
| [`videoconvert`](https://gstreamer.freedesktop.org/documentation/videoconvertscale/videoconvert.html) | `x264enc`, `openh264enc`, `x265enc`, `vp8enc`, `vp9enc`, `rav1enc` | Software | All | N/A | N/A |

This table specifies the currently supported display interfaces and how each plugin selects each video device.

| Plugin | Device Selector | Display Interfaces | Input Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`ximagesrc`](https://gstreamer.freedesktop.org/documentation/ximagesrc/index.html) | `DISPLAY` environment | X.Org / X11 | [`Xlib`](https://github.com/python-xlib/python-xlib) w/ [`pynput`](https://github.com/moses-palmer/pynput) | Linux | Various | N/A |

This table specifies the currently implemented audio encoders and their corresponding codecs. Opus is currently the only adequate fullband audio media codec supported in web browsers by specification.

| Plugin | Codec | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`opusenc`](https://gstreamer.freedesktop.org/documentation/opus/opusenc.html) | Opus | All | All Major | `libopus` | N/A |

This table specifies the currently supported audio interfaces and how each plugin selects each audio device.

| Plugin | Device Selector | Audio Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`pulsesrc`](https://gstreamer.freedesktop.org/documentation/pulseaudio/pulsesrc.html) | `PULSE_SERVER` environment | PulseAudio or PipeWire-Pulse | Linux | `libpulse` | N/A |

This table specifies the currently supported transport protocol components.

| Plugin | Protocols | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html) | [WebRTC](https://webrtc.org) | All | All Major | Various | N/A |

## Using a TURN server

**(IMPORTANT) This is mandatory if the HTML5 web interface loads and the signalling connection works, but the WebRTC connection fails and therefore the remote desktop does not start.**

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container without host networking, or in other cases where the HTML5 web interface loads but the connection to the server fails. This is required for all WebRTC applications, especially since `selkies-gstreamer` is self-hosted, unlike other proprietary services which provide a TURN server for you.**

For an easy fix to when the HTML5 web interface and the signalling connection works, but the WebRTC connection fails in a container, add the option `--network=host` to your Docker command, or add `hostNetwork: true` under your Kubernetes YAML configuration file's pod `spec:` entry, which should be indented in the same depth as `containers:` (note that your cluster may have not allowed this, resulting in an error). This exposes your container to the host network, which disables network isolation. If this does not fix the connection issue (normally when the server is behind another firewall) or you cannot use this fix for security or technical reasons, read the below text.

In most cases when either of your server or client does not have a restrictive firewall, the default Google STUN server configuration will work without additional configuration. However, when connecting from networks that cannot be traversed with STUN, a TURN server is required.

[Open Relay](https://www.metered.ca/tools/openrelay) is a free TURN server instance that may be used for personal testing purposes, but may not be optimal for production usage.

An open-source TURN server for Linux or UNIX-like operating systems that may be used is [coTURN](https://github.com/coturn/coturn), available in major package repositories or as an example container [`coturn/coturn:latest`](https://hub.docker.com/r/coturn/coturn). Alternatively, the `selkies-gstreamer` [`coturn`](addons/coturn) and [`coturn-web`](addons/coturn-web) images [`ghcr.io/selkies-project/selkies-gstreamer/coturn`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn) and [`ghcr.io/selkies-project/selkies-gstreamer/coturn-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn-web) are also included in this repository, and may be used to host your own STUN/TURN infrastructure.

For all other major operating systems including Windows, [Pion TURN](https://github.com/pion/turn)'s `turn-server-simple` executable or [eturnal](https://eturnal.net) are recommended alternative TURN server implementations. [STUNner](https://github.com/l7mp/stunner) is a Kubernetes native STUN and TURN deployment if Helm is possible to be used.

### Install and run coTURN on a standalone machine or cloud instance

It is possible to install [coTURN](https://github.com/coturn/coturn) on your own server or PC from a package repository, as long as the listing port and the relay ports may be opened. In short, `/etc/turnserver.conf` must have the lines `listening-ip=0.0.0.0` and `realm=example.com` (change the realm as appropriate), and either the lines `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)`, or the lines `lt-cred-mech` and `user=yourusername:yourpassword`. It is strongly recommended to set the `min-port=` and `max-port=` parameters which specifies your relay ports between TURN servers (all ports between this range must be open). Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

The `cert=` and `pkey=` options, which lead to the certificate and the private key from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), are required for using TURN over TLS/DTLS, but are otherwise optional.

### Deploy coTURN with Docker

In order to deploy a coTURN container, use the following command (consult this [example configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) for more options which may also be used as command-line arguments). You should be able to expose these ports to the internet. Modify the relay ports `-p 49160-49200:49160-49200/udp` and `--min-port=49160 --max-port=49200` as appropriate (at least one relay port is required). Simply using `--network=host` instead of specifying `-p 49160-49200:49160-49200/udp` is also fine if possible. The relay ports and the listening port must all be open to the internet. Add the `--no-udp-relay` behind `-n` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or `--no-tcp-relay` behind `-n` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

For time-limited shared secret TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --listening-ip=0.0.0.0 --realm=example.com --min-port=49160 --max-port=49200 --use-auth-secret --static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)
```

For legacy long-term TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --listening-ip=0.0.0.0 --realm=example.com --min-port=49160 --max-port=49200 --lt-cred-mech --user=yourusername:yourpassword
```

If you want to use TURN over TLS/DTLS, you must have a valid hostname, and also provision a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), and provide the certificate and private files to the coTURN container with `-v /mylocalpath/coturncert.pem:/etc/coturncert.pem -v /mylocalpath/coturnkey.pem:/etc/coturnkey.pem`, then add the command-line arguments `-n --cert=/etc/coturncert.pem --pkey=/etc/coturnkey.pem` (the specified paths are an example).

More information available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Deploy coTURN With Kubernetes

Before you read, [STUNner](https://github.com/l7mp/stunner) is a pretty good method to deploy a TURN or STUN server on Kubernetes if you are able to use Helm.

You are recommended to use a `ConfigMap` for creating the configuration file for coTURN. Use the [example coTURN configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) as a reference to create a `ConfigMap` which mounts to `/etc/turnserver.conf`. The only mandatory lines are the lines `listening-ip=0.0.0.0` and `realm=example.com` (change the realm as appropriate), and either `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)` or `lt-cred-mech` and `user=yourusername:yourpassword`, but specifying `min-port=` and `max-port=` are strongly recommended to restrict the range of the relay ports.

Use `Deployment` or `DaemonSet` and use `containerPort` and `hostPort` under `ports:` to open the listening port 3478 (or any other port you set in `/etc/turnserver.conf` with `listening-port=`).

Then you must also open all ports between `min-port=` and `max-port=` that you set in `/etc/turnserver.conf`, but this may be skipped if `hostNetwork: true` is used instead. The relay ports and the listening port must all be open to the internet. Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

Under `args:` set `-c /etc/turnserver.conf` and use the `coturn/coturn:latest` image.

If you want to use TURN over TLS/DTLS, use [cert-manager](https://cert-manager.io) to issue a valid certificate with the correct hostname from preferably ZeroSSL (Let's Encrypt may have issues based on the OS), then mount the certificate and private key in the container. Do not forget to include the options `cert=` and `pkey=` in `/etc/turnserver.conf` to the correct path of the certificate and the key.

More information is available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Start `selkies-gstreamer` with the TURN server credentials

Provide the TURN server host address (the environment variable `SELKIES_TURN_HOST` or the command-line option `--turn_host`), port (the environment variable `SELKIES_TURN_PORT` or the command-line option `--turn_port`), and the shared secret (`SELKIES_TURN_SHARED_SECRET`/`--turn_shared_secret`) or the legacy long-term authentication username/password (`SELKIES_TURN_USERNAME`/`--turn_username` and `SELKIES_TURN_PASSWORD`/`--turn_password`) in order to take advantage of the TURN relay capabilities and guarantee connection success.

You may set the environment variable `SELKIES_TURN_PROTOCOL` to `tcp` or set the command-line option `--turn_protocol=tcp` if you are unable to open the UDP listening port to the internet for the coTURN container, or if the UDP protocol is blocked or throttled in your client network.

You may also set `SELKIES_TURN_TLS` to `true` or set `--turn_tls=true` if TURN over TLS/DTLS was properly configured from the TURN server with a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS).

## Development

This project was meant to be built upon community contributions. [GStreamer](https://gstreamer.freedesktop.org) is much easier to develop without prior experience on multimedia application development, and this project is a perfect starting point for anyone who wants to get started. Please give back with a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls) if you made modifications to the code or added new features, especially if you use this project commercially. We will be happy to help if you are stuck.

Regardless of whether you are an experienced developer or engineer already with experience on media pipelines, internet standards, video conferencing applications using SIP or H.323, or all other multimedia projects, just getting started on multimedia development, or even getting started on Python, JavaScript, or HTML, there can be something that you may help. Our code structure enables you to focus on parts of the code that you know best without necessarily understanding the rest.

Even if you are not a developer, you still suggest various improvements including to the documentation, suggest optimized parameters for the video encoders from your experiences using live streaming or video editing software, or become a community helper at [Discord](https://discord.gg/wDNGDeSW5F).

As the relatively permissive license compared to similar projects is for the benefit of the community, please do not take advantage of it. If improvements are not merged, it will ultimately lead to the project becoming unsustainable. We need your help to continue maintaining performance and quality, staying competent compared to proprietary applications.

Please join our [Discord](https://discord.gg/wDNGDeSW5F) server, then start out with the [Issues](https://github.com/selkies-project/selkies-gstreamer/issues) to see if new enhancements that you can make or things that you want solved have been already raised.

We use Docker containers for building every commit. The root directory [`Dockerfile`](./Dockerfile) and Dockerfiles within the [`addons`](addons) directory provide directions for building each component, so that you may replicate the procedures in your own setup even without Docker. When contributing, please follow the overall style of the code, and the names of all variables, classes, or functions have to be unambiguous and as less generic as possible.

If you want new features or improvements but if you are not a developer or lack enough time, please consider offering bounties by contacting us. If you want new features that currently are not yet available with [GStreamer](https://gstreamer.freedesktop.org), we must fund the small pool of full-time GStreamer developers capable of implementing new features in order to bring them to `selkies-gstreamer` as well. Such issues are tagged as requiring an upstream plugin from GStreamer. Even for features or improvements that are ready to be implemented, crowdfunding bounties motivates developers to solve them faster.

### GStreamer advices

Any [GStreamer](https://gstreamer.freedesktop.org) plugin [documentation page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html) is supposed to have a **Hierarchy** section. As all GStreamer objects are defined as **classes** used with object-oriented programming, any properties that you see in parent classes are also properties that you may use for your own classes and plugins. Therefore, all contributors implementing or modifying code relevant to GStreamer are also to carefully check parent classes as well when configuring [properties](https://gstreamer.freedesktop.org/documentation/plugin-development/basics/args.html) or [capabilities](https://gstreamer.freedesktop.org/documentation/gstreamer/gstcaps.html).

## Troubleshooting

### The HTML5 web interface loads and the signalling connection works, but the WebRTC connection fails or the remote desktop does not start.

First of all, use HTTPS or HTTP port forwarding to localhost as much as possible. Browsers do not support WebRTC or relevant features including pointer and keyboard lock in HTTP outside localhost. Also check if the WebRTC video codec is supported in the web browser, as the server may panic if the codecs do not match. Moreover, ensure that there is a running PulseAudio or PipeWire-Pulse session as the interface does not establish without an audio server.

Then, please read [Using a TURN server](#using-a-turn-server).

Make sure to also check that you enabled automatic login with your display manager, as the remote desktop cannot access the initial login screen after boot without login. If you created the TURN server or the example container inside a VPN-enabled environment or virtual machine and the WebRTC connection fails, then you may need to add the `SELKIES_TURN_HOST` environment variable to the private VPN IP of the TURN server host, such as `192.168.0.2`.

### The web interface refuses to start up in the terminal after rebooting my computer or restarting my desktop in a standalone instance.

This is because the desktop session starts as `root` when the user is not logged in. Next time, set up automatic login in the settings with the user you want to use. In order to use the web interface when this is not possible (or when you are using SSH or remote access), check `sudo systemctl status sddm`, `sudo systemctl status lightdm`, or `sudo systemctl status gdm3` (use your display session manager) and find the path next to the `-auth` argument. Set the environment variable `XAUTHORITY` to the path you found while running `selkies-gstreamer` as `root`.

### The HTML5 web interface is slow and laggy.

**Usually, the issue arises from using a WiFi router with bufferbloat issues, especially if you observe stuttering. Try using the [Bufferbloat Test](https://www.waveform.com/tools/bufferbloat) to identify the issue first before moving on.** Using wired ethernet or a good 5GHz WiFi connection is important. Ensure that the latency to your TURN server from the server and the client is ideally under 50 ms. If the latency is too high, your connection may be too laggy for any remote desktop application. Also note that a higher framerate will improve performance if you have sufficient bandwidth. This is because one screen refresh from a 60 fps screen takes 16.67 ms at a time, while one screen refresh from a 15 fps screen inevitably takes 66.67 ms, and therefore inherently causes a visible lag.

If the latency becomes higher while the screen is idle or when the tab is not focused, the internal efficiency control mechanism of the web browser may activate, which will be resolved automatically after a few seconds if there is new activity. If it does not, disable all power saving or efficiency features available in the web browser. In Windows 10 or 11, try `Start > Settings > System > Power & battery > Power mode > Best performance`. Also, note that if you saturate your CPU or GPU with an application on the host, the remote desktop interface will also substantially slow down as it cannot use the CPU or GPU enough to decode the screen.

However, it might be that the parameters for the WebRTC interface, video encoders, RTSP, or other [GStreamer](https://gstreamer.freedesktop.org) plugins are not optimized enough. If you find that it is the case, we always welcome contributions. If your changes show noticeably better results in the same conditions, please make a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls), or tell us about the parameters in any channel that we can reach so that we can also test.

### My touchpad does not move while pressing a key with the keyboard.

This is a setting from the client operating system and will show the same behavior with other applications. In Windows, go to `Settings > Bluetooth & devices > Touchpad > Taps` to increase your touchpad sensitivity. In Linux or Mac, turn off the setting `Touchpad > Disable while typing`.

### I want to pass multiple screens within a server to another client using the WebRTC HTML5 web interface.

You can start a new instance of `selkies-gstreamer` by changing the `DISPLAY` environment variable and setting a different web interface port in a different terminal to pass a different screen simultaneously to your current screen.

### I want to test a shared secret TURN server by manually generating a TURN credential from a shared secret.

The below steps are required when you want to test your TURN server configured with a shared secret instead of the legacy username/password authentication.

1. Run the test container:

```bash
docker-compose run --service-ports test
```

2. From inside the test container, call the `generate_rtc_config` method.

```bash
export SELKIES_TURN_HOST="Your TURN Host"
export SELKIES_TURN_PORT="Your TURN Port"
export SELKIES_TURN_SECRET="Your Shared Secret"
export SELKIES_TURN_USER="user"

python3 -c 'import os;from selkies_gstreamer.signalling_web import generate_rtc_config; print(generate_rtc_config(os.environ["SELKIES_TURN_HOST"], os.environ["SELKIES_TURN_PORT"], os.environ["SELKIES_TURN_SECRET"], os.environ["SELKIES_TURN_USER"]))'
```

> You can then test your TURN server configuration from the [Trickle ICE](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/) webpage.

---
This work was supported in part by National Science Foundation (NSF) awards CNS-1730158, ACI-1540112, ACI-1541349, OAC-1826967, OAC-2112167, CNS-2100237, CNS-2120019, the University of California Office of the President, and the University of California San Diego's California Institute for Telecommunications and Information Technology/Qualcomm Institute. Thanks to CENIC for the 100Gbps networks.
