# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import base64
import json
import logging

import gi
gi.require_version("Gst", "1.0")
gi.require_version('GstWebRTC', '1.0')
gi.require_version('GstSdp', '1.0')
from gi.repository import Gst
from gi.repository import GstWebRTC
from gi.repository import GstSdp

logger = logging.getLogger("gstwebrtc_app")
logger.setLevel(logging.INFO)

class GSTWebRTCAppError(Exception):
    pass


class GSTWebRTCApp:
    def __init__(self, stun_servers=None, turn_servers=None, audio=True, framerate=30, encoder=None, video_bitrate=2000, audio_bitrate=64000):
        """Initialize gstreamer webrtc app.

        Initializes GObjects and checks for required plugins.

        Arguments:
            stun_servers {[list of string]} -- Optional STUN server uris in the form of:
                                    stun:<host>:<port>
            turn_servers {[list of strings]} -- Optional TURN server uris in the form of:
                                    turn://<user>:<password>@<host>:<port>
        """

        self.stun_servers = stun_servers
        self.turn_servers = turn_servers
        self.audio = audio
        self.pipeline = None
        self.webrtcbin = None
        self.data_channel = None
        self.encoder = encoder

        self.framerate = framerate
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate

        # WebRTC ICE and SDP events
        self.on_ice = lambda mlineindex, candidate: logger.warn(
            'unhandled ice event')
        self.on_sdp = lambda sdp_type, sdp: logger.warn('unhandled sdp event')

        # Data channel events
        self.on_data_open = lambda: logger.warn('unhandled on_data_open')
        self.on_data_close = lambda: logger.warn('unhandled on_data_close')
        self.on_data_error = lambda: logger.warn('unhandled on_data_error')
        self.on_data_message = lambda msg: logger.warn(
            'unhandled on_data_message')

        Gst.init(None)

        self.check_plugins()

        self.pipeline = None
        self.ximagesrc = None
        self.last_cursor_sent = None

    def stop_ximagesrc(self):
        """Helper function to stop the ximagesrc, useful when resizing
        """
        if self.ximagesrc:
            self.ximagesrc.set_state(Gst.State.NULL)

    def start_ximagesrc(self):
        """Helper function to start the ximagesrc, useful when resizing
        """
        if self.ximagesrc:
            self.ximagesrc.set_property("endx", 0)
            self.ximagesrc.set_property("endy", 0)
            self.ximagesrc.set_state(Gst.State.PLAYING)

    # [START build_webrtcbin_pipeline]
    def build_webrtcbin_pipeline(self):
        """Adds the webrtcbin elments to the pipeline.

        The video and audio pipelines are linked to this in the
            build_video_pipline() and build_audio_pipeline() methods.
        """

        # Create webrtcbin element named app
        self.webrtcbin = Gst.ElementFactory.make("webrtcbin", "app")

        # The bundle policy affects how the SDP is generated.
        # This will ultimately determine how many tracks the browser receives.
        # Setting this to max-compat will generate separate tracks for
        # audio and video.
        # See also: https://webrtcstandards.info/sdp-bundle/
        self.webrtcbin.set_property("bundle-policy", "max-compat")

        # Connect signal handlers
        self.webrtcbin.connect(
            'on-negotiation-needed', lambda webrtcbin: self.__on_negotiation_needed(webrtcbin))
        self.webrtcbin.connect('on-ice-candidate', lambda webrtcbin, mlineindex,
                               candidate: self.__send_ice(webrtcbin, mlineindex, candidate))

        # Add STUN server
        # TODO: figure out how to add more than 1 stun server.
        if self.stun_servers:
            self.webrtcbin.set_property("stun-server", self.stun_servers[0])

        # Add TURN server
        if self.turn_servers:
            for turn_server in self.turn_servers:
                logger.info("adding TURN server: %s" % turn_server)
                self.webrtcbin.emit("add-turn-server", turn_server)

        # Add element to the pipeline.
        self.pipeline.add(self.webrtcbin)
    # [END build_webrtcbin_pipeline]

    # [START build_video_pipeline]
    def build_video_pipeline(self):
        """Adds the RTP video stream to the pipeline.
        """

        # Create ximagesrc element named x11
        # Note that when using the ximagesrc plugin, ensure that the X11 server was
        # started with shared memory support: '+extension MIT-SHM' to achieve
        # full frame rates.
        # You can check if XSHM is in use with the following command:
        #   GST_DEBUG=default:5 gst-launch-1.0 ximagesrc ! fakesink num-buffers=1 2>&1 |grep -i xshm
        self.ximagesrc = Gst.ElementFactory.make("ximagesrc", "x11")
        ximagesrc = self.ximagesrc

        # disables display of the pointer using the XFixes extension,
        # common when building a remote desktop interface as the clients
        # mouse pointer can be used to give the user perceived lower latency.
        # This can be programmatically toggled after the pipeline is started
        # for example if the user is viewing full screen in the browser,
        # they may want to revert to seeing the remote cursor when the
        # client side cursor disappears.
        ximagesrc.set_property("show-pointer", 0)

        # Tells GStreamer that you are using an X11 window manager or
        # compositor with off-screen buffer. If you are not using a
        # window manager this can be set to 0. It's also important to
        # make sure that your X11 server is running with the XSHM extension
        # to ensure direct memory access to frames which will reduce latency.
        ximagesrc.set_property("remote", 1)

        # Defines the size in bytes to read per buffer. Increasing this from
        # the default of 4096 bytes helps performance when capturing high
        # resolutions like 1080P, and 2K.
        ximagesrc.set_property("blocksize", 16384)

        # The X11 XDamage extension allows the X server to indicate when a
        # regions of the screen has changed. While this can significantly
        # reduce CPU usage when the screen is idle, it has little effect with
        # constant motion. This can also have a negative consequences with H.264
        # as the video stream can drop out and take several seconds to recover
        # until a valid I-Frame is received.
        # Set this to 0 for most streaming use cases.
        ximagesrc.set_property("use-damage", 0)

        # Create capabilities for ximagesrc
        ximagesrc_caps = Gst.caps_from_string("video/x-raw")

        # Setting the framerate=60/1 capability instructs the ximagesrc element
        # to generate buffers at 60 frames per second (FPS).
        # The higher the FPS, the lower the latency so this parameter is one
        # way to set the overall target latency of the pipeline though keep in
        # mind that the pipeline may not always perfom at the full 60 FPS.
        ximagesrc_caps.set_value("framerate", Gst.Fraction(self.framerate, 1))

        # Create a capability filter for the ximagesrc_caps
        ximagesrc_capsfilter = Gst.ElementFactory.make("capsfilter")
        ximagesrc_capsfilter.set_property("caps", ximagesrc_caps)

        if self.encoder in ["nvh264enc"]:
            # Upload buffers from ximagesrc directly to CUDA memory where
            # the colorspace conversion will be performed.
            cudaupload = Gst.ElementFactory.make("cudaupload")

            # Convert the colorspace from BGRx to NVENC compatible format.
            # This is performed with CUDA which reduces the overall CPU load
            # compared to using the software videoconvert element.
            cudaconvert = Gst.ElementFactory.make("cudaconvert")

            # Convert ximagesrc BGRx format to I420 using cudaconvert.
            # This is a more compatible format for client-side software decoders.
            cudaconvert_caps = Gst.caps_from_string("video/x-raw(memory:CUDAMemory)")
            cudaconvert_caps.set_value("format", "I420")
            cudaconvert_capsfilter = Gst.ElementFactory.make("capsfilter")
            cudaconvert_capsfilter.set_property("caps", cudaconvert_caps)

            # Create the nvh264enc element named nvenc.
            # This is the heart of the video pipeline that converts the raw
            # frame buffers to an H.264 encoded byte-stream on the GPU.
            nvh264enc = Gst.ElementFactory.make("nvh264enc", "nvenc")

            # The initial bitrate of the encoder in bits per second.
            # Setting this to 0 will use the bitrate from the NVENC preset.
            # This parameter can be set while the pipeline is running using the
            # set_video_bitrate() method. This helps to match the available
            # bandwidth. If set too high, the cliend side jitter buffer will
            # not be unable to lock on to the stream and it will fail to render.
            nvh264enc.set_property("bitrate", self.video_bitrate)

            # Rate control mode tells the encoder how to compress the frames to
            # reach the target bitrate. A Constant Bit Rate (CBR) setting is best
            # for streaming use cases as bit rate is the most important factor.
            # A Variable Bit Rate (VBR) setting tells the encoder to adjust the
            # compression level based on scene complexity, something not needed
            # when streaming in real-time.
            nvh264enc.set_property("rc-mode", "cbr")

            # Group of Pictures (GOP) size is the distance between I-Frames that
            # contain the full frame data needed to render a whole frame.
            # Infinite GOP is best for streaming because it reduces the number
            # of large I-Frames being transmitted. At higher resolutions, these
            # I-Frames can dominate the bandwidth and add additional latency.
            # With infinite GOP, you can use a higher bit rate to increase quality
            # without a linear increase in total bandwidth.
            # A negative consequence when using infinite GOP size is that
            # when packets are lost, it may take the decoder longer to recover.
            # NVENC supports infinite GOP by setting this to -1.
            nvh264enc.set_property("gop-size", -1)

            # Instructs encoder to handle Quality of Service (QOS) events from
            # the rest of the pipeline. Setting this to true increases
            # encoder stability.
            nvh264enc.set_property("qos", True)

            # The NVENC encoder supports a limited nubmer of encoding presets.
            # These presets are different than the open x264 standard.
            # The presets control the picture coding technique, bitrate,
            # and encoding quality.
            # The low-latency-hq is the NVENC preset reccomended for streaming.
            #
            # See this link for details on each preset:
            #   https://streamquality.report/docs/report.html#1080p60-nvenc-h264-picture-quality
            nvh264enc.set_property("preset", "low-latency-hq")

            # Set the capabilities for the nvh264enc element.
            nvh264enc_caps = Gst.caps_from_string("video/x-h264")

            # Sets the H.264 encoding profile to one compatible with WebRTC.
            # The high profile is used for streaming HD video.
            # Browsers only support specific H.264 profiles and they are
            # coded in the RTP payload type set by the rtph264pay_caps below.
            nvh264enc_caps.set_value("profile", "high")

            # Create a capability filter for the nvh264enc_caps.
            nvh264enc_capsfilter = Gst.ElementFactory.make("capsfilter")
            nvh264enc_capsfilter.set_property("caps", nvh264enc_caps)

            # Create the rtph264pay element to convert buffers into
            # RTP packets that are sent over the connection transport.
            rtph264pay = Gst.ElementFactory.make("rtph264pay")

            # Set the capabilities for the rtph264pay element.
            rtph264pay_caps = Gst.caps_from_string("application/x-rtp")

            # Set the payload type to video.
            rtph264pay_caps.set_value("media", "video")

            # Set the video encoding name to match our encoded format.
            rtph264pay_caps.set_value("encoding-name", "H264")

            # Set the payload type to one that matches the encoding profile.
            # Payload number 123 corresponds to H.264 encoding with the high profile.
            # Other payloads can be derived using WebRTC specification:
            #   https://tools.ietf.org/html/rfc6184#section-8.2.1
            rtph264pay_caps.set_value("payload", 123)

            # Set caps that help with frame retransmits that will avoid screen freezing on packet loss.
            rtph264pay_caps.set_value("rtcp-fb-nack-pli", True)
            rtph264pay_caps.set_value("rtcp-fb-ccm-fir", True)
            rtph264pay_caps.set_value("rtcp-fb-x-gstreamer-fir-as-repair", True)

            # Create a capability filter for the rtph264pay_caps.
            rtph264pay_capsfilter = Gst.ElementFactory.make("capsfilter")
            rtph264pay_capsfilter.set_property("caps", rtph264pay_caps)

        elif self.encoder in ["x264enc"]:
            # Videoconvert for colorspace conversion
            videoconvert = Gst.ElementFactory.make("videoconvert")
            videoconvert_caps = Gst.caps_from_string("video/x-raw")
            videoconvert_capsfilter = Gst.ElementFactory.make("capsfilter")
            videoconvert_capsfilter.set_property("caps", videoconvert_caps)

            # encoder
            x264enc = Gst.ElementFactory.make("x264enc", "x264enc")
            x264enc.set_property("threads", 4)
            x264enc.set_property("bframes", 0)
            x264enc.set_property("key-int-max", 0)
            x264enc.set_property("byte-stream", True)
            x264enc.set_property("tune", "zerolatency")
            x264enc.set_property("speed-preset", "veryfast")
            x264enc.set_property("bitrate", self.video_bitrate)

            # capsfilter
            x264enc_caps = Gst.caps_from_string("video/x-h264")
            x264enc_caps.set_value("stream-format", "byte-stream")
            x264enc_caps.set_value("profile", "high")
            x264enc_capsfilter = Gst.ElementFactory.make("capsfilter")
            x264enc_capsfilter.set_property("caps", x264enc_caps)

            # RTP payload
            rtph264pay = Gst.ElementFactory.make("rtph264pay")
            rtph264pay_caps = Gst.caps_from_string("application/x-rtp")
            rtph264pay_caps.set_value("media", "video")
            rtph264pay_caps.set_value("encoding-name", "H264")
            rtph264pay_caps.set_value("payload", 123)
            rtph264pay_caps.set_value("rtcp-fb-nack-pli", True)
            rtph264pay_caps.set_value("rtcp-fb-ccm-fir", True)
            rtph264pay_caps.set_value("rtcp-fb-x-gstreamer-fir-as-repair", True)

            # Create a capability filter for the rtph264pay_caps.
            rtph264pay_capsfilter = Gst.ElementFactory.make("capsfilter")
            rtph264pay_capsfilter.set_property("caps", rtph264pay_caps)

        elif self.encoder in ["vp8enc", "vp9enc"]:
            videoconvert = Gst.ElementFactory.make("videoconvert")
            videoconvert_caps = Gst.caps_from_string("video/x-raw,format=I420")
            videoconvert_capsfilter = Gst.ElementFactory.make("capsfilter")
            videoconvert_capsfilter.set_property("caps", videoconvert_caps)

            if self.encoder == "vp8enc":
                vpenc = Gst.ElementFactory.make("vp8enc", "vpenc")
                vpenc_caps = Gst.caps_from_string("video/x-vp8")
                vpenc_capsfilter = Gst.ElementFactory.make("capsfilter")
                vpenc_capsfilter.set_property("caps", vpenc_caps)

                rtpvppay = Gst.ElementFactory.make("rtpvp8pay")
                rtpvppay_caps = Gst.caps_from_string("application/x-rtp")
                rtpvppay_caps.set_value("media", "video")
                rtpvppay_caps.set_value("encoding-name", "VP8")
                rtpvppay_caps.set_value("payload", 123)
                rtpvppay_capsfilter = Gst.ElementFactory.make("capsfilter")
                rtpvppay_capsfilter.set_property("caps", rtpvppay_caps)

            if self.encoder == "vp9enc":
                vpenc = Gst.ElementFactory.make("vp9enc", "vpenc")
                vpenc.set_property("threads", 4)
                vpenc_caps = Gst.caps_from_string("video/x-vp9")
                vpenc_capsfilter = Gst.ElementFactory.make("capsfilter")
                vpenc_capsfilter.set_property("caps", vpenc_caps)

                rtpvppay = Gst.ElementFactory.make("rtpvp9pay")
                rtpvppay_caps = Gst.caps_from_string("application/x-rtp")
                rtpvppay_caps.set_value("media", "video")
                rtpvppay_caps.set_value("encoding-name", "VP9")
                rtpvppay_caps.set_value("payload", 123)
                rtpvppay_capsfilter = Gst.ElementFactory.make("capsfilter")
                rtpvppay_capsfilter.set_property("caps", rtpvppay_caps)

            # VPX Parameters
            # Borrowed from: https://github.com/nurdism/neko/blob/df98368137732b8aaf840e27cdf2bd41067b2161/server/internal/gst/gst.go#L94
            vpenc.set_property("threads", 2)
            vpenc.set_property("cpu-used", 8)
            vpenc.set_property("deadline", 1)
            vpenc.set_property("error-resilient", "partitions")
            vpenc.set_property("keyframe-max-dist", 10)
            vpenc.set_property("auto-alt-ref", True)
            vpenc.set_property("target-bitrate", self.video_bitrate*1000)

        else:
            raise GSTWebRTCAppError("Unsupported encoder for pipeline: %s" % self.encoder)

        # Add all elements to the pipeline.
        self.pipeline.add(ximagesrc)
        self.pipeline.add(ximagesrc_capsfilter)

        if self.encoder == "nvh264enc":
            self.pipeline.add(cudaupload)
            self.pipeline.add(cudaconvert)
            self.pipeline.add(cudaconvert_capsfilter)
            self.pipeline.add(nvh264enc)
            self.pipeline.add(nvh264enc_capsfilter)
            self.pipeline.add(rtph264pay)
            self.pipeline.add(rtph264pay_capsfilter)

        if self.encoder == "x264enc":
            self.pipeline.add(videoconvert)
            self.pipeline.add(videoconvert_capsfilter)
            self.pipeline.add(x264enc)
            self.pipeline.add(x264enc_capsfilter)
            self.pipeline.add(rtph264pay)
            self.pipeline.add(rtph264pay_capsfilter)

        elif self.encoder.startswith("vp"):
            self.pipeline.add(videoconvert)
            self.pipeline.add(videoconvert_capsfilter)
            self.pipeline.add(vpenc)
            self.pipeline.add(vpenc_capsfilter)
            self.pipeline.add(rtpvppay)
            self.pipeline.add(rtpvppay_capsfilter)

        # Link the pipeline elements and raise exception of linking fails
        # due to incompatible element pad capabilities.
        if not Gst.Element.link(ximagesrc, ximagesrc_capsfilter):
            raise GSTWebRTCAppError("Failed to link ximagesrc -> ximagesrc_capsfilter")

        if self.encoder == "nvh264enc":
            if not Gst.Element.link(ximagesrc_capsfilter, cudaupload):
                raise GSTWebRTCAppError(
                    "Failed to link ximagesrc_capsfilter -> cudaupload")

            if not Gst.Element.link(cudaupload, cudaconvert):
                raise GSTWebRTCAppError(
                    "Failed to link cudaupload -> cudaconvert")

            if not Gst.Element.link(cudaconvert, cudaconvert_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link cudaconvert -> cudaconvert_capsfilter")

            if not Gst.Element.link(cudaconvert_capsfilter, nvh264enc):
                raise GSTWebRTCAppError(
                    "Failed to link cudaconvert_capsfilter -> nvh264enc")

            if not Gst.Element.link(nvh264enc, nvh264enc_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link nvh264enc -> nvh264enc_capsfilter")

            if not Gst.Element.link(nvh264enc_capsfilter, rtph264pay):
                raise GSTWebRTCAppError(
                    "Failed to link nvh264enc_capsfilter -> rtph264pay")

            if not Gst.Element.link(rtph264pay, rtph264pay_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link rtph264pay -> rtph264pay_capsfilter")

            # Link the last element to the webrtcbin
            if not Gst.Element.link(rtph264pay_capsfilter, self.webrtcbin):
                raise GSTWebRTCAppError(
                    "Failed to link rtph264pay_capsfilter -> webrtcbin")

        elif self.encoder == "x264enc":
            if not Gst.Element.link(ximagesrc_capsfilter, videoconvert):
                raise GSTWebRTCAppError(
                    "Failed to link ximagesrc_capsfilter -> videoconvert")

            if not Gst.Element.link(videoconvert, videoconvert_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link videoconvert -> videoconvert_capsfilter")

            if not Gst.Element.link(videoconvert_capsfilter, x264enc):
                raise GSTWebRTCAppError(
                    "Failed to link videoconvert_capsfilter -> x264enc")

            if not Gst.Element.link(x264enc, x264enc_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link x264enc -> x264enc_capsfilter")

            if not Gst.Element.link(x264enc_capsfilter, rtph264pay):
                raise GSTWebRTCAppError(
                    "Failed to link x264enc_capsfilter -> rtph264pay")

            if not Gst.Element.link(rtph264pay, rtph264pay_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link rtph264pay -> rtph264pay_capsfilter")

            # Link the last element to the webrtcbin
            if not Gst.Element.link(rtph264pay_capsfilter, self.webrtcbin):
                raise GSTWebRTCAppError(
                    "Failed to link rtph264pay_capsfilter -> webrtcbin")

        elif self.encoder.startswith("vp"):
            if not Gst.Element.link(ximagesrc_capsfilter, videoconvert):
                raise GSTWebRTCAppError(
                    "Failed to link ximagesrc_capsfilter -> videoconvert")

            if not Gst.Element.link(videoconvert, videoconvert_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link videoconvert -> videoconvert_capsfilter")

            if not Gst.Element.link(videoconvert_capsfilter, vpenc):
                raise GSTWebRTCAppError(
                    "Failed to link videoconvert_capsfilter -> vpenc")

            if not Gst.Element.link(vpenc, vpenc_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link vpenc -> vpenc_capsfilter")

            if not Gst.Element.link(vpenc_capsfilter, rtpvppay):
                raise GSTWebRTCAppError(
                    "Failed to link vpenc_capsfilter -> rtpvppay")

            if not Gst.Element.link(rtpvppay, rtpvppay_capsfilter):
                raise GSTWebRTCAppError(
                    "Failed to link rtpvppay -> rtpvppay_capsfilter")

            # Link the last element to the webrtcbin
            if not Gst.Element.link(rtpvppay_capsfilter, self.webrtcbin):
                raise GSTWebRTCAppError(
                    "Failed to link rtpvppay_capsfilter -> webrtcbin")

    # [END build_video_pipeline]

    # [START build_audio_pipeline]
    def build_audio_pipeline(self):
        """Adds the RTP audio stream to the pipeline.
        """

        # Create element for receiving audio from pulseaudio.
        pulsesrc = Gst.ElementFactory.make("pulsesrc", "pulsesrc")

        # Let the audio source provide the global clock.
        # This is important when trying to keep the audio and video
        # jitter buffers in sync. If there is skew between the video and audio
        # buffers, features like NetEQ will continuously increase the size of the
        # jitter buffer to catch up and will never recover.
        pulsesrc.set_property("provide-clock", True)

        # Apply stream time to buffers, this helps with pipeline synchronization.
        pulsesrc.set_property("do-timestamp", True)

        # Encode the raw pulseaudio stream to opus format which is the
        # default packetized streaming format for the web.
        opusenc = Gst.ElementFactory.make("opusenc", "opusenc")

        # Set audio bitrate to 64kbps.
        # This can be dynamically changed using set_audio_bitrate()
        opusenc.set_property("bitrate", self.audio_bitrate)

        # Create the rtpopuspay element to convert buffers into
        # RTP packets that are sent over the connection transport.
        rtpopuspay = Gst.ElementFactory.make("rtpopuspay")

        # Insert a queue for the RTP packets.
        rtpopuspay_queue = Gst.ElementFactory.make("queue", "rtpopuspay_queue")

        # Make the queue leaky, so just drop packets if the queue is behind.
        rtpopuspay_queue.set_property("leaky", True)

        # Set the queue max time to 16ms (16000000ns)
        # If the pipeline is behind by more than 1s, the packets
        # will be dropped.
        # This helps buffer out latency in the audio source.
        rtpopuspay_queue.set_property("max-size-time", 16000000)

        # Set the other queue sizes to 0 to make it only time-based.
        rtpopuspay_queue.set_property("max-size-buffers", 0)
        rtpopuspay_queue.set_property("max-size-bytes", 0)

        # Set the capabilities for the rtpopuspay element.
        rtpopuspay_caps = Gst.caps_from_string("application/x-rtp")

        # Set the payload type to audio.
        rtpopuspay_caps.set_value("media", "audio")

        # Set the audio encoding name to match our encoded format.
        rtpopuspay_caps.set_value("encoding-name", "OPUS")

        # Set the payload type to match the encoding format.
        # A value of 96 is the default that most browsers use for Opus.
        # See the RFC for details:
        #   https://tools.ietf.org/html/rfc4566#section-6
        rtpopuspay_caps.set_value("payload", 96)

        # Create a capability filter for the rtpopuspay_caps.
        rtpopuspay_capsfilter = Gst.ElementFactory.make("capsfilter")
        rtpopuspay_capsfilter.set_property("caps", rtpopuspay_caps)

        # Add all elements to the pipeline.
        self.pipeline.add(pulsesrc)
        self.pipeline.add(opusenc)
        self.pipeline.add(rtpopuspay)
        self.pipeline.add(rtpopuspay_queue)
        self.pipeline.add(rtpopuspay_capsfilter)

        # Link the pipeline elements and raise exception of linking fails
        # due to incompatible element pad capabilities.
        if not Gst.Element.link(pulsesrc, opusenc):
            raise GSTWebRTCAppError("Failed to link pulsesrc -> opusenc")

        if not Gst.Element.link(opusenc, rtpopuspay):
            raise GSTWebRTCAppError("Failed to link opusenc -> rtpopuspay")

        if not Gst.Element.link(rtpopuspay, rtpopuspay_queue):
            raise GSTWebRTCAppError("Failed to link rtpopuspay -> rtpopuspay_queue")

        if not Gst.Element.link(rtpopuspay_queue, rtpopuspay_capsfilter):
            raise GSTWebRTCAppError(
                "Failed to link rtpopuspay_queue -> rtpopuspay_capsfilter")

        # Link the last element to the webrtcbin
        if not Gst.Element.link(rtpopuspay_capsfilter, self.webrtcbin):
            raise GSTWebRTCAppError(
                "Failed to link rtpopuspay_capsfilter -> webrtcbin")
    # [END build_audio_pipeline]

    def check_plugins(self):
        """Check for required gstreamer plugins.

        Raises:
            GSTWebRTCAppError -- thrown if any plugins are missing.
        """

        required = ["opus", "nice", "webrtc", "dtls", "srtp", "rtp", "sctp",
                    "rtpmanager", "ximagesrc"]

        supported = ["nvh264enc", "vp8enc", "vp9enc", "x264enc"]
        if self.encoder not in supported:
            raise GSTWebRTCAppError('Unsupported encoder, must be one of: ' + ','.join(supported))

        if self.encoder.startswith("nv"):
            required.append("nvcodec")

        if self.encoder.startswith("vp"):
            required.append("vpx")

        missing = list(
            filter(lambda p: Gst.Registry.get().find_plugin(p) is None, required))
        if missing:
            raise GSTWebRTCAppError('Missing gstreamer plugins:', missing)

    def set_sdp(self, sdp_type, sdp):
        """Sets remote SDP received by peer.

        Arguments:
            sdp_type {string} -- type of sdp, offer or answer
            sdp {object} -- SDP object

        Raises:
            GSTWebRTCAppError -- thrown if SDP is recevied before session has been started.
            GSTWebRTCAppError -- thrown if SDP type is not 'answer', this script initiates the call, not the peer.
        """

        if not self.webrtcbin:
            raise GSTWebRTCAppError('Received SDP before session started')

        if sdp_type != 'answer':
            raise GSTWebRTCAppError('ERROR: sdp type was not "answer"')

        _, sdpmsg = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
        answer = GstWebRTC.WebRTCSessionDescription.new(
            GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
        promise = Gst.Promise.new()
        self.webrtcbin.emit('set-remote-description', answer, promise)
        promise.interrupt()

    def set_ice(self, mlineindex, candidate):
        """Adds ice candidate received from signalling server

        Arguments:
            mlineindex {integer} -- the mlineindex
            candidate {string} -- the candidate

        Raises:
            GSTWebRTCAppError -- thrown if called before session is started.
        """

        logger.info("setting ICE candidate: %d, %s" % (mlineindex, candidate))

        if not self.webrtcbin:
            raise GSTWebRTCAppError('Received ICE before session started')

        self.webrtcbin.emit('add-ice-candidate', mlineindex, candidate)

    def set_enable_audio(self, enabled):
        """Set pipeline audio state

        Arguments:
            enabled {boolean} -- true of false indicating if audio should be enabled the next time the pipeline is built.
        """
        self.audio = enabled
        logger.info("audio set to: %s" % str(enabled))

    def set_framerate(self, framerate):
        """Set pipeline framerate in fps

        Arguments:
            framerate {integer} -- framerate in frames per second, for example, 15, 30, 60.
        """
        self.framerate = framerate
        logger.info("framerate set to: %d" % framerate)

    def set_video_bitrate(self, bitrate):
        """Set NvEnc encoder target bitrate in bps

        Arguments:
            bitrate {integer} -- bitrate in bits per second, for example, 2000 for 2kbits/s or 10000 for 1mbit/sec.
        """

        if self.encoder.startswith("nv"):
            element = Gst.Bin.get_by_name(self.pipeline, "nvenc")
            element.set_property("bitrate", bitrate)
        elif self.encoder.startswith("x264"):
            element = Gst.Bin.get_by_name(self.pipeline, "x264enc")
            element.set_property("bitrate", bitrate)
        elif self.encoder.startswith("vp"):
            element = Gst.Bin.get_by_name(self.pipeline, "vpenc")
            element.set_property("target-bitrate", bitrate*1000)
        else:
            logger.warning("set_video_bitrate not supported with encoder: %s" % self.encoder)

        logger.info("video bitrate set to: %d" % bitrate)

        self.video_bitrate = bitrate

        self.__send_data_channel_message(
            "pipeline", {"status": "Video bitrate set to: %d" % bitrate})

    def set_audio_bitrate(self, bitrate):
        """Set Opus encoder target bitrate in bps

        Arguments:
            bitrate {integer} -- bitrate in bits per second, for example, 96000 for 96kbits/s.
        """

        if self.audio:
            element = Gst.Bin.get_by_name(self.pipeline, "opusenc")
            element.set_property("bitrate", bitrate)

            logger.info("audio bitrate set to: %d" % bitrate)
            self.audio_bitrate = bitrate
            self.__send_data_channel_message(
                "pipeline", {"status": "Audio bitrate set to: %d" % bitrate})

    def set_pointer_visible(self, visible):
        """Set pointer visibiltiy on the ximagesrc element

        Arguments:
            visible {bool} -- True to enable pointer visibility
        """

        element = Gst.Bin.get_by_name(self.pipeline, "x11")
        element.set_property("show-pointer", visible)
        self.__send_data_channel_message(
            "pipeline", {"status": "Set pointer visibility to: %d" % visible})

    def send_clipboard_data(self, data):
        self.__send_data_channel_message(
            "clipboard", {"content": base64.b64encode(data.encode()).decode("utf-8")})

    def send_cursor_data(self, data):
        self.last_cursor_sent = data
        self.__send_data_channel_message(
            "cursor", data)

    def send_gpu_stats(self, load, memory_total, memory_used):
        """Sends GPU stats to the data channel

        Arguments:
            load {float} -- utilization of GPU between 0 and 1
            memory_total {float} -- total memory on GPU in MB
            memory_used {float} -- memor used on GPU in MB
        """

        self.__send_data_channel_message("gpu_stats", {
            "load": load,
            "memory_total": memory_total,
            "memory_used": memory_used,
        })

    def send_reload_window(self):
        """Sends reload window command to the data channel
        """

        logger.info("sending window reload")
        self.__send_data_channel_message(
            "system", {"action": "reload"})

    def send_framerate(self, framerate):
        """Sends the current frame rate to the data channel
        """

        logger.info("sending frame rate")
        self.__send_data_channel_message(
            "system", {"action": "framerate,"+str(framerate)})

    def send_video_bitrate(self, bitrate):
        """Sends the current video bitrate to the data channel
        """
        logger.info("sending video bitrate")
        self.__send_data_channel_message(
            "system", {"action": "video_bitrate,%d" % bitrate})

    def send_audio_bitrate(self, bitrate):
        """Sends the current audio bitrate to the data channel
        """
        logger.info("sending audio bitrate")
        self.__send_data_channel_message(
            "system", {"action": "audio_bitrate,%d" % bitrate})

    def send_encoder(self, encoder):
        """Sends the encoder name to the data channel
        """

        logger.info("sending encoder: " + encoder)
        self.__send_data_channel_message(
            "system", {"action": "encoder,%s" % encoder})

    def send_audio_enabled(self, audio_enabled):
        """Sends the current audio state
        """

        logger.info("sending audio enabled")
        self.__send_data_channel_message(
            "system", {"action": "audio,"+str(audio_enabled)})

    def send_resize_enabled(self, resize_enabled):
        """Sends the current resize enabled state
        """

        logger.info("sending resize enabled state")
        self.__send_data_channel_message(
            "system", {"action": "resize,"+str(resize_enabled)})

    def send_ping(self, t):
        """Sends a ping request over the data channel to measure latency
        """

        self.__send_data_channel_message(
            "ping", {"start_time": float("%.3f" % t)})

    def send_latency_time(self, latency):
        """Sends measured latency response time in ms
        """

        self.__send_data_channel_message(
            "latency_measurement", {"latency_ms": latency})

    def send_system_stats(self, cpu_percent, mem_total, mem_used):
        """Sends system stats
        """

        self.__send_data_channel_message(
            "system_stats", {
                "cpu_percent": cpu_percent,
                "mem_total": mem_total,
                "mem_used": mem_used,
            })

    def is_data_channel_ready(self):
        """Checks to see if the data channel is open.

        Returns:
            [bool] -- true if data channel is open
        """

        return self.data_channel and self.data_channel.get_property("ready-state").value_name == 'GST_WEBRTC_DATA_CHANNEL_STATE_OPEN'

    def __send_data_channel_message(self, msg_type, data):
        """Sends message to the peer through the data channel

        Message is dropped if the channel is not open.

        Arguments:
            msg_type {string} -- the type of message being sent
            data {dict} -- data to send, this is JSON serialized.
        """

        if not self.is_data_channel_ready():
            logger.debug(
                "skipping messaage because data channel is not ready: %s" % msg_type)
            return

        msg = {
            "type": msg_type,
            "data": data,
        }
        self.data_channel.emit("send-string", json.dumps(msg))

    def __on_offer_created(self, promise, _, __):
        """Handles on-offer-created promise resolution

        The offer contains the local description.
        Generate a set-local-description action with the offer.
        Sends the offer to the on_sdp handler.

        Arguments:
            promise {GstPromise} -- the promise
            _ {object} -- unused
            __ {object} -- unused
        """

        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value('offer')
        promise = Gst.Promise.new()
        self.webrtcbin.emit('set-local-description', offer, promise)
        promise.interrupt()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.on_sdp('offer', offer.sdp.as_text()))

    def __on_negotiation_needed(self, webrtcbin):
        """Handles on-negotiation-needed signal, generates create-offer action

        Arguments:
            webrtcbin {GstWebRTCBin gobject} -- webrtcbin gobject
        """

        logger.info("handling on-negotiation-needed, creating offer.")
        promise = Gst.Promise.new_with_change_func(
            self.__on_offer_created, webrtcbin, None)
        webrtcbin.emit('create-offer', None, promise)

    def __send_ice(self, webrtcbin, mlineindex, candidate):
        """Handles on-ice-candidate signal, generates on_ice event

        Arguments:
            webrtcbin {GstWebRTCBin gobject} -- webrtcbin gobject
            mlineindex {integer} -- ice candidate mlineindex
            candidate {string} -- ice candidate string
        """

        logger.debug("received ICE candidate: %d %s", mlineindex, candidate)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.on_ice(mlineindex, candidate))

    def start_pipeline(self):
        """Starts the gstreamer pipeline
        """

        logger.info("starting pipeline")

        self.pipeline = Gst.Pipeline.new()

        # Construct the webrtcbin pipeline with video and audio.
        self.build_webrtcbin_pipeline()
        self.build_video_pipeline()

        if self.audio:
            self.build_audio_pipeline()

        # Advance the state of the pipeline to PLAYING.
        res = self.pipeline.set_state(Gst.State.PLAYING)
        if res.value_name != 'GST_STATE_CHANGE_SUCCESS':
            raise GSTWebRTCAppError(
                "Failed to transition pipeline to PLAYING: %s" % res)

        # Create the data channel, this has to be done after the pipeline is PLAYING.
        options = Gst.Structure("application/data-channel")
        options.set_value("ordered", True)
        options.set_value("max-retransmits", 0)
        self.data_channel = self.webrtcbin.emit(
            'create-data-channel', "input", options)
        self.data_channel.connect('on-open', lambda _: self.on_data_open())
        self.data_channel.connect('on-close', lambda _: self.on_data_close())
        self.data_channel.connect('on-error', lambda _: self.on_data_error())
        self.data_channel.connect(
            'on-message-string', lambda _, msg: self.on_data_message(msg))

        # Enable NACKs on the transceiver, helps with retransmissions and freezing when packets are dropped.
        transceiver = self.webrtcbin.emit("get-transceiver", 0)
        transceiver.set_property("do-nack", True)

        logger.info("pipeline started")

    def stop_pipeline(self):
        logger.info("stopping pipeline")
        if self.data_channel:
            self.data_channel.emit('close')
            self.data_channel = None
            logger.info("data channel closed")
        if self.pipeline:
            logger.info("setting pipeline state to NULL")
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.unparent()
            self.pipeline = None
            logger.info("pipeline set to state NULL")
        if self.webrtcbin:
            self.webrtcbin.set_state(Gst.State.NULL)
            self.webrtcbin.unparent()
            self.webrtcbin = None
            logger.info("webrtcbin set to state NULL")
        logger.info("pipeline stopped")