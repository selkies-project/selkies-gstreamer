# Getting Started

## Quick Start

**Choose between this section and [Advanced Install](#advanced-install) if you need to self-host on a standalone instance or use with HPC clusters. This section is recommended for starters.**

This **Quick Start** uses a portable tarball distribution with most (but not all) dependencies included and supported with **any Linux distribution with `glibc ≥ 2.17`** (CentOS 7 or newer) to deploy Selkies-GStreamer.

Read [Conda Toolchain](component.md#conda-toolchain) for more details of this step and procedures for installing from the latest commit in the `main` branch.

**1. Install required dependencies, for Ubuntu or Debian-based distributions, run this command:**

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq tar gzip ca-certificates curl libpulse0 wayland-protocols libwayland-dev libwayland-egl1 x11-utils x11-xkb-utils x11-xserver-utils xserver-xorg-core libx11-xcb1 libxcb-dri3-0 libxkbcommon0 libxdamage1 libxfixes3 libxv1 libxtst6 libxext6 xvfb
```

In the future, this host dependency requirement may be completely eliminated if relevant [conda-forge](https://conda-forge.org) feedstocks are available.

**2. Download and unpack the latest stable release of the Selkies-GStreamer portable distribution inside a directory of your choice:**

```bash
export SELKIES_VERSION="$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g')"
cd ~ && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-portable-v${SELKIES_VERSION}_amd64.tar.gz" | tar -xzf -
```

**3. Set your `DISPLAY` and `PULSE_SERVER` environment variables for the X.Org X11 display server or PulseAudio audio server.**

**Check that you are using X.Org instead of Wayland (which is the default in many distributions but not supported) when using an existing display. You also need to be logged in from the login screen or autologin should be enabled.**

Set `DISPLAY` to an unoccupied display server ID (such as `:99`) if you want Selkies-GStreamer to start its own virtual X11 display server (defaults to `:0`), and keep environment variables `PULSE_RUNTIME_PATH` and `PULSE_SERVER` empty if you want Selkies-GStreamer to start a portable PulseAudio audio server.

**The environment variables that are set here should also be set with the host application or desktop environment, else you will likely not have audio or be shown an error.**

```bash
export DISPLAY="${DISPLAY:-:0}"
export PIPEWIRE_LATENCY="128/48000"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
export PIPEWIRE_RUNTIME_DIR="${PIPEWIRE_RUNTIME_DIR:-${XDG_RUNTIME_DIR:-/tmp}}"
export PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}"
export PULSE_SERVER="${PULSE_SERVER:-unix:${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}/native}"
```

**4. Run Selkies-GStreamer** (change `--encoder=` to another value such as `nvh264enc`, `vah264enc`, `vp9enc`, or `vp8enc`, if you want to [use different codecs or GPU acceleration](component.md#encoders))**:**

```bash
./selkies-gstreamer/selkies-gstreamer-run --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=mypasswd --encoder=x264enc --enable_resize=false
```

The default username (set with `--basic_auth_user=` or `SELKIES_BASIC_AUTH_USER`), when not specified, is the current user environment variable `$USER` (empty username if nonexistent), and the default password (set with `--basic_auth_password=` or `SELKIES_BASIC_AUTH_PASSWORD`), when not specified, is `mypasswd`.

Use `--enable_resize=true` if you want to fit the remove resolution to the client window and skip the next section. You **must NOT** enable this option when streaming a physical monitor.

**5. Resize to your intended resolution (DO NOT resize when streaming a physical monitor):**

```bash
./selkies-gstreamer/selkies-gstreamer-resize-run 1920x1080
```

**6. Check the [**Joystick Interposer**](component.md#joystick-interposer) section if you need to use joystick/gamepad devices from your web browser client.**

You can replace `/usr/$LIB/selkies_joystick_interposer.so` with any non-root path of your choice if using the `.tar.gz` tarball.

**7. (MANDATORY) If the HTML5 web interface loads and the signaling connection works, but the WebRTC connection fails or the remote desktop does not start:**

**Depending on your environment, this step may be mandatory. Moreover, when there is a very high latency or stutter, and the TURN server is shown as `staticauth.openrelay.metered.ca` with a `relay` connection, this section is very important.**

Please read [**WebRTC and Firewall Issues**](firewall.md).

**8. Read [**Troubleshooting and FAQs**](usage.md#troubleshooting-and-faqs) if something is not as intended and [**Usage**](usage.md#usage) for more information on customizing.**

## Desktop Container

Full desktop containers that can be used out-of-the-box are available in separate repositories. If you can deploy Docker® or Podman containers, this is the easiest way to get started.

[`docker-nvidia-glx-desktop`](https://github.com/selkies-project/docker-nvidia-glx-desktop) and [`docker-nvidia-egl-desktop`](https://github.com/selkies-project/docker-nvidia-egl-desktop) are expandable ready-to-go out-of-the-box containerized remote desktop implementations of Selkies-GStreamer supporting hardware acceleration on NVIDIA and other GPUs.

The [`selkies-vdi`](https://github.com/selkies-project/selkies-vdi) or [`selkies-examples`](https://github.com/selkies-project/selkies-examples) repositories from the [Selkies Project](https://github.com/selkies-project) provide containerized virtual desktop infrastructure (VDI) templates, but are outdated. Contributions to sync the projects with the current release are welcome.

## Minimal Container

The [Example Container](/addons/example) is the reference minimal-functionality container developers can base upon, or test Selkies-GStreamer quickly. The bare minimum Xfce4 desktop environment is installed together with Firefox, as well as an embedded TURN server inside the container for quick WebRTC firewall traversal.

Instructions are available in the [Example Container](component.md#example-container) section.

**(MANDATORY) Follow the instructions from [WebRTC and Firewall Issues](firewall.md) in order to make the container or self-hosted standalone instance using an external TURN server.**

A TURN server is required if trying to use this project inside a Docker® or Kubernetes container without `--network=host`, or in other cases where the HTML5 web interface loads but the connection fails. This is required for all WebRTC applications, especially since Selkies-GStreamer is self-hosted, unlike other proprietary services which provide a TURN server for you.

## Advanced Install 

**Choose between [Quick Start](#quick-start) and this section.**

This distribution is slightly more complicated to deploy, yet is the recommended `Dockerfile` build procedure. The below installation procedures allow using Ubuntu packages as dependencies for Selkies-GStreamer.

### Backgrounds

Selkies-GStreamer has a highly modularized architecture, composed of multiple components.

Three mandatory components are required to run Selkies-GStreamer: the [standalone or distribution-provided build of GStreamer](/addons/gstreamer) with the most recent version (currently ≥ 1.22), the [Python component wheel package](/src/selkies_gstreamer) including the signaling server, and the [HTML5 web interface components](/addons/gst-web). Currently, Ubuntu 24.04 (Mint 22), 22.04 (Mint 21), 20.04 (Mint 20) are supported, but other operating systems should also work if using your own GStreamer build of the newest version (contributions for build workflows of more operating systems are welcome).

All three of the components are built and packaged every [Release](https://github.com/selkies-project/selkies-gstreamer/releases). In addition, every latest commit gets built and is made available in container forms [`ghcr.io/selkies-project/selkies-gstreamer/gstreamer`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgstreamer), [`ghcr.io/selkies-project/selkies-gstreamer/py-build`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fpy-build), and [`ghcr.io/selkies-project/selkies-gstreamer/gst-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fgst-web).

For more information, check the [Components](component.md#components) section.

The [All-In-One Desktop Containers](#desktop-container) support unprivileged self-hosted Kubernetes clusters and Docker®/Podman.

Example Google Compute Engine/Google Kubernetes Engine deployment configurations of all components are available in the [`infra/gce`](/infra/gce) and [`infra/gke`](/infra/gke) directories, but may be deprecated in favor of vendor-agnostic Kubernetes configurations.

### Install the packaged version on self-hosted standalone machines, cloud instances, or virtual machines

**NOTE: You will need to use an external STUN/TURN server capable of `srflx` or `relay` type ICE connections if both your server and client have ports closed or are under a restrictive firewall. Either open the UDP and TCP port ranges 49152-65535 of your server, or follow the instructions from [WebRTC and Firewall Issues](firewall.md) to make the container work using an external TURN server.**

While this instruction assumes that you are installing this project systemwide, it is possible to install and run all components completely within the userspace. Dependencies may also be installed without root permissions if you use the [**Quick Start**](#quick-start) procedures.

**1. Install the dependencies, for Ubuntu or Debian-based distributions, run this command:**

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y jq tar gzip ca-certificates curl build-essential python3-pip python3-dev python3-gi python3-setuptools python3-wheel libgcrypt20 libgirepository-1.0-1 glib-networking libglib2.0-0 libgudev-1.0-0 alsa-utils jackd2 libjack-jackd2-0 libpulse0 libopus0 libvpx-dev x264 x265 libdrm2 libegl1 libgl1 libopengl0 libgles1 libgles2 libglvnd0 libglx0 wayland-protocols libwayland-dev libwayland-egl1 wmctrl xsel xdotool x11-utils x11-xkb-utils x11-xserver-utils xserver-xorg-core libx11-xcb1 libxcb-dri3-0 libxdamage1 libxfixes3 libxv1 libxtst6 libxext6
```

Install additional dependencies if using Ubuntu ≥ 22.04 (Mint 21) or a higher equivalent version of another operating system:

```bash
sudo apt-get update && sudo apt-get install --no-install-recommends -y xcvt libopenh264-dev svt-av1 aom-tools
```

If using supported NVIDIA GPUs, install NVENC (bundled with the GPU driver) and NVRTC (bundled with pre-built GStreamer component, check the [GStreamer Dockerfile](/addons/gstreamer/Dockerfile) for manual installation instructions).

If using AMD or Intel GPUs, install its graphics and VA-API drivers, as well as `libva2`. The bundled VA-API driver in the AMDGPU Pro graphics driver is recommended for AMD GPUs and the `i965-va-driver-shaders` or `intel-media-va-driver-non-free` packages are recommended depending on your Intel GPU generation. Optionally install `vainfo`, `intel-gpu-tools`, `radeontop`, or `nvtop` for GPU monitoring.

Use the following commands to retrieve the latest `SELKIES_VERSION` release, the current Ubuntu `DISTRIB_RELEASE`, and the current architecture `ARCH` in the following steps:

```bash
export SELKIES_VERSION="$(curl -fsSL "https://api.github.com/repos/selkies-project/selkies-gstreamer/releases/latest" | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g')"
export DISTRIB_RELEASE="$(grep VERSION_ID= /etc/os-release | cut -d= -f2 | tr -d '\"')"
export ARCH="$(dpkg --print-architecture)"
```

**2. Unpack the GStreamer components of Selkies-GStreamer** (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`), using your own GStreamer build on any architecture can work **as long as it is the most recent stable version with the required plugins included:**

Read [GStreamer](component.md#gstreamer) for more details of this step and procedures for installing from the latest commit in the `main` branch.

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/gstreamer-selkies_gpl_v${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_amd64.tar.gz" | sudo tar -xzf -
```

This will install the GStreamer components to the default directory of `/opt/gstreamer`. If you are unpacking to a different directory, make sure to set the the environment variable `GSTREAMER_PATH` to the directory. GStreamer builds for `aarch64` are not provided but can be built following procedures in the [GStreamer Dockerfile](/addons/gstreamer/Dockerfile) or [Conda Dockerfile](/addons/conda/Dockerfile).

**3. Install the Selkies-GStreamer Python components** (this component is pure Python and any operating system is compatible, fill in `SELKIES_VERSION`)**:**

Read [Python Application](component.md#python-application) for more details of this step and procedures for installing from the latest commit in the `main` branch.

```bash
cd /tmp && curl -O -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --no-cache-dir --force-reinstall "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl" && rm -f "selkies_gstreamer-${SELKIES_VERSION}-py3-none-any.whl"
```

**4. Unpack the Selkies-GStreamer HTML5 components:**

Read [Web Application](component.md#web-application) for more details of this step and procedures for installing from the latest commit in the `main` branch.

```bash
cd /opt && curl -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-gstreamer-web_v${SELKIES_VERSION}.tar.gz" | sudo tar -xzf -
```

This will install the HTML5 components to the default directory of `/opt/gst-web`. If you are unpacking to a different directory, make sure to set the directory to the environment variable `SELKIES_WEB_ROOT` or add the command-line option `--web_root=` to Selkies-GStreamer. Note that you should change `manifest.json` and `cacheName` in `sw.js` to rebrand the web interface to a different name.

**5. Install the Joystick Interposer to process gamepad input**, if you need to use joystick/gamepad devices from your web browser client (fill in `SELKIES_VERSION`, `DISTRIB_RELEASE`, and `ARCH` of either `amd64` for `x86_64`, and `arm64` for `aarch64`)**:**

Read [Joystick Interposer](component.md#joystick-interposer) for more details of this step and procedures for installing from the latest commit in the `main` branch.

```bash
cd /tmp && curl -o selkies-js-interposer.deb -fsSL "https://github.com/selkies-project/selkies-gstreamer/releases/download/v${SELKIES_VERSION}/selkies-js-interposer_v${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_${ARCH}.deb" && sudo apt-get update && sudo apt-get install --no-install-recommends -y ./selkies-js-interposer.deb && rm -f selkies-js-interposer.deb
```

Alternatively, users may directly place the Joystick Interposer libraries from the `selkies-js-interposer_v${SELKIES_VERSION}_ubuntu${DISTRIB_RELEASE}_${ARCH}.tar.gz` tarball into the library path, for instance into `/usr/lib/i386-linux-gnu` and `/usr/lib/i386-linux-gnu`. More information can be found in [Joystick Interposer](component.md#joystick-interposer).

You can replace `/usr/$LIB/selkies_joystick_interposer.so` with any non-root path of your choice if using the `.tar.gz` tarball.

**6. Run Selkies-GStreamer after changing the below script appropriately** (install `xvfb` and uncomment relevant sections if there is no real display, **DO NOT resize when streaming a physical monitor**)**:**

**Check that you are using X.Org instead of Wayland (which is the default in many distributions but not supported) when using an existing display. You also need to be logged in from the login screen or autologin should be enabled.**

```bash
export DISPLAY="${DISPLAY:-:0}"
# Configure the Joystick Interposer
export SELKIES_INTERPOSER='/usr/$LIB/selkies_joystick_interposer.so'
export LD_PRELOAD="${SELKIES_INTERPOSER}${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
sudo mkdir -pm1777 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3
sudo chmod 777 /dev/input/js*

# Commented sections are optional but may be mandatory based on setup

# Start a virtual X11 server if not already running, skip this line if an X server already exists or you are already using a display
# Xvfb "${DISPLAY}" -screen 0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -ac -noreset -shmem >/tmp/Xvfb_selkies.log 2>&1 &

# Wait for X server to start
# echo 'Waiting for X Socket' && until [ -S "/tmp/.X11-unix/X${DISPLAY#*:}" ]; do sleep 0.5; done && echo 'X Server is ready'

# Choose one between PulseAudio and PipeWire if not already running, either one must be installed

# Initialize PulseAudio (set PULSE_SERVER to unix:/run/pulse/native if your user is in the pulse-access group and pulseaudio is triggered with sudo/root), omit the below lines if a PulseAudio server is already running
# export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}/native}"
# /usr/bin/pulseaudio -k >/dev/null 2>&1 || true
# /usr/bin/pulseaudio --verbose --log-target=file:/tmp/pulseaudio_selkies.log --disallow-exit &

# Initialize PipeWire
# export PIPEWIRE_LATENCY="128/48000"
# export DISABLE_RTKIT="y"
# export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
# export PIPEWIRE_RUNTIME_DIR="${PIPEWIRE_RUNTIME_DIR:-${XDG_RUNTIME_DIR:-/tmp}}"
# export PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}"
# export PULSE_SERVER="${PULSE_SERVER:-unix:${PULSE_RUNTIME_PATH:-${XDG_RUNTIME_DIR:-/tmp}/pulse}/native}"
# pipewire &
# wireplumber &
# pipewire-pulse &

# Replace this line with your desktop environment session or skip this line if already running, use VirtualGL `vglrun +wm xfce4-session` here if needed
# [ "${START_XFCE4:-true}" = "true" ] && rm -rf ~/.config/xfce4 && xfce4-session &

# Initialize the GStreamer environment after setting GSTREAMER_PATH to the path of your GStreamer directory
export GST_DEBUG="*:2"
export GSTREAMER_PATH=/opt/gstreamer
. /opt/gstreamer/gst-env
# Replace with your wanted resolution if using without resize, DO NOT USE if there is a physical display
# selkies-gstreamer-resize 1920x1080

# Starts the remote desktop process
# Change `--encoder=` to `nvh264enc`, `vah264enc`, `vp9enc`, or `vp8enc` for different video codecs or hardware encoders
# DO NOT set `--enable_resize=true` if there is a physical display
selkies-gstreamer --addr=0.0.0.0 --port=8080 --enable_https=false --https_cert=/etc/ssl/certs/ssl-cert-snakeoil.pem --https_key=/etc/ssl/private/ssl-cert-snakeoil.key --basic_auth_user=user --basic_auth_password=mypasswd --encoder=x264enc --enable_resize=false &
```

The default username (set with `--basic_auth_user=` or `SELKIES_BASIC_AUTH_USER`), when not specified, is the current user environment variable `$USER` (empty username if nonexistent), and the default password (set with `--basic_auth_password=` or `SELKIES_BASIC_AUTH_PASSWORD`), when not specified, is `mypasswd`.

**7. (MANDATORY) If the HTML5 web interface loads and the signaling connection works, but the WebRTC connection fails or the remote desktop does not start:**

**Depending on your environment, this step may be mandatory. Moreover, when there is a very high latency or stutter, and the TURN server is shown as `staticauth.openrelay.metered.ca` with a `relay` connection, this section is very important.**

Please read [**WebRTC and Firewall Issues**](firewall.md).

**8. Read [**Troubleshooting and FAQs**](usage.md#troubleshooting-and-faqs) if something is not as intended and [**Usage**](usage.md#usage) for more information on customizing.**

### Install the latest build on self-hosted standalone machines, cloud instances, or virtual machines

**Build artifacts for every `main` branch commit are available as an after logging into GitHub in [Actions](https://github.com/selkies-project/selkies-gstreamer/actions), and you do not need Docker® to download them.**

Otherwise, Docker®/Podman (or any equivalent) may be used if you want to use builds from the latest commit. Refer to [Components](component.md) for more information.

This method can be also used when building a new container image with the `FROM [--platform=<platform>] <image> [AS <name>]` and `COPY [--from=<name>] <src_path> <dest_path>` instruction instead of using the `docker` CLI. Change `main` to `latest` if you want the latest release version instead of the latest development version.
