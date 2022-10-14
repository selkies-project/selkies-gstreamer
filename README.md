![Selkies WebRTC](logo/horizontal-480.png)

![Build](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_all_images.yaml/badge.svg)

[![Discord](https://img.shields.io/discord/798699922223398942?logo=discord)](https://discord.gg/wDNGDeSW5F)

**Please read [Troubleshooting](#troubleshooting) first, then use [Discord](https://discord.gg/wDNGDeSW5F) or [GitHub Discussions](https://github.com/selkies-project/selkies-gstreamer/discussions) for support questions. Please only use [Issues](https://github.com/selkies-project/selkies-gstreamer/issues) for technical inquiries or bug reports.**

## What is `selkies-gstreamer`?

`selkies-gstreamer` is a modern open-source low-latency Linux WebRTC HTML5 remote desktop, first started out as a [project by Google engineers](https://web.archive.org/web/20210310083658/https://cloud.google.com/solutions/gpu-accelerated-streaming-using-webrtc) and currently supported by [itopia](https://itopia.com). `selkies-gstreamer` streams a Linux X11 desktop or a Docker or Kubernetes container to a recent web browser using WebRTC with hardware or software acceleration from the server or the client. Linux Wayland, Mac, and Windows support is planned.

This project is adequate as a high-performance replacement to most Linux remote desktop solutions, providing similar performance (at least 30 FPS at 720p with software encoding or at least 60+ FPS at Full HD with an NVIDIA GPU) to popular game streaming applications like [Parsec](https://parsec.app), [Moonlight](https://github.com/moonlight-stream) + [Sunshine](https://github.com/LizardByte/Sunshine), [Steam Remote Play](https://store.steampowered.com/remoteplay), and [NICE DCV](https://aws.amazon.com/hpc/dcv/). It is also adequate to be used in place of [noVNC](https://github.com/novnc/noVNC) or [Apache Guacamole](https://guacamole.apache.org). You may create a self-hosted version of Shadow, NVIDIA GeForce NOW, Google Stadia, or Xbox Cloud Gaming, running on a Linux host with a web-based client from any operating system.

There are several strengths of `selkies-gstreamer` compared to other game streaming or remote desktop solutions. 

First, `selkies-gstreamer` is much more flexible to be used across various types of environments compared to other services or projects. Its focus on a single web interface instead of multiple native client implementations allow any operating system with a recent web browser to work as a client. Either the built-in HTTP basic authentication feature of `selkies-gstreamer` or any HTTP web server may provide protection to the web interface. Compared to many remote desktop or game streaming applications requiring multiple ports open to stream your desktop across the internet, `selkies-gstreamer` only requires one HTTP web server or reverse proxy which supports WebSocket, or a single TCP port from the server. A TURN server for actual traffic relaying can be flexibly configured within any location at or between the server and the client.

Second, `selkies-gstreamer` can utilize H.264 hardware acceleration of GPUs, as well as falling back to software acceleration with the H.264, VP8, and VP9 codecs. Audio streaming from the server is supported using the Opus codec. WebRTC ensures minimum latency from the server to the HTML5 web client interface. Any other video encoder, video converter, screen capturing interface, or protocol may be contributed from the community easily. NVIDIA GPUs are currently fully supported with NVENC, with progress on supporting AMD, Intel, and other GPU hardware.

Third, `selkies-gstreamer` was designed not only for desktops and bare metal servers, but also for unprivileged Docker and Kubernetes containers. Unlike other similar Linux solutions, there are no dependencies that require access to special devices not available inside containers by default, and is also not dependent on `systemd`. This enables virtual desktop infrastructure (VDI) using containers instead of virtual machines (VMs) which have high overhead.

Fourth, `selkies-gstreamer` is easy to use and expand to various usage cases, attracting users and developers from diverse backgrounds, as it uses [GStreamer](https://gstreamer.freedesktop.org). GStreamer allows pluggable components to be mixed and matched like LEGO blocks to form arbitrary pipelines, providing an easier interface with more comprehensive documentation compared to [FFmpeg](https://ffmpeg.org). Therefore, `selkies-gstreamer` is meant from the start to be a community-built project, where developers from all backgrounds can easily contribute to or expand upon. `selkies-gstreamer` mainly uses [`gst-python`](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/tree/main/subprojects/gst-python), the [Python](https://www.python.org) bindings for GStreamer, [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html), which provides the ability to send a WebRTC remote desktop stream to web browsers from GStreamer, and many more community plugins provided by GStreamer.

## How do I get started?

Three components are required to run `selkies-gstreamer`: the [standalone build of GStreamer](addons/gstreamer) with the most recent version, the [Python package](src/selkies_gstreamer) including the signaling server, and the [HTML5 web interface](addons/gst-web). Currently, Ubuntu 18.04 (Mint 19), 20.04 (Mint 20), 22.04 (Mint 21) are supported, but other operating systems should also work if using your own GStreamer build of the newest version (contributions for build workflows of more operating systems are welcome).

All three of the components are built and packaged [every release](https://github.com/selkies-project/selkies-gstreamer/releases). In addition, every latest commit gets built and is made available in container forms [`ghcr.io/selkies-project/selkies-gstreamer/gstreamer`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgstreamer), [`ghcr.io/selkies-project/selkies-gstreamer/py-build`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fpy-build), and [`ghcr.io/selkies-project/selkies-gstreamer/gst-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-web).

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container, or in other cases where the HTML5 web interface loads but the connection fails. This is required for all WebRTC applications, especially since `selkies-gstreamer` is self-hosted, unlike other proprietary services which provide a TURN server for you. Follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

Example Google Compute Engine/Google Kubernetes Engine deployment configurations of all components are available in the [`infra/gce`](infra/gce) and [`infra/gke`](infra/gke) directories. Commercial support on Google Cloud is available with [itopia Spaces](https://itopiaspaces.com).

### Example Docker container

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if you use this in a container WITHOUT host networking (add `--network=host` to the Docker command to enable host networking and work around this requirement if your server is not behind NAT). Follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

An example image [`ghcr.io/selkies-project/selkies-gstreamer/gst-py-example`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-py-example) from the base [example Dockerfile](./Dockerfile.example) is available.

Run the docker container built from the [`Dockerfile.example`](./Dockerfile.example), then connect to port **8080** of your Docker host to access the web interface (**replace `latest` to `master` for the development build instead of the release build, and choose the Ubuntu versions `18.04`, `20.04`, or `22.04`**):

```bash
docker run --name selkies -it --rm -p 8080:8080 ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:latest-ubuntu20.04
```

Repositories [`selkies-vdi`](https://github.com/selkies-project/selkies-vdi) or [`selkies-examples`](https://github.com/selkies-project/selkies-examples) from the [Selkies Project](https://github.com/selkies-project) provide containerized virtual desktop infrastructure (VDI) templates.

[`docker-nvidia-glx-desktop`](https://github.com/ehfd/docker-nvidia-glx-desktop) and [`docker-nvidia-egl-desktop`](https://github.com/ehfd/docker-nvidia-egl-desktop) are expandable ready-to-go zero-configuration batteries-included containerized remote desktop implementations of `selkies-gstreamer` supporting hardware acceleration on NVIDIA and other GPUs.

### Install the packaged version on a standalone machine or cloud instance

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y adwaita-icon-theme-full build-essential python3-pip python3-dev python3-gi python3-setuptools python3-wheel tzdata sudo udev xclip x11-utils xdotool wmctrl jq gdebi-core x11-xserver-utils xserver-xorg-core libopus0 libgdk-pixbuf2.0-0 libsrtp2-1 libxdamage1 libxml2-dev libwebrtc-audio-processing1 libcairo-gobject2 pulseaudio libpulse0 libpangocairo-1.0-0 libgirepository1.0-dev libjpeg-dev libvpx-dev zlib1g-dev x264
```

Additionally, install `xcvt` if using Ubuntu 22.04 (Mint 21) or an equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt
```

2. Unpack the GStreamer components of `selkies-gstreamer` (fill in `SELKIES_VERSION` and `UBUNTU_RELEASE`), using your own GStreamer build may work **as long as it is the most recent version with the required plugins included**:

```bash
cd /opt && curl -fsSL https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-v${SELKIES_VERSION}-ubuntu${UBUNTU_RELEASE}.tgz | sudo tar -zxf -
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`.

3. Install the Python components of `selkies-gstreamer` (this component is pure Python and any operating system is compatible, fill in `SELKIES_VERSION`):

```bash
cd /tmp && curl -O -fsSL https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl && sudo pip3 install selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl && rm -f selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl && sudo pip3 install --upgrade --no-deps --force-reinstall https://github.com/python-xlib/python-xlib/archive/e8cf018.zip
```

4. Unpack the HTML5 components of `selkies-gstreamer`:

```bash
cd /opt && curl -fsSL https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-web-v${SELKIES_VERSION}.tgz | sudo tar -zxf -
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `WEB_ROOT` or add the command-line option `--web_root` to `selkies-gstreamer`.

5. If using NVIDIA GPUs for hardware acceleration, run this command (make sure the NVIDIA CUDA Toolkit is installed before this):

```bash
cd /usr/local/cuda/lib64 && sudo find . -maxdepth 1 -type l -name "*libnvrtc.so.*" -exec sh -c 'ln -sf $(basename {}) libnvrtc.so' \;
```

6. Run `selkies-gstreamer` after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY=:0
export GST_DEBUG=*:2
export PULSE_SERVER=127.0.0.1:4713
# Initialize the GStreamer environment after setting GSTREAMER_PATH to the path of your GStreamer directory
export GSTREAMER_PATH=/opt/gstreamer
source /opt/gstreamer/gst-env
# Start a virtual X server, skip this line if an X server already exists or you are already using a display
Xvfb -screen :0 8192x4096x24 +extension RANDR +extension GLX +extension MIT-SHM -nolisten tcp -noreset -shmem 2>&1 >/tmp/Xvfb.log &
# Ensure the X server is ready
until [[ -S /tmp/.X11-unix/X0 ]]; do sleep 1; done && echo 'X Server is ready'
# Initialize PulseAudio, TCP interface to port 4713 must be configured if using a separate setup
sudo /usr/bin/pulseaudio -k >/dev/null 2>&1
sudo /usr/bin/pulseaudio --daemonize --system --verbose --log-target=file:/tmp/pulseaudio.log --realtime=true --disallow-exit -L 'module-native-protocol-tcp auth-ip-acl=127.0.0.0/8 port=4713 auth-anonymous=1'
# Replace this line with your desktop environment session or skip this line if already running, use VirtualGL `vglrun` here if needed
[[ "${START_XFCE4:-true}" == "true" ]] && rm -rf ~/.config/xfce4 && xfce4-session &
# Write Progressive Web App (PWA) config.
export PWA_APP_NAME="Selkies WebRTC"
export PWA_APP_SHORT_NAME="selkies"
export PWA_START_URL="/index.html"
sed -i \
    -e "s|PWA_APP_NAME|${PWA_APP_NAME}|g" \
    -e "s|PWA_APP_SHORT_NAME|${PWA_APP_SHORT_NAME}|g" \
    -e "s|PWA_START_URL|${PWA_START_URL}|g" \
/opt/gst-web/manifest.json
sed -i \
    -e "s|PWA_CACHE|${PWA_APP_SHORT_NAME}-webrtc-pwa|g" \
/opt/gst-web/sw.js
# Choose your video encoder
export WEBRTC_ENCODER=x264enc
# Do not enable resize if there is a physical display
export WEBRTC_ENABLE_RESIZE=${WEBRTC_ENABLE_RESIZE:-false}
# Replace to your resolution if using without resize, skip if there is a physical display
selkies-gstreamer-resize 1280x720
# Starts the remote desktop process
selkies-gstreamer &
```

### Install the latest build on a standalone machine or cloud instance

Docker (or an equivalent) is required if you are to use builds from the latest commit. Refer to the above section for more granular informations. This method can be also used when building a new container image with the `FROM [--platform=<platform>] <image> [AS <name>]` and `COPY [--from=<name>] <src_path> <dest_path>` instruction instead of using the `docker` CLI. **Change `master` to `latest` if you want the latest release version instead of the latest development version.**

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](#using-a-turn-server) in order to make the container work using an external TURN server.**

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y adwaita-icon-theme-full build-essential python3-pip python3-dev python3-gi python3-setuptools python3-wheel tzdata sudo udev xclip x11-utils xdotool wmctrl jq gdebi-core x11-xserver-utils xserver-xorg-core libopus0 libgdk-pixbuf2.0-0 libsrtp2-1 libxdamage1 libxml2-dev libwebrtc-audio-processing1 libcairo-gobject2 pulseaudio libpulse0 libpangocairo-1.0-0 libgirepository1.0-dev libjpeg-dev libvpx-dev zlib1g-dev x264
```

Additionally, install `xcvt` if using Ubuntu 22.04 (Mint 21) or an equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt
```

2. Copy the GStreamer build from the container image and move it to `/opt/gstreamer` (change the OS version `UBUNTU_RELEASE` as needed):

```bash
docker pull ghcr.io/selkies-project/selkies-gstreamer/gstreamer:master-ubuntu${UBUNTU_RELEASE}
docker create --name gstreamer ghcr.io/selkies-project/selkies-gstreamer/gstreamer:master-ubuntu${UBUNTU_RELEASE}
sudo docker cp gstreamer:/opt/gstreamer /opt/gstreamer
docker rm gstreamer
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`.

3. Copy the Python Wheel file from the container image and install it:

```bash
docker pull ghcr.io/selkies-project/selkies-gstreamer/py-build:master
docker create --name selkies-py ghcr.io/selkies-project/selkies-gstreamer/py-build:master
docker cp selkies-py:/opt/pypi/dist/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
docker rm selkies-py
sudo pip3 install /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
rm -f /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
sudo pip3 install --upgrade --no-deps --force-reinstall https://github.com/python-xlib/python-xlib/archive/e8cf018.zip
```

4. Install the HTML5 components to the container image:

```bash
docker pull ghcr.io/selkies-project/selkies-gstreamer/gst-web:master
docker create --name gst-web ghcr.io/selkies-project/selkies-gstreamer/gst-web:master
sudo docker cp gst-web:/usr/share/nginx/html /opt/gst-web
docker rm gst-web
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `WEB_ROOT` or add the command-line option `--web_root` to `selkies-gstreamer`.

5. If using NVIDIA GPUs for hardware acceleration, run this command (make sure the NVIDIA CUDA Toolkit is installed before this):

```bash
cd /usr/local/cuda/lib64 && sudo find . -maxdepth 1 -type l -name "*libnvrtc.so.*" -exec sh -c 'ln -sf $(basename {}) libnvrtc.so' \;
```

6. Run `selkies-gstreamer` after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY=:0
export GST_DEBUG=*:2
export PULSE_SERVER=127.0.0.1:4713
# Initialize the GStreamer environment after setting GSTREAMER_PATH to the path of your GStreamer directory
export GSTREAMER_PATH=/opt/gstreamer
source /opt/gstreamer/gst-env
# Start a virtual X server, skip this line if an X server already exists or you are already using a display
Xvfb -screen :0 8192x4096x24 +extension RANDR +extension GLX +extension MIT-SHM -nolisten tcp -noreset -shmem 2>&1 >/tmp/Xvfb.log &
# Ensure the X server is ready
until [[ -S /tmp/.X11-unix/X0 ]]; do sleep 1; done && echo 'X Server is ready'
# Initialize PulseAudio, TCP interface to port 4713 must be configured if using a separate setup
sudo /usr/bin/pulseaudio -k >/dev/null 2>&1
sudo /usr/bin/pulseaudio --daemonize --system --verbose --log-target=file:/tmp/pulseaudio.log --realtime=true --disallow-exit -L 'module-native-protocol-tcp auth-ip-acl=127.0.0.0/8 port=4713 auth-anonymous=1'
# Replace this line with your desktop environment session or skip this line if already running, use VirtualGL `vglrun` here if needed
[[ "${START_XFCE4:-true}" == "true" ]] && rm -rf ~/.config/xfce4 && xfce4-session &
# Write Progressive Web App (PWA) config.
export PWA_APP_NAME="Selkies WebRTC"
export PWA_APP_SHORT_NAME="selkies"
export PWA_START_URL="/index.html"
sed -i \
    -e "s|PWA_APP_NAME|${PWA_APP_NAME}|g" \
    -e "s|PWA_APP_SHORT_NAME|${PWA_APP_SHORT_NAME}|g" \
    -e "s|PWA_START_URL|${PWA_START_URL}|g" \
/opt/gst-web/manifest.json
sed -i \
    -e "s|PWA_CACHE|${PWA_APP_SHORT_NAME}-webrtc-pwa|g" \
/opt/gst-web/sw.js
# Choose your video encoder
export WEBRTC_ENCODER=x264enc
# Do not enable resize if there is a physical display
export WEBRTC_ENABLE_RESIZE=${WEBRTC_ENABLE_RESIZE:-false}
# Replace to your resolution if using without resize, skip if there is a physical display
selkies-gstreamer-resize 1280x720
# Starts the remote desktop process
selkies-gstreamer &
```

## Usage

### Locking the cursor and fullscreen mode

The cursor can be locked into the web interface using `Control + Shift + Left Click` in web browsers supporting the Pointer Lock API. Press `Escape` to exit this remote cursor mode. This remote cursor capability is useful for most games or graphics applications where the cursor must be confined to the remote screen. Fullscreen mode is available with the shortcut `Control + Shift + F`, or by pressing the fullscreen button in the configuration menu. Press `Escape` for a long time to exit fullscreen mode. The configuration menu is available by clicking the small button on the right of the interface with fullscreen turned off, or by using the shortcut `Control + Shift + M`.

### Command-line options and environment variables

Use `selkies-gstreamer --help` for all command-line options, after sourcing `gst-env`. Environment variables for each of the command-line options are available within [`__main__.py`](src/selkies_gstreamer/__main__.py). 

### GStreamer components

Below are GStreamer components which are implemented and therefore may be used with `selkies-gstreamer`. Some include environment variables or command-line options which may be used select one type of component, and others are chosen automatically based on the operating system or configuration. This section is to be continuously updated.

This table specifies the currently implemented video encoders and their corresponding codecs, which may be set using the environment variable `WEBRTC_ENCODER` or the command-line option `--encoder`.

| Plugin (set `WEBRTC_ENCODER` to) | Codec | Acceleration | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`x264enc`](https://gstreamer.freedesktop.org/documentation/x264/index.html) | H.264 AVC | Software | All | All Major | `x264` | N/A |
| [`vp8enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp8enc.html) | VP8 | Software | All | All Major | `libvpx` | N/A |
| [`vp9enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp9enc.html) | VP9 | Software | All | Chromium-based, Firefox | `libvpx` | N/A |
| [`nvh264enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvh264enc.html) | H.264 AVC | NVIDIA GPU | All | All Major | [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) | [Requires NVENC - Encoding H.264 AVCHD](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) |

This table specifies the currently implemented video frame converters used to convert the YUV formats from `BGRx` to `I420`, which are automatically decided based on the encoder types.

| Plugin | Encoders | Acceleration | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`videoconvert`](https://gstreamer.freedesktop.org/documentation/videoconvertscale/videoconvert.html) | `x264enc`, `vp8enc`, `vp9enc` | Software | All | Various | N/A |
| [`cudaconvert`](https://gstreamer.freedesktop.org/documentation/nvcodec/cudaconvert.html) | `nvh264enc` | NVIDIA GPU | Linux | [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) | N/A |

This table specifies the currently supported display interfaces and how each plugin selects each video device.

| Plugin | Device Selector | Display Interfaces | Input Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`ximagesrc`](https://gstreamer.freedesktop.org/documentation/ximagesrc/index.html) | `DISPLAY` environment | X.Org / X11 | [`Xlib`](https://github.com/python-xlib/python-xlib) w/ [`pynput`](https://github.com/moses-palmer/pynput), `uinput` | Linux | Various | N/A |

This table specifies the currently implemented audio encoders and their corresponding codecs. Opus is currently the only adequate media codec supported in web browsers by specification.

| Plugin | Codec | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`opusenc`](https://gstreamer.freedesktop.org/documentation/opus/opusenc.html) | Opus | All | All Major | `libopus` | N/A |

This table specifies the currently supported audio interfaces and how each plugin selects each audio device.

| Plugin | Device Selector | Audio Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`pulsesrc`](https://gstreamer.freedesktop.org/documentation/pulseaudio/pulsesrc.html) | `PULSE_SERVER` environment | PulseAudio | Linux | `libpulse` | N/A |

This table specifies the currently supported transport protocol components.

| Plugin | Protocols | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html) | [WebRTC](https://webrtc.org) | All | All Major | Various | N/A |

## Using a TURN server

**You are at the right place if the HTML5 web interface loads and the signalling connection works, but the WebRTC connection fails and therefore the remote desktop does not start.**

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container without host networking, or in other cases where the HTML5 web interface loads but the connection to the server fails. This is required for all WebRTC applications, especially since `selkies-gstreamer` is self-hosted, unlike other proprietary services which provide a TURN server for you.**

For an easy fix to when the HTML5 web interface and the signalling connection works, but the WebRTC connection fails in a container, add the option `--network=host` to your Docker command, or add `hostNetwork: true` under your Kubernetes YAML configuration file's pod `spec:` entry, which should be indented in the same depth as `containers:` (note that your cluster may have not allowed this, resulting in an error). This exposes your container to the host network, which disables network isolation. If this does not fix the connection issue (normally when the server is behind another firewall) or you cannot use this fix for security or technical reasons, read the below text.

In most cases when either of your server or client does not have a restrictive firewall, the default Google STUN server configuration will work without additional configuration. However, when connecting from networks that cannot be traversed with STUN, a TURN server is required.

[Open Relay](https://www.metered.ca/tools/openrelay) is a free TURN server instance that may be used for personal testing purposes, but may not be optimal for production usage.

An open-source TURN server for Linux or UNIX-like operating systems that may be used is [coTURN](https://github.com/coturn/coturn), available in major package repositories or as an example container [`coturn/coturn:latest`](https://hub.docker.com/r/coturn/coturn). Alternatively, the `selkies-gstreamer` [`coturn`](addons/coturn) and [`coturn-web`](addons/coturn-web) images [`ghcr.io/selkies-project/selkies-gstreamer/coturn`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn) and [`ghcr.io/selkies-project/selkies-gstreamer/coturn-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn-web) are also included in this repository, and may be used to host your own STUN/TURN infrastructure.

For all other major operating systems including Windows, [Pion TURN](https://github.com/pion/turn)'s `turn-server-simple` executable or [eturnal](https://eturnal.net) are recommended alternative TURN server implementations. [STUNner](https://github.com/l7mp/stunner) is a Kubernetes native STUN and TURN deployment if Helm is possible to be used.

### Install and run coTURN on a standalone machine or cloud instance

It is possible to install [coTURN](https://github.com/coturn/coturn) on your own server or PC from a package repository, as long as the listing port and the relay ports may be opened. In short, `/etc/turnserver.conf` must have either the lines `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)`, or the lines `lt-cred-mech` and `user=yourusername:yourpassword`. It is strongly recommended to set the `min-port=` and `max-port=` parameters which specifies your relay ports between TURN servers (all ports between this range must be open). Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

The `cert=` and `pkey=` options, which lead to the certificate and the private key from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), are required for using TURN over TLS/DTLS, but are otherwise optional.

### Deploy coTURN with Docker

In order to deploy a coTURN container, use the following command (consult this [example configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) for more options which may also be used as command-line arguments). You should be able to expose these ports to the internet. Modify the relay ports `-p 49160-49200:49160-49200/udp` and `--min-port=49160 --max-port=49200` as appropriate (at least one relay port is required). Simply using `--network=host` instead of specifying `-p 49160-49200:49160-49200/udp` is also fine if possible. The relay ports and the listening port must all be open to the internet. Add the `--no-udp-relay` behind `-n` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or `--no-tcp-relay` behind `-n` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

For time-limited shared secret TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --min-port=49160 --max-port=49200 --use-auth-secret --static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)
```

For legacy long-term TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --min-port=49160 --max-port=49200 --lt-cred-mech --user=yourusername:yourpassword
```

If you want to use TURN over TLS/DTLS, you must have a valid hostname, and also provision a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), and provide the certificate and private files to the coTURN container with `-v /mylocalpath/coturncert.pem:/etc/coturncert.pem -v /mylocalpath/coturnkey.pem:/etc/coturnkey.pem`, then add the command-line arguments `-n --cert=/etc/coturncert.pem --pkey=/etc/coturnkey.pem` (the specified paths are an example).

More information available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Deploy coTURN With Kubernetes

Before you read, [STUNner](https://github.com/l7mp/stunner) is a pretty good method to deploy a TURN or STUN server on Kubernetes if you are able to use Helm.

You are recommended to use a `ConfigMap` for creating the configuration file for coTURN. Use the [example coTURN configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) as a reference to create a `ConfigMap` which mounts to `/etc/turnserver.conf`. The only mandatory lines are either `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)` or `lt-cred-mech` and `user=yourusername:yourpassword`, but specifying `min-port=` and `max-port=` are strongly recommended to restrict the range of the relay ports.

Use `Deployment` or `DaemonSet` and use `containerPort` and `hostPort` under `ports:` to open the listening port 3478 (or any other port you set in `/etc/turnserver.conf` with `listening-port=`).

Then you must also open all ports between `min-port=` and `max-port=` that you set in `/etc/turnserver.conf`, but this may be skipped if `hostNetwork: true` is used instead. The relay ports and the listening port must all be open to the internet. Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

Under `args:` set `-c /etc/turnserver.conf` and use the `coturn/coturn:latest` image.

If you want to use TURN over TLS/DTLS, use [cert-manager](https://cert-manager.io) to issue a valid certificate with the correct hostname from preferably ZeroSSL (Let's Encrypt may have issues based on the OS), then mount the certificate and private key in the container. Do not forget to include the options `cert=` and `pkey=` in `/etc/turnserver.conf` to the correct path of the certificate and the key.

More information is available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Start `selkies-gstreamer` with the TURN server credentials

Provide the TURN server host address (the environment variable `TURN_HOST` or the command-line option `--turn_host`), port (the environment variable `TURN_PORT` or the command-line option `--turn_port`), and the shared secret (`TURN_SHARED_SECRET`/`--turn_shared_secret`) or the legacy long-term authentication username/password (`TURN_USERNAME`/`--turn_username` and `TURN_PASSWORD`/`--turn_password`) in order to take advantage of the TURN relay capabilities and guarantee connection success.

You may set the environment variable `TURN_PROTOCOL` to `tcp` or set the command-line option `--turn_protocol=tcp` if you are unable to open the UDP listening port to the internet for the coTURN container, or if the UDP protocol is blocked or throttled in your client network.

You may also set `TURN_TLS` to `true` or set `--turn_tls=true` if TURN over TLS/DTLS was properly configured from the TURN server with a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS).

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

### The HTML5 web interface is slow and laggy.

It's most likely something with your network. Ensure that the latency to your TURN server from the server and the client is ideally under 50 ms. If the latency is too high, your connection may be too laggy for any remote desktop application. Moreover, please try to use a wired connection over a wireless connection. Also note that a higher framerate will improve performance if you have the sufficient bandwidth. This is because one screen refresh from a 60 fps screen takes 16.67 ms at a time, while one screen refresh from a 15 fps screen inevitably takes 66.67 ms, and therefore inherently causes a visible lag. Also, note that if you saturate your CPU or GPU with an application on the host, the remote desktop interface will also substantially slow down as it cannot use the CPU or GPU enough to encode the screen.

However, it might be that the parameters for the encoders, WebRTC, RTSP, or other [GStreamer](https://gstreamer.freedesktop.org) plugins are not optimized enough. If you find that it is the case, we always welcome contributions. If your changes show noticeably better results in the same conditions, please make a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls), or tell us about the parameters in any channel that we can reach so that we can also test.

### The HTML5 web interface loads and the signalling connection works, but the WebRTC connection fails and the remote desktop does not start.

Please read [Using a TURN server](#using-a-turn-server).

### I want to pass multiple screens within a server to another client using the WebRTC HTML5 web interface.

You can start a new instance of `selkies-gstreamer` by changing the `DISPLAY` environment variable and setting a different web interface port in a different terminal to pass a different screen simultaneously to your current screen.

### I want to test a shared secret TURN server by manually generating a TURN credential from a shared secret.

This step is required when you want to test your TURN server configured with a shared secret instead of the legacy username/password authentication.

1. Run the test container:

```bash
docker-compose run --service-ports test
```

2. From inside the test container, source `gst-env` and call the `generate_rtc_config` method.

```bash
export GSTREAMER_PATH=/opt/gstreamer
source /opt/gstreamer/gst-env

export TURN_HOST="Your TURN Host"
export TURN_PORT="Your TURN Port"
export TURN_SECRET="Your Shared Secret"
export TURN_USER="user"

python3 -c 'import os;from selkies_gstreamer.signalling_web import generate_rtc_config; print(generate_rtc_config(os.environ["TURN_HOST"], os.environ["TURN_PORT"], os.environ["TURN_SECRET"], os.environ["TURN_USER"]))'
```

> You can then test your TURN server configuration from the [Trickle ICE](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/) webpage.
