![Selkies WebRTC](logo/horizontal-480.png)

![Build](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_all_images.yaml/badge.svg)

## What is `selkies-gstreamer`?

`selkies-gstreamer` is a [`gst-python`](https://gitlab.freedesktop.org/gstreamer/gst-python) application for streaming a Linux X11 desktop to a web browser using WebRTC.

Built on top of [`gstwebrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html?gi-language=c), this package is capable of streaming a desktop experience at 30fps 720p with the software x264 encoder or at 60+ fps at 2K with an NVIDIA GPU.

Included is a bundled signaling server and web interface, served from the single python script entrypoint.

A [`coturn`](addons/coturn) and [`coturn-web`](addons/coturn-web) image are also included in this repo that can be used to host your own STUN/TURN infrastructure, which is required if trying it use this in a Docker container.

