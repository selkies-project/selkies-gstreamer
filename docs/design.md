**If you simply want to get this project running and do not like reading long text, head to [Getting Started](start.md).**

## What is Selkies-GStreamer?

Have you ever wondered why Windows has Parsec, and Linux does not? Have you ever wanted to obtain full frame on interactive 3D OpenGL/Vulkan/Wine-Direct3D applications or Linux/Wine video games, without relying on proprietary installers or seated server licenses, from the convenience of your web browser that you enjoyed from noVNC or Apache Guacamole? Do you have a web server, reverse proxy, or load balancer in your infrastructure that a web application deployment must pass through?

Have you ever wondered if Parsec, Moonlight + Sunshine, or Steam Remote Play could be exposed over an HTML5 web browser interface without the need to open as many ports? Or ever wondered how GeForce Now or Xbox Cloud Gaming delivered fluid streams in Google Chrome with WebRTC?

None of these capabilities have to be behind proprietary walls, the community can build one!

**Moonlight, Google Stadia, or GeForce NOW in noVNC form factor for Linux X11, in any HTML5 web interface you wish to embed inside, with at least 60 frames per second on Full HD resolution.**

Selkies-GStreamer is an open-source low-latency high-performance Linux-native GPU/CPU-accelerated WebRTC HTML5 remote desktop streaming platform, for self-hosting, containers, Kubernetes, or Cloud/HPC platforms, [started out first by Google engineers](https://web.archive.org/web/20210310083658/https://cloud.google.com/solutions/gpu-accelerated-streaming-using-webrtc), then expanded by academic researchers.

Selkies-GStreamer is designed for researchers, including people in the graphical AI/robotics/autonomous driving/drug discovery fields, SLURM supercomputer/HPC system administrators, Jupyter/Kubernetes/Docker®/Coder infrastructure administrators, and Linux cloud gaming enthusiasts.

While designed for clustered or unprivileged containerized environments, Selkies-GStreamer can also be deployed in desktop computers, and any performance or quality issue that would be problematic with cloud gaming platforms is also considered a bug.

## Motivation

The Linux operating system (OS) has now become more than a server or enthusiast operating system. It has become the operating system of choice for artificial intelligence (AI), machine learning (ML), and deep learning, together with the cloud computing paradigm. In this era, artificial intelligence, especially including large deep learning models, has rewarded massive scale from clustered computing and supercomputers.

The first step of a user working in a clustered computing environment always tends to be some type of gateway. Many use SSH into a login node, and others can use a web frontend interface such as Jupyter to start and manage their workload. But one sector The Linux operating system landscape lacked a proper successor to VNC. VNC allowed GUI applications from clustered environments to be directly from such clusters.

However, because RFB, the protocol for VNC, is based on a 30-year-old protocol, several pitfalls exist, like the Tight encoding format, combining "rectangle, palette and gradient filling with zlib and JPEG" being adequate for partial screen refresh, but not fullscreen refresh and 3D graphics. Several alternative solutions exist for Linux that support video codecs including H.264, and even software encoding on video delivers better performance and efficiency with recent hardware.

Although, such solutions are currently primarily proprietary, requiring license servers and license seats integrated into the infrastructure, and having major issues integrating into reproducible environments such as virtual machine snapshots or containers. Due to using closed-source installer packages for these proprietary solutions, the flexibility to deploy on various niche environments, such as for embedded devices or exotic CPU architectures, also suffers. Other open-source solutions available such as RustDesk are meant for TeamViewer-like remote user support, not for large-scale client-server deployments in the cloud or in clusters.

## Design

Selkies-GStreamer streams a Linux X11 desktop or Docker®/Kubernetes container to a recent web browser using WebRTC with GPU hardware or CPU software acceleration from the server and the client. Linux Wayland, Mac, and Windows support is planned, but community contribution will always accelerate new features.

This project is adequate as a high-performance replacement to most Linux remote desktop solutions, especially VNC, delivering 60 frames per second at 1080p resolution with software encoding on 150% CPU consumption or better on an NVIDIA or Intel/AMD GPU. Selkies-GStreamer, overall, achieves comparable performance to proprietary remote desktop platforms and surpasses those of similar open-source applications by incorporating GPU-accelerated screen encoding and latency-eliminating techniques utilized in web-based WebRTC game streaming platforms.

You may create a self-hosted version of your favorite cloud gaming platform, running on a Linux host with a web-based client from any operating system. Wine and Proton allow your `.exe` Windows application, as well as Windows games, to run with Linux, without the complicated Windows licensing.

There are several strengths of Selkies-GStreamer compared to other game streaming or remote desktop platforms.

**First, Selkies-GStreamer is much more flexible to be used across various types of environments compared to other services or projects.**

Its focus on a single web interface instead of multiple native client implementations allow any operating system with a recent web browser to work as a client.

Either the built-in HTTP basic authentication feature of Selkies-GStreamer or any HTTP web server/reverse proxy may provide protection to the web interface.

Compared to many remote desktop or game streaming applications requiring multiple ports open to stream your desktop across the internet, Selkies-GStreamer only requires one HTTP web server or reverse proxy which supports WebSocket, or a single TCP port from the server. This allows many existing infrastructure previously utilizing noVNC to switch to Selkies-GStreamer without changing other components of the infrastructure.

A dedicated TURN server for actual traffic relaying can be flexibly configured within any location at or between the server and the client.

**Second, Selkies-GStreamer can utilize H.264 hardware acceleration of GPUs, as well as falling back to software acceleration with the H.264, H.265, VP8, VP9, and AV1 codecs.**

Audio streaming from the server is supported using the Opus codec. Check the [GStreamer Components](component.md#gstreamer-components) section for current codec and interface support.

WebRTC ensures minimum latency from the server to the HTML5 web client interface. Any other video encoder, video converter, screen capturing interface, or protocol may be contributed from the community easily. NVIDIA GPUs are currently fully supported with NVENC, and Intel and AMD GPUs supported with VA-API, with progress on supporting other GPU hardware.

**Third, Selkies-GStreamer was designed not only for desktops and bare metal servers, but also for unprivileged Docker® and Kubernetes containers.**

Unlike other similar Linux solutions, there are no dependencies that require access to special devices not available inside containers by default, and is also not dependent on `systemd`.

This enables virtual desktop infrastructure (VDI) using containers instead of virtual machines (VMs) which tend to have high overhead.

Root permissions are also not required at all, and all components can be installed completely to the userspace in a portable way. This indicates that no administrator intervention is typically required for a user to deploy Selkies-GStreamer in any shared infrastructure.

**Fourth, Selkies-GStreamer is modularized, easy to use, and expand to various usage cases, attracting users and developers from diverse backgrounds, as it uses [GStreamer](https://gstreamer.freedesktop.org).**

GStreamer allows pluggable components to be mixed and matched like LEGO blocks to form arbitrary pipelines, providing an easier interface with more comprehensive documentation compared to [FFmpeg](https://ffmpeg.org).

The remote desktop code components are abstracted behind GStreamer to achieve highly readable and understandable code, enabling developers and researchers to customize to their own needs, as long as the MPL-2.0 license terms are met. More complicated mechanisms are veiled behind GStreamer and are battle-tested from users and developers worldwide.

Therefore, Selkies-GStreamer is meant from the start to be a community-built project, where developers from all backgrounds can easily contribute to or expand upon.

Selkies-GStreamer mainly uses [`GStreamer-Python`](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/tree/main/subprojects/gst-python), the [Python](https://www.python.org) bindings for GStreamer, [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html), which provides the ability to send a WebRTC remote desktop stream to web browsers from GStreamer, and many more community plugins provided by GStreamer.

**Head to [Getting Started](start.md) to deploy your own instance.**
