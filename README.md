![Selkies WebRTC](logo/horizontal-480.png)

![Build](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_all_images.yaml/badge.svg)

[![Discord](https://img.shields.io/discord/798699922223398942?logo=discord)](https://discord.gg/wDNGDeSW5F)

## What is `selkies-gstreamer`?

`selkies-gstreamer` is a [`gst-python`](https://gitlab.freedesktop.org/gstreamer/gst-python) application for streaming a Linux X11 desktop to a web browser using WebRTC.

Built on top of [`gstwebrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html?gi-language=c), this package is capable of streaming a desktop experience at 30fps 720p with the software x264 encoder or at 60+ fps at 2K with an NVIDIA GPU.

Included is a standalone build of the latest gstreamer, a signaling server, and web interface.

A [`coturn`](addons/coturn) and [`coturn-web`](addons/coturn-web) image are also included in this repo that can be used to host your own STUN/TURN infrastructure, which is required if trying it use this in a Docker container.

## How do I use it?

### Example Docker container

> NOTE: you will need to use an external STUN/TURN server capable of srflx or relay type ICE connections if you use this in a container WITHOUT host networking. An example GCP deployment of coturn is in the [`infra/gcp`](infra/gcp) directory.

Running the docker container built from the [`Dockerfile.example`](./Dockerfile.example):

```bash
docker run --name selkies --net=host ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:latest
```

> Now connect to your docker host on port `8080` to access the web interface.

### Installing on a standalone machine or cloud instance

1. Copy the gstreamer build tarball from the docker image and extract it to `/opt/gstreamer`:

```bash
docker create --name gstreamer ghcr.io/selkies-project/selkies-gstreamer/gstreamer:latest
docker cp gstreamer:/opt/selkies-gstreamer-latest.tgz /opt/selkies-gstreamer-latest.tgz
docker rm gstreamer
cd /opt && tar zxvf selkies-gstreamer-latest.tgz
```

2. Copy the python wheel from the docker image and install it:

```bash
docker create --name selkies-py ghcr.io/selkies-project/selkies-gstreamer/py-build:latest
docker cp selkies-py:/opt/pypi/dist/selkies_gstreamer_disla-1.0.0rc0-py3-none-any.whl /opt/selkies_gstreamer_disla-1.0.0rc0-py3-none-any.whl
docker rm selkies-py
python3 -m pip install /opt/selkies_gstreamer_disla-1.0.0rc0-py3-none-any.whl
```

3. Install the web interface source from the docker image:

```bash
docker create --name gst-web ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
cd /opt && docker cp gst-web:/usr/share/nginx/html ./gst-web
docker rm gst-web
```

4. Run selkies-gstreamer:

```bash
export DISPLAY=:0
export GST_DEBUG=*:2
source /opt/gstreamer/gst-env
Xvfb -screen :0 8192x4096x24 +extension RANDR +extension GLX +extension MIT-SHM -nolisten tcp -noreset -shmem 2>&1 >/tmp/Xvfb.log &
until [[ -S /tmp/.X11-unix/X0 ]]; do sleep 1; done && echo 'X Server is ready'
sudo /usr/bin/pulseaudio --system --verbose --log-target=file:/tmp/pulseaudio.log --realtime=true --disallow-exit -F /etc/pulse/system.pa &
icewm-session &
export WEBRTC_ENCODER=x264enc
export WEBRTC_ENABLE_RESIZE=\${WEBRTC_ENABLE_RESIZE:-false}
export PULSE_SERVER=127.0.0.1:4713
export JSON_CONFIG=/tmp/selkies.json
echo '{}' > \$JSON_CONFIG
selkies-gstreamer-resize 1280x720
selkies-gstreamer &
```