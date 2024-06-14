# Getting Started

## Container Start

If you can deploy Docker® or Podman containers, this is the easiest way to get started.

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container, or in other cases where the HTML5 web interface loads but the connection fails. This is required for all WebRTC applications, especially since Selkies-GStreamer is self-hosted, unlike other proprietary services which provide a TURN server for you. Follow the instructions from [WebRTC and Firewalls](firewall.md) in order to make the container work using an external TURN server.**

### Example Docker container

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if you use this in a container WITHOUT host networking (add `--network=host` to the Docker command to enable host networking and work around this requirement if your server is not behind NAT). Follow the instructions from [Using a TURN server](firewall.md) in order to make the container work using an external TURN server.**

An example image [`ghcr.io/selkies-project/selkies-gstreamer/gst-py-example`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-py-example) from the base [example Dockerfile](/example/Dockerfile) is available.

Run the Docker container built from the [`Example Dockerfile`](/example/Dockerfile), then connect to port **8080** of your Docker host to access the web interface (Username: **`ubuntu`**, Password: **`password`**, **change `DISTRIB_RELEASE` to `24.04`, `22.04`, or `20.04`, and replace `main` to `latest` for the release build instead of the development build if needed**):

```bash
docker run --pull=always --name selkies -it -d --rm -p 8080:8080 -p 3478:3478 ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:main-ubuntu${DISTRIB_RELEASE}
```

Repositories [`selkies-vdi`](https://github.com/selkies-project/selkies-vdi) or [`selkies-examples`](https://github.com/selkies-project/selkies-examples) from the [Selkies Project](https://github.com/selkies-project) provide containerized virtual desktop infrastructure (VDI) templates.

[`docker-nvidia-glx-desktop`](https://github.com/selkies-project/docker-nvidia-glx-desktop) and [`docker-nvidia-egl-desktop`](https://github.com/selkies-project/docker-nvidia-egl-desktop) are expandable ready-to-go zero-configuration batteries-included containerized remote desktop implementations of Selkies-GStreamer supporting hardware acceleration on NVIDIA and other GPUs.

## Quick Start

**Choose between this section and [Advanced Install](#advanced-install) if you need to self-host on a standalone instance or use on HPC clusters. This section is recommended for starters.**

### Portable Distribution

(ADDME)

## Advanced Install 

**Choose between [Quick Start](#quick-start) and this section.**

This distribution is slightly more complicated to deploy, yet is recommended for containers.

### Backgrounds

Selkies-GStreamer has a highly modularized architecture, and it is composed of components.

Three mandatory components are required to run Selkies-GStreamer: the [standalone or distribution-provided build of GStreamer](/addons/gstreamer) with the most recent version (currently ≥ 1.22), the [Python component wheel package](/src/selkies_gstreamer) including the signaling server, and the [HTML5 web interface components](/addons/gst-web). Currently, Ubuntu 24.04 (Mint 22), 22.04 (Mint 21), 20.04 (Mint 20) are supported, but other operating systems should also work if using your own GStreamer build of the newest version (contributions for build workflows of more operating systems are welcome).

All three of the components are built and packaged [every release](https://github.com/selkies-project/selkies-gstreamer/releases). In addition, every latest commit gets built and is made available in container forms [`ghcr.io/selkies-project/selkies-gstreamer/gstreamer`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgstreamer), [`ghcr.io/selkies-project/selkies-gstreamer/py-build`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fpy-build), and [`ghcr.io/selkies-project/selkies-gstreamer/gst-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-web).

Example Google Compute Engine/Google Kubernetes Engine deployment configurations of all components are available in the [`infra/gce`](/infra/gce) and [`infra/gke`](/infra/gke) directories. The all-in-one containers support unprivileged self-hosted Kubernetes clusters and Docker/Podman.

### Install the packaged version on a standalone machine or cloud instance

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](firewall.md) in order to make the container work using an external TURN server.**

While this instruction assumes that you are installing this project systemwide, it is possible to install and run all components completely within the userspace. Dependencies may also be installed without root permissions if you use [`conda`](https://conda.io) or other userspace package management systems. Documentation contributions for such instructions are welcome.

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq python3-pip python3-dev python3-gi python3-setuptools python3-wheel libaa1 bzip2 libgcrypt20 libcairo-gobject2 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libsoup2.4-1 libsoup-gnome2.4-1 libgirepository-1.0-1 glib-networking libglib2.0-0 libjson-glib-1.0-0 libgudev-1.0-0 alsa-utils jackd2 libjack-jackd2-0 libpulse0 libogg0 libopus0 libvorbis-dev libjpeg-turbo8 libopenjp2-7 libvpx-dev libwebp-dev x264 x265 libdrm2 libegl1 libgl1 libgles1 libglvnd0 libglx0 wayland-protocols libwayland-dev libwayland-egl1 wmctrl xsel xdotool x11-utils x11-xserver-utils xserver-xorg-core libx11-xcb1 libxcb-dri3-0 libxkbcommon0 libxdamage1 libxfixes3 libxtst6 libxext6
```

Install additional packages if using Ubuntu ≥ 22.04 (Mint 21) or a higher equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools
```

If using supported NVIDIA GPUs, install NVENC (bundled with the GPU driver) and NVRTC (part of CUDA but not the full toolkit required). If using AMD or Intel GPUs, install its graphics and VA-API drivers, as well as `libva2`. The bundled VA-API driver in the AMDGPU Pro graphics driver is recommended for AMD GPUs and the `i965-va-driver-shaders` or `intel-media-va-driver-non-free` packages are recommended depending on your Intel GPU generation. Optionally install `vainfo`, `intel-gpu-tools`, `radeontop` for GPU monitoring.

2. Unpack the GStreamer components of Selkies-GStreamer (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`), using your own GStreamer build on any architecture may work **as long as it is the most recent stable version with the required plugins included**:

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/gstreamer-selkies_gpl_${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_amd64.tar.gz" | sudo tar -xzf -
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`. GStreamer builds for ARMv8 are not provided but can be built following procedures in the [GStreamer Dockerfile](/addons/gstreamer/Dockerfile).

3. Install the Python components of Selkies-GStreamer (this component is pure Python and any operating system is compatible, fill in `SELKIES_VERSION`):

```bash
cd /tmp && curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && && sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir --force-reinstall "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
```

4. Unpack the HTML5 components of Selkies-GStreamer:

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-web_${SELKIES_VERSION}.tar.gz" | sudo tar -xzf -
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `SELKIES_WEB_ROOT` or add the command-line option `--web_root` to Selkies-GStreamer. Note that you should change `manifest.json` and `cacheName` in `sw.js` to rebrand the web interface to a different name.

5. Install the Joystick Interposer to process gamepad input (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`, and `ARCH` of either `amd64` for x86_64, and `arm64` for ARMv8):

```bash
cd /tmp && curl -o selkies-js-interposer.deb -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-js-interposer_${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_arm64.deb" && sudo apt-get update && sudo apt-get install --no-install-recommends -y ./selkies-js-interposer.deb && rm -f selkies-js-interposer.deb
```

6. Run Selkies-GStreamer after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY="${DISPLAY:-:0}"
# Configure the Joystick Interposer
export SELKIES_INTERPOSER='/usr/$LIB/selkies_joystick_interposer.so'
export LD_PRELOAD="${SELKIES_INTERPOSER}${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
sudo mkdir -pm755 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3

# Commented sections are optional based on setup

# Start a virtual X11 server, skip this line if an X server already exists or you are already using a display
# Xvfb -screen :0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -noreset -shmem >/tmp/Xvfb.log 2>&1 &

# Ensure the X server is ready
# until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done && echo 'X Server is ready'

# Choose one between PulseAudio and PipeWire

# Initialize PulseAudio (set PULSE_SERVER to unix:/run/pulse/native if your user is in the pulse-access group and pulseaudio is triggered with sudo/root), omit the below lines if a PulseAudio server is already running
# export PULSE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${XDG_RUNTIME_DIR:-/tmp}/pulse/native}"
# /usr/bin/pulseaudio -k >/dev/null 2>&1 || true
# /usr/bin/pulseaudio --verbose --log-target=file:/tmp/pulseaudio.log --disallow-exit &

# Initialize PipeWire
# export PIPEWIRE_LATENCY="32/48000"
# export DISABLE_RTKIT="y"
# export PIPEWIRE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${XDG_RUNTIME_DIR:-/tmp}/pulse/native}"
# pipewire &
# wireplumber &
# pipewire-pulse &

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
selkies-gstreamer --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=password --encoder=nvh264enc --enable_resize=false &
```

### Install the latest build on a standalone machine or cloud instance

**Build artifacts for every commit are available as an after logging into GitHub in [Actions](https://github.com/selkies-project/selkies-gstreamer/actions), and you do not need Docker to download them.**

Otherwise, Docker (or an equivalent) may be used if you are to use builds from the latest commit. Refer to the above section for more granular informations. This method can be also used when building a new container image with the `FROM [--platform=<platform>] <image> [AS <name>]` and `COPY [--from=<name>] <src_path> <dest_path>` instruction instead of using the `docker` CLI. Change `main` to `latest` if you want the latest release version instead of the latest development version.

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the TCP and UDP port ranges 49152-65535 of your server, or follow the instructions from [Using a TURN server](firewall.md) in order to make the container work using an external TURN server.**

While this instruction assumes that you are installing this project systemwide, it is possible to install and run all components completely within the userspace. Dependencies may also be installed without root permissions if you use [`conda`](https://conda.io) or other userspace package management systems. Documentation contributions for such instructions are welcome.

1. Install the dependencies, for Ubuntu or Debian-based distros run this command:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq python3-pip python3-dev python3-gi python3-setuptools python3-wheel libaa1 bzip2 libgcrypt20 libcairo-gobject2 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libsoup2.4-1 libsoup-gnome2.4-1 libgirepository-1.0-1 glib-networking libglib2.0-0 libjson-glib-1.0-0 libgudev-1.0-0 alsa-utils jackd2 libjack-jackd2-0 libpulse0 libogg0 libopus0 libvorbis-dev libjpeg-turbo8 libopenjp2-7 libvpx-dev libwebp-dev x264 x265 libdrm2 libegl1 libgl1 libgles1 libglvnd0 libglx0 wayland-protocols libwayland-dev libwayland-egl1 wmctrl xsel xdotool x11-utils x11-xserver-utils xserver-xorg-core libx11-xcb1 libxcb-dri3-0 libxkbcommon0 libxdamage1 libxfixes3 libxtst6 libxext6
```

Install additional packages if using Ubuntu ≥ 22.04 (Mint 21) or a higher equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt libopenh264-dev libde265-0 svt-av1 aom-tools
```

If using supported NVIDIA GPUs, install NVENC (bundled with the GPU driver) and NVRTC (part of CUDA but not the full toolkit required). If using AMD or Intel GPUs, install its graphics and VA-API drivers, as well as `libva2`. The bundled VA-API driver in the AMDGPU Pro graphics driver is recommended for AMD GPUs and the `i965-va-driver-shaders` or `intel-media-va-driver-non-free` packages are recommended depending on your Intel GPU generation. Optionally install `vainfo`, `intel-gpu-tools`, `radeontop` for GPU monitoring.

2. Copy the GStreamer build from the container image and move it to `/opt/gstreamer` (fill in the OS version `DISTRIB_RELEASE`):

```bash
docker create --platform="linux/amd64" --name gstreamer ghcr.io/selkies-project/selkies-gstreamer/gstreamer:main-ubuntu${DISTRIB_RELEASE}
sudo docker cp gstreamer:/opt/gstreamer /opt/gstreamer
docker rm gstreamer
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `GSTREAMER_PATH`. GStreamer builds for ARMv8 are not provided but can be built following procedures in the [GStreamer Dockerfile](/addons/gstreamer/Dockerfile).

3. Copy the Python Wheel file from the container image and install it (DO NOT change the platform in non-x86_64 architectures, install [binfmt](https://github.com/tonistiigi/binfmt) instead):

```bash
docker create --platform="linux/amd64" --name selkies-py ghcr.io/selkies-project/selkies-gstreamer/py-build:main
docker cp selkies-py:/opt/pypi/dist/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
docker rm selkies-py
sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir --force-reinstall /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
rm -f /tmp/selkies_gstreamer-0.0.0.dev0-py3-none-any.whl
```

4. Install the HTML5 components to the container image (DO NOT change the platform in non-x86_64 architectures, install [binfmt](https://github.com/tonistiigi/binfmt) instead):

```bash
docker create --platform="linux/amd64" --name gst-web ghcr.io/selkies-project/selkies-gstreamer/gst-web:main
sudo docker cp gst-web:/usr/share/nginx/html /opt/gst-web
docker rm gst-web
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `SELKIES_WEB_ROOT` or add the command-line option `--web_root` to Selkies-GStreamer. Note that you should change `manifest.json` and `cacheName` in `sw.js` to rebrand the web interface to a different name.

5. Install the Joystick Interposer to process gamepad input (fill in the OS version `DISTRIB_RELEASE` and set platform to `linux/arm64` in ARMv8):

```bash
docker create --platform="linux/amd64" --name js-interposer ghcr.io/selkies-project/selkies-gstreamer/js-interposer:main-ubuntu${DISTRIB_RELEASE}
docker cp js-interposer:/opt/selkies-js-interposer_0.0.0.deb /tmp/selkies-js-interposer.deb
docker rm js-interposer
sudo apt-get update && sudo apt-get install --no-install-recommends -y /tmp/selkies-js-interposer.deb
rm -f /tmp/selkies-js-interposer.deb
```

6. Run Selkies-GStreamer after changing the script below appropriately, install `xvfb` if you do not have a real display:

```bash
export DISPLAY="${DISPLAY:-:0}"
# Configure the Joystick Interposer
export SELKIES_INTERPOSER='/usr/$LIB/selkies_joystick_interposer.so'
export LD_PRELOAD="${SELKIES_INTERPOSER}${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
sudo mkdir -pm755 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3

# Commented sections are optional based on setup

# Start a virtual X11 server, skip this line if an X server already exists or you are already using a display
# Xvfb -screen :0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -noreset -shmem >/tmp/Xvfb.log 2>&1 &

# Ensure the X server is ready
# until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done && echo 'X Server is ready'

# Choose one between PulseAudio and PipeWire

# Initialize PulseAudio (set PULSE_SERVER to unix:/run/pulse/native if your user is in the pulse-access group and pulseaudio is triggered with sudo/root), omit the below lines if a PulseAudio server is already running
# export PULSE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${XDG_RUNTIME_DIR:-/tmp}/pulse/native}"
# /usr/bin/pulseaudio -k >/dev/null 2>&1 || true
# /usr/bin/pulseaudio --verbose --log-target=file:/tmp/pulseaudio.log --disallow-exit &

# Initialize PipeWire
# export PIPEWIRE_LATENCY="32/48000"
# export DISABLE_RTKIT="y"
# export PIPEWIRE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${XDG_RUNTIME_DIR:-/tmp}/pulse/native}"
# pipewire &
# wireplumber &
# pipewire-pulse &

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
selkies-gstreamer --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=password --encoder=nvh264enc --enable_resize=false &
```
