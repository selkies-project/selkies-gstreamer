# Components

## GStreamer Components

Below are GStreamer components which are implemented and therefore used with Selkies-GStreamer. Some include environment variables or command-line options which may be used select one type of component, and others are chosen automatically based on the operating system or configuration. This section is to be continuously updated.

### Encoders

This table specifies the currently implemented video encoders and their corresponding codecs, which may be set using the environment variable `SELKIES_ENCODER` or the command-line option `--encoder`.

**Encoders marked as "Recommended": Tested on Chromium where the encoder adds no perceptible delay or frame drops from the host encoder even with a high (> 16 mbps) bitrate with an actively moving screen.** Note that broadband internet through 5 GHz Wi-Fi or wired ethernet is highly recommended.

**As Selkies-GStreamer uses new GStreamer components from the latest stable GStreamer versions, GStreamer ≥ 1.22 is the current strict requirement. No support will be provided for older versions, but you can build your own version in older distributions or use the portable Conda distribution.**

| Plugin (set `SELKIES_ENCODER` to) | Codec | Acceleration | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`nvh264enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvh264enc.html) | H.264 AVC | NVIDIA GPU | All | All Major | NVRTC, `libnvidia-encode` | **Recommended**, [Requires NVENC - Encoding H.264 (AVCHD)](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) |
| [`vah264enc`](https://gstreamer.freedesktop.org/documentation/va/vah264enc.html) | H.264 AVC | AMD, Intel GPU | All | All Major | VA-API Driver, `libva` | Requires supported GPU |
| [`x264enc`](https://gstreamer.freedesktop.org/documentation/x264/index.html) | H.264 AVC | Software | All | All Major | `x264` | **Recommended** |
| [`openh264enc`](https://gstreamer.freedesktop.org/documentation/openh264/openh264enc.html) | H.264 AVC | Software | All | All Major | `openh264` | N/A |
| [`nvh265enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvh265enc.html) | H.265 HEVC | NVIDIA GPU | All | Safari ≥ 17.9 | NVRTC, `libnvidia-encode` | [Requires NVENC - Encoding H.265 (HEVC)](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) |
| [`vah265enc`](https://gstreamer.freedesktop.org/documentation/va/vah265enc.html) | H.265 HEVC | AMD, Intel GPU | All | Safari ≥ 17.9 | VA-API Driver, `libva` | Unstable, Requires supported GPU |
| [`x265enc`](https://gstreamer.freedesktop.org/documentation/x265/index.html) | H.265 HEVC | Software | All | Safari ≥ 17.9 | `x265` | Unstable |
| [`vp8enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp8enc.html) | VP8 | Software | All | All Major | `libvpx` | **Recommended under 2K resolution but not with constrained network** |
| [`vavp9enc`](https://gstreamer.freedesktop.org/documentation/va/vavp9enc.html) | VP9 | AMD, Intel GPU | All | All Major | VA-API Driver, `libva` | Unstable, Requires supported GPU and GStreamer ≥ 1.25 |
| [`vp9enc`](https://gstreamer.freedesktop.org/documentation/vpx/vp9enc.html) | VP9 | Software | All | All Major | `libvpx` | **Recommended but not with constrained network** |
| [`nvav1enc`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvav1enc.html) | AV1 | NVIDIA GPU | All | Chromium-based, Safari | NVRTC, `libnvidia-encode`, [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Unstable, [Requires NVENC - Encoding AV1](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new) and GStreamer ≥ 1.25 |
| [`vaav1enc`](https://gstreamer.freedesktop.org/documentation/va/vaav1enc.html) | AV1 | AMD, Intel GPU | All | Chromium-based, Safari | VA-API Driver, `libva`, [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Unstable, Requires supported GPU and GStreamer ≥ 1.24 |
| [`svtav1enc`](https://gstreamer.freedesktop.org/documentation/svtav1/svtav1enc.html) | AV1 | Software | All | Chromium-based, Safari | `svt-av1` ≥ 1.1, [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | NOT WORKING, Conda or Ubuntu ≥ 24.04 |
| [`av1enc`](https://gstreamer.freedesktop.org/documentation/aom/av1enc.html) | AV1 | Software | All | Chromium-based, Safari | `aom`, [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Unstable, Conda or Ubuntu ≥ 22.04 |
| [`rav1enc`](https://gstreamer.freedesktop.org/documentation/rav1e/index.html) | AV1 | Software | All | Chromium-based, Safari | [`gst-plugins-rs`](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs) | Unstable |

### Video Color Converters

This table specifies the currently implemented video frame converters used to convert the YUV formats from `BGRx` to `I420` or `NV12`, which are automatically decided based on the encoder types.

| Plugin | Encoders | Acceleration | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`cudaconvert`](https://gstreamer.freedesktop.org/documentation/nvcodec/cudaconvert.html) | `nvh264enc`, `nvh265enc`, `nvav1enc` | NVIDIA GPU | All | NVRTC | N/A |
| [`vapostproc`](https://gstreamer.freedesktop.org/documentation/va/vapostproc.html) | `vah264enc`, `vah265enc`, `vavp9enc`, `vaav1enc` | AMD, Intel GPU | All | VA-API Driver, `libva` | N/A |
| [`videoconvert`](https://gstreamer.freedesktop.org/documentation/videoconvertscale/videoconvert.html) | `x264enc`, `openh264enc`, `x265enc`, `vp8enc`, `vp9enc`, `svtav1enc`, `av1enc`, `rav1enc` | Software | All | N/A | N/A |

### Display Capture Interfaces

This table specifies the currently supported display interfaces and how each plugin selects each video device.

| Plugin | Device Selector | Display Interfaces | Input Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|---|
| [`ximagesrc`](https://gstreamer.freedesktop.org/documentation/ximagesrc/index.html) | `DISPLAY` environment | X.Org / X11 | [`Xlib`](https://github.com/python-xlib/python-xlib) w/ [`pynput`](https://github.com/moses-palmer/pynput) | Linux | Various | N/A |

### Audio Encoders

This table specifies the currently implemented audio encoders and their corresponding codecs. Opus is currently the only adequate fullband audio media codec supported in web browsers by specification.

| Plugin | Codec | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`opusenc`](https://gstreamer.freedesktop.org/documentation/opus/opusenc.html) | Opus | All | All Major | `libopus` | N/A |

### Audio Capture Interfaces

This table specifies the currently supported audio interfaces and how each plugin selects each audio device.

| Plugin | Device Selector | Audio Interfaces | Operating Systems | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`pulsesrc`](https://gstreamer.freedesktop.org/documentation/pulseaudio/pulsesrc.html) | `PULSE_SERVER` environment | PulseAudio or PipeWire-Pulse | Linux | `libpulse` | N/A |

### Stream Transport Protocols

This table specifies the currently supported transport protocol components.

| Plugin | Protocols | Operating Systems | Browsers | Main Dependencies | Notes |
|---|---|---|---|---|---|
| [`webrtcbin`](https://gstreamer.freedesktop.org/documentation/webrtc/index.html) | [WebRTC](https://webrtc.org) | All | All Major | Various | N/A |
