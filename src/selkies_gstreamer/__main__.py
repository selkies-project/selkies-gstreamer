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

import argparse
import asyncio
import http.client
import json
import logging
import os
import socket
import sys
import time
import urllib.parse

from watchdog.observers import Observer
from watchdog.events import FileClosedEvent, FileSystemEventHandler
from webrtc_input import WebRTCInput
from webrtc_signalling import WebRTCSignalling, WebRTCSignallingErrorNoPeer
from gstwebrtc_app import GSTWebRTCApp
from gpu_monitor import GPUMonitor
from system_monitor import SystemMonitor
from metrics import Metrics
from resize import resize_display, get_new_res
from signalling_web import WebRTCSimpleServer, generate_rtc_config

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

DEFAULT_RTC_CONFIG = """{
  "lifetimeDuration": "86400s",
  "iceServers": [
    {
      "urls": [
        "stun:stun.l.google.com:19302"
      ]
    }
  ],
  "blockStatus": "NOT_BLOCKED",
  "iceTransportPolicy": "all"
}"""

class HMACRTCMonitor:
    def __init__(self, turn_host, turn_port, turn_shared_secret, turn_username, period=60, enabled=True):
        self.turn_host = turn_host
        self.turn_port = turn_port
        self.turn_username = turn_username
        self.turn_shared_secret = turn_shared_secret
        self.period = period
        self.enabled = enabled

        self.running = False

        self.on_rtc_config = lambda stun_servers, turn_servers, rtc_config: logger.warning(
            "unhandled on_rtc_config")

    def start(self):
        self.running = True
        while self.running:
            if self.enabled:
                try:
                    data = generate_rtc_config(self.turn_host, self.turn_port, self.turn_shared_secret, self.turn_username)
                    stun_servers, turn_servers, rtc_config = parse_rtc_config(data)
                    self.on_rtc_config(stun_servers, turn_servers, rtc_config)
                except Exception as e:
                    logger.warning("could not fetch coturn config in periodic monitor: {}".format(e))
            time.sleep(self.period)

    def stop(self):
        self.running = False

class CoturnRTCMonitor:
    def __init__(self, coturn_web_uri, coturn_web_username, coturn_auth_header_name, period=60, enabled=True):
        self.period = period
        self.enabled = enabled
        self.running = False

        self.coturn_web_uri = coturn_web_uri
        self.coturn_web_username = coturn_web_username
        self.coturn_auth_header_name = coturn_auth_header_name

        self.on_rtc_config = lambda stun_servers, turn_servers, rtc_config: logger.warning(
            "unhandled on_rtc_config")

    def start(self):
        self.running = True
        while self.running:
            if self.enabled:
                try:
                    stun_servers, turn_servers, rtc_config = fetch_coturn(self.coturn_web_uri, self.coturn_web_username, self.coturn_auth_header_name)
                    self.on_rtc_config(stun_servers, turn_servers, rtc_config)
                except Exception as e:
                    logger.warning("could not fetch coturn config in periodic monitor: {}".format(e))
            time.sleep(self.period)

    def stop(self):
        self.running = False

class RTCConfigFileMonitor:
    def __init__(self, rtc_file, enabled=True):
        self.enabled = enabled
        self.running = False
        self.rtc_file = rtc_file

        self.on_rtc_config = lambda stun_servers, turn_servers, rtc_config: logger.warning(
            "unhandled on_rtc_config")
        
        self.observer = Observer()
        self.file_event_handler = FileSystemEventHandler()
        self.file_event_handler.on_closed = self.event_handler
        self.observer.schedule(self.file_event_handler, self.rtc_file, recursive=False)

    def event_handler(self, event):
        if type(event) is FileClosedEvent:
            print("Detected RTC JSON file change: {}".format(event.src_path))
            try:
                with open(self.rtc_file, 'rb') as f:
                    data = f.read()
                    stun_servers, turn_servers, rtc_config = parse_rtc_config(data)
                    self.on_rtc_config(stun_servers, turn_servers, rtc_config)
            except Exception as e:
                logger.warning("could not read RTC JSON file: {}: {}".format(self.rtc_file, e))
            
    def start(self):
        if self.enabled:
            self.observer.start()
            self.running = True

    def stop(self):
        self.observer.stop()
        self.running = False

def make_turn_rtc_config_json(host, port, username, password):
    return """{
  "lifetimeDuration": "86400s",
  "iceServers": [
    {
      "urls": [
        "stun:%s:%s"
      ]
    },
    {
      "urls": [
        "turn:%s:%s?transport=udp"
      ],
      "username": "%s",
      "credential": "%s"
    }
  ],
  "blockStatus": "NOT_BLOCKED",
  "iceTransportPolicy": "all"
}""" % (host, port, host, port, username, password)

def parse_rtc_config(data):
    ice_servers = json.loads(data)['iceServers']
    stun_uris = []
    turn_uris = []
    for server in ice_servers:
        for url in server.get("urls", []):
            if url.startswith("stun:"):
                stun_host = url.split(":")[1]
                stun_port = url.split(":")[2].split("?")[0]
                stun_uri = "stun://%s:%s" % (
                    stun_host,
                    stun_port
                )
                stun_uris.append(stun_uri)
            elif url.startswith("turn:"):
                turn_host = url.split(':')[1]
                turn_port = url.split(':')[2].split('?')[0]
                turn_user = server['username']
                turn_password = server['credential']
                turn_uri = "turn://%s:%s@%s:%s" % (
                    urllib.parse.quote(turn_user, safe=""),
                    urllib.parse.quote(turn_password, safe=""),
                    turn_host,
                    turn_port
                )
                turn_uris.append(turn_uri)
    return stun_uris, turn_uris, data

def fetch_coturn(uri, user, auth_header_name):
    """Fetches TURN uri from a coturn web API

    Arguments:
        uri {string} -- uri of coturn web service, example: http://localhost:8081/
        user {string} -- username used to generate coturn credential, for example: <hostname>

    Raises:
        Exception -- if response http status code is >= 400

    Returns:
        [string] -- TURN URI used with gstwebrtcbin in the form of:
                        turn://<user>:<password>@<host>:<port>
                    NOTE that the user and password are URI encoded to escape special characters like '/'
    """

    parsed_uri = urllib.parse.urlparse(uri)

    conn = http.client.HTTPConnection(parsed_uri.netloc)
    if parsed_uri.scheme == "https":
        conn = http.client.HTTPSConnection(parsed_uri.netloc)
    auth_headers = {
        auth_header_name: user
    }

    conn.request("GET", parsed_uri.path, headers=auth_headers)
    resp = conn.getresponse()
    data = resp.read()
    if resp.status >= 400:
        raise Exception("error fetching coturn web config. Status code: {}. {}, {}".format(resp.status, resp.reason, data))
    if not data:
        raise Exception("data from coturn web service was empty")
    return parse_rtc_config(data)

def wait_for_app_ready(ready_file, app_auto_init = True):
    """Wait for streaming app ready signal.

    returns when either app_auto_init is True OR the file at ready_file exists.

    Keyword Arguments:
        app_auto_init {bool} -- skip wait for appready file (default: {True})
    """

    logger.info("Waiting for streaming app ready")
    logging.debug("app_auto_init=%s, ready_file=%s" % (app_auto_init, ready_file))

    while not (app_auto_init or os.path.exists(ready_file)):
        time.sleep(0.2)

def set_json_app_argument(config_path, key, value):
    """Writes kv pair to json argument file

    Arguments:
        config_path {string} -- path to json config file, example: /var/run/appconfig/streaming_args.json
        key {string} -- the name of the argument to set
        value {any} -- the value of the argument to set
    """

    if not os.path.exists(config_path):
        # Create new file
        with open(config_path, 'w') as f:
            json.dump({}, f)

    # Read current config JSON
    json_data = json.load(open(config_path))

    # Set the new value for the argument.
    json_data[key] = value

    # Save the json file
    json.dump(json_data, open(config_path, 'w'))

    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_config',
                        default=os.environ.get(
                            'JSON_CONFIG', '/var/run/appconfig/streaming_args.json'),
                        help='Path to JSON file containing argument key-value pairs that are overlayed with cli args/env.')
    parser.add_argument('--addr',
                        default=os.environ.get(
                            'LISTEN_HOST', '0.0.0.0'),
                        help='Host to listen on for the signaling and web server, default: "0.0.0.0"')
    parser.add_argument('--port',
                        default=os.environ.get(
                            'LISTEN_PORT', '8080'),
                        help='Port to listen on for the signaling and web server, default: "8080"')
    parser.add_argument('--enable_basic_auth',
                        default=os.environ.get(
                            'ENABLE_BASIC_AUTH', 'false'),
                        help='Enable Basic authentication on server. Must set basic_auth_user and basic_auth_password to enforce Basic auth.')
    parser.add_argument('--basic_auth_user',
                        default=os.environ.get(
                            'BASIC_AUTH_USER', os.environ.get('USER', '')),
                        help='Username for basic auth, default is to use the USER env var. Must also set basic_auth_password to enforce Basic auth.')
    parser.add_argument('--basic_auth_password',
                        default=os.environ.get(
                            'BASIC_AUTH_PASSWORD', ''),
                        help='Password used when basic_auth_user is set.')
    parser.add_argument('--web_root',
                        default=os.environ.get(
                            'WEB_ROOT', '/opt/gst-web'),
                        help='Path to directory containing web app source, default: "/opt/gst-web"')
    parser.add_argument('--coturn_web_uri',
                        default=os.environ.get(
                            'COTURN_WEB_URI', ''),
                        help='URI for coturn REST API service, example: http://localhost:8081')
    parser.add_argument('--coturn_web_username',
                        default=os.environ.get(
                            'COTURN_WEB_USERNAME', "selkies-{}".format(socket.gethostname())),
                        help='URI for coturn REST API service, default is the system hostname')
    parser.add_argument('--coturn_auth_header_name',
                        default=os.environ.get(
                            'COTURN_AUTH_HEADER_NAME', 'x-auth-user'),
                        help='header name to pass user to coturn web service')
    parser.add_argument('--rtc_config_json',
                        default=os.environ.get(
                            'RTC_CONFIG_JSON', '/tmp/rtc.json'),
                        help='JSON file with RTC config to use as alternative to coturn service, read periodically')
    parser.add_argument('--turn_shared_secret',
                        default=os.environ.get(
                            'TURN_SHARED_SECRET', ''),
                        help='shared TURN secret used to generate HMAC credentials, also requires TURN_HOST and TURN_PORT.')
    parser.add_argument('--turn_username',
                        default=os.environ.get(
                            'TURN_USERNAME', ''),
                        help='Legacy non-HMAC TURN credential username, also requires TURN_HOST and TURN_PORT.')
    parser.add_argument('--turn_password',
                        default=os.environ.get(
                            'TURN_PASSWORD', ''),
                        help='Legacy non-HMAC TURN credential password, also requires TURN_HOST and TURN_PORT.')
    parser.add_argument('--turn_host',
                        default=os.environ.get(
                            'TURN_HOST', ''),
                        help='TURN host when generating RTC config from shared secret or legacy credentials.')
    parser.add_argument('--turn_port',
                        default=os.environ.get(
                            'TURN_PORT', ''),
                        help='TURN port when generating RTC config from shared secret or legacy credentials.')
    parser.add_argument('--uinput_mouse_socket',
                        default=os.environ.get('UINPUT_MOUSE_SOCKET', ''),
                        help='path to uinput mouse socket provided by uinput-device-plugin, if not provided, uinput is used directly.')
    parser.add_argument('--uinput_js_socket',
                        default=os.environ.get('UINPUT_JS_SOCKET', ''),
                        help='path to uinput joystick socket provided by uinput-device-plugin, if not provided, uinput is used directly.')
    parser.add_argument('--enable_audio',
                        default=os.environ.get('ENABLE_AUDIO', 'true'),
                        help='enable or disable audio stream')
    parser.add_argument('--enable_clipboard',
                        default=os.environ.get('ENABLE_CLIPBOARD', 'true'),
                        help='enable or disable the clipboard features, supported values: true, false, in, out')
    parser.add_argument('--app_auto_init',
                        default=os.environ.get('APP_AUTO_INIT', 'true'),
                        help='if true, skips wait for APP_READY_FILE to exist before starting stream.')
    parser.add_argument('--app_ready_file',
                        default=os.environ.get('APP_READY_FILE', '/var/run/appconfig/appready'),
                        help='file set by sidecar used to indicate that app is initialized and ready')
    parser.add_argument('--framerate',
                        default=os.environ.get('WEBRTC_FRAMERATE', '30'),
                        help='framerate of streaming pipeline')
    parser.add_argument('--video_bitrate',
                        default=os.environ.get('WEBRTC_VIDEO_BITRATE', '2000'),
                        help='default video bitrate')
    parser.add_argument('--audio_bitrate',
                        default=os.environ.get('WEBRTC_AUDIO_BITRATE', '64000'),
                        help='default audio bitrate')
    parser.add_argument('--encoder',
                        default=os.environ.get('WEBRTC_ENCODER', 'nvh264enc'),
                        help='gstreamer encoder plugin to use')
    parser.add_argument('--enable_resize', action='store_true',
                        default=os.environ.get('WEBRTC_ENABLE_RESIZE', 'true'),
                        help='Enable dynamic resizing to match browser size')
    parser.add_argument('--metrics_port',
                        default=os.environ.get('METRICS_PORT', '8000'),
                        help='port to start metrics server on')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    args = parser.parse_args()

    if os.path.exists(args.json_config):
        # Read and overlay args from json file
        # Note that these are explicit overrides only.
        try:
            json_args = json.load(open(args.json_config))
            for k, v in json_args.items():
                if k == "framerate":
                    args.framerate = int(v)
                if k == "video_bitrate":
                    args.video_bitrate = int(v)
                if k == "audio_bitrate":
                    args.audio_bitrate = int(v)
                if k == "enable_audio":
                    args.enable_audio = str((str(v).lower() == 'true')).lower()
                if k == "enable_resize":
                    args.enable_resize = str((str(v).lower() == 'true')).lower()
                if k == "encoder":
                    args.ecoder = v.lower()
        except Exception as e:
            logger.error("failed to load json config from %s: %s" % (args.json_config, str(e)))

    logging.warn(args)

    # Set log level
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Wait for streaming app to initialize
    wait_for_app_ready(args.app_ready_file, args.app_auto_init == "true")

    # Peer id for this app, default is 0, expecting remote peer id to be 1
    my_id = 0
    peer_id = 1

    # Initialize metrics server.
    metrics = Metrics(int(args.metrics_port))

    # Initialize the signalling client
    signalling = WebRTCSignalling('ws://127.0.0.1:%s/ws' % args.port, my_id, peer_id,
        enable_basic_auth=args.enable_basic_auth.lower() == 'true',
        basic_auth_user=args.basic_auth_user,
        basic_auth_password=args.basic_auth_password)

    # Handle errors from the signalling server.
    async def on_signalling_error(e):
       if isinstance(e, WebRTCSignallingErrorNoPeer):
           # Waiting for peer to connect, retry in 2 seconds.
           time.sleep(2)
           await signalling.setup_call()
       else:
           logger.error("signalling eror: %s", str(e))
           app.stop_pipeline()
    signalling.on_error = on_signalling_error

    signalling.on_disconnect = lambda: app.stop_pipeline()

    # After connecting, attempt to setup call to peer.
    signalling.on_connect = signalling.setup_call

    # [START main_setup]
    # Fetch the turn server and credentials
    rtc_config = None
    using_coturn = False
    using_hmac_turn = False
    using_rtc_config_json = False
    if os.path.exists(args.rtc_config_json):
        logger.warning("Using file for RTC config: %s", args.rtc_config_json)
        with open(args.rtc_config_json, 'r') as f:
            stun_servers, turn_servers, rtc_config = parse_rtc_config(f.read())
        using_rtc_config_json = True
    else:
        if args.turn_shared_secret:
            # Get HMAC credentials from built-in web server.
            using_hmac_turn = True
            data = generate_rtc_config(args.turn_host, args.turn_port, args.turn_shared_secret, args.coturn_web_username)
            stun_servers, turn_servers, rtc_config = parse_rtc_config(data)
        elif args.turn_username and args.turn_password:
            if not args.turn_host and args.turn_port:
                logger.error("missing turn host and turn port")
                sys.exit(1)
            logger.warning("using legacy non-HMAC TURN credentials.")
            config_json = make_turn_rtc_config_json(args.turn_host, args.turn_port, args.turn_username, args.turn_password)
            stun_servers, turn_servers, rtc_config = parse_rtc_config(config_json)
        else:
            # Use existing coturn-web infrastructure.
            try:
                stun_servers, turn_servers, rtc_config = fetch_coturn(
                    args.coturn_web_uri, args.coturn_web_username, args.coturn_auth_header_name)
                using_coturn = True
            except Exception as e:
                logger.warning("error fetching coturn RTC config, using DEFAULT_RTC_CONFIG: {}".format(str(e)))
                stun_servers, turn_servers, rtc_config = parse_rtc_config(DEFAULT_RTC_CONFIG)

    logger.info("initial server RTC config: {}".format(rtc_config))

    # Extract args
    enable_audio = args.enable_audio == "true"
    enable_resize = args.enable_resize == "true"
    curr_fps = int(args.framerate)
    curr_video_bitrate = int(args.video_bitrate)
    curr_audio_bitrate = int(args.audio_bitrate)

    # Create instance of app
    app = GSTWebRTCApp(stun_servers, turn_servers, enable_audio, curr_fps, args.encoder, curr_video_bitrate, curr_audio_bitrate)

    # [END main_setup]

    # Send the local sdp to signalling when offer is generated.
    app.on_sdp = signalling.send_sdp

    # Send ICE candidates to the signalling server.
    app.on_ice = signalling.send_ice

    # Set the remote SDP when received from signalling server.
    signalling.on_sdp = app.set_sdp

    # Set ICE candidates received from signalling server.
    signalling.on_ice = app.set_ice

    # Start the pipeline once the session is established.
    signalling.on_session = app.start_pipeline

    # Initialize the Xinput instance
    webrtc_input = WebRTCInput(args.uinput_mouse_socket, args.uinput_js_socket, args.enable_clipboard.lower())

    # Log message when data channel is open
    def data_channel_ready():
        logger.info(
            "opened peer data channel for user input to X11")

        app.send_framerate(app.framerate)
        app.send_video_bitrate(app.video_bitrate)
        app.send_audio_bitrate(app.audio_bitrate)
        app.send_audio_enabled(app.audio)
        app.send_resize_enabled(enable_resize)
        app.send_encoder(app.encoder)

    app.on_data_open = lambda: data_channel_ready()

    # Send incomming messages from data channel to input handler
    app.on_data_message = webrtc_input.on_message

    # Send video bitrate messages to app
    webrtc_input.on_video_encoder_bit_rate = lambda bitrate: set_json_app_argument(args.json_config, "video_bitrate", bitrate) and (app.set_video_bitrate(int(bitrate)))

    # Send audio bitrate messages to app
    webrtc_input.on_audio_encoder_bit_rate = lambda bitrate: set_json_app_argument(args.json_config, "audio_bitrate", bitrate) and app.set_audio_bitrate(int(bitrate))

    # Send pointer visibility setting to app
    webrtc_input.on_mouse_pointer_visible = lambda visible: app.set_pointer_visible(
        visible)

    # Send clipboard contents when requested
    webrtc_input.on_clipboard_read = lambda data: app.send_clipboard_data(data)

    # Write framerate arg to local config and then tell client to reload.
    def set_fps_handler(fps):
        set_json_app_argument(args.json_config, "framerate", fps)
        curr_fps = app.framerate
        app.set_framerate(fps)
        if fps != curr_fps:
            logger.warning("sending window reload to restart pipeline with new framerate")
            app.send_reload_window()
    webrtc_input.on_set_fps = lambda fps: set_fps_handler(fps)

    # Write audio enabled arg to local config and then tell client to reload.
    def enable_audio_handler(enabled):
        set_json_app_argument(args.json_config, "enable_audio", enabled)
        curr_audio = app.audio
        app.set_enable_audio(enabled)
        if enabled != curr_audio:
            app.send_reload_window()
    webrtc_input.on_set_enable_audio = lambda enabled: enable_audio_handler(enabled)

    # Handler for resize events.
    app.last_resize_success = True
    def on_resize_handler(res):
        # Trigger resize and reload if it changed.
        curr_res, new_res, _, __, ___ = get_new_res(res)
        if curr_res != new_res:
            if not app.last_resize_success:
                logger.warning("skipping resize because last resize failed.")
                return
            logger.warning("stopping ximagesrc")
            app.stop_ximagesrc()
            logger.warning("resizing display from {} to {}".format(curr_res, new_res))
            resize_display(res)
            app.start_ximagesrc()

    # Initial binding of enable resize handler.
    if enable_resize:
        webrtc_input.on_resize = on_resize_handler

    webrtc_input.on_ping_response = lambda latency: app.send_latency_time(latency)

    # Enable resize with resolution handler
    def enable_resize_handler(enabled, enable_res):
        set_json_app_argument(args.json_config, "enable_resize", enabled)
        if enabled:
            # Bind the handler
            webrtc_input.on_resize = on_resize_handler

            # Trigger resize and reload if it changed.
            on_resize_handler(enable_res)
        else:
            logger.info("removing handler for on_resize")
            webrtc_input.on_resize = lambda res: logger.warning("remote resize is disabled, skipping resize to %s" % res)

    webrtc_input.on_set_enable_resize = enable_resize_handler

    # Send client FPS to metrics
    webrtc_input.on_client_fps = lambda fps: metrics.set_fps(fps)

    # Send client latency to metrics
    webrtc_input.on_client_latency = lambda latency_ms: metrics.set_latency(latency_ms)

    # Initialize GPU monitor
    gpu_mon = GPUMonitor(enabled=args.encoder.startswith("nv"))

    # Send the GPU stats when available.
    def on_gpu_stats(load, memory_total, memory_used):
        app.send_gpu_stats(load, memory_total, memory_used)
        metrics.set_gpu_utilization(load * 100)

    gpu_mon.on_stats = on_gpu_stats

    # Initialize the system monitor
    system_mon = SystemMonitor()

    def on_sysmon_timer(t):
        webrtc_input.ping_start = t
        app.send_system_stats(system_mon.cpu_percent, system_mon.mem_total, system_mon.mem_used)
        app.send_ping(t)

    system_mon.on_timer = on_sysmon_timer

    # [START main_start]
    # Connect to the signalling server and process messages.
    loop = asyncio.get_event_loop()

    # Initialize the signaling and web server
    options = argparse.Namespace()
    options.addr = args.addr
    options.port = args.port
    options.enable_basic_auth = args.enable_basic_auth
    options.basic_auth_user = args.basic_auth_user
    options.basic_auth_password = args.basic_auth_password
    options.disable_ssl = True
    options.health = "/health"
    options.web_root = args.web_root
    options.keepalive_timeout = 30
    options.cert_path = None
    options.cert_restart = False
    options.rtc_config_file = args.rtc_config_json
    options.rtc_config = rtc_config
    options.turn_shared_secret = args.turn_shared_secret
    options.turn_host = args.turn_host
    options.turn_port = args.turn_port
    options.turn_auth_header_name = args.coturn_auth_header_name
    server = WebRTCSimpleServer(loop, options)

    # Callback method to update turn servers of a running pipeline.
    def mon_rtc_config(stun_servers, turn_servers, rtc_config):
        for turn_server in turn_servers:
            if app.webrtcbin:
                app.webrtcbin.emit("add-turn-server", turn_server)
        server.set_rtc_config(rtc_config)

    # Initialize periodic montior to refresh TURN RTC config when using shared secret.
    hmac_turn_mon = HMACRTCMonitor(
        args.turn_host,
        args.turn_port,
        args.turn_shared_secret,
        args.coturn_web_username,
        enabled=using_hmac_turn, period=60)
    hmac_turn_mon.on_rtc_config = mon_rtc_config

    # Initialize coturn RTC config monitor to periodically refresh the coturn RTC config.
    coturn_mon = CoturnRTCMonitor(
        args.coturn_web_uri,
        args.coturn_web_username,
        args.coturn_auth_header_name,
        enabled=using_coturn, period=60)
    coturn_mon.on_rtc_config = mon_rtc_config

    # Initialize file watcher for RTC config JSON file.
    rtc_file_mon = RTCConfigFileMonitor(
        rtc_file=args.rtc_config_json,
        enabled=using_rtc_config_json)
    rtc_file_mon.on_rtc_config = mon_rtc_config

    try:
        server.run()
        metrics.start()
        loop.run_until_complete(webrtc_input.connect())
        loop.run_in_executor(None, lambda: webrtc_input.start_clipboard())
        loop.run_in_executor(None, lambda: gpu_mon.start())
        loop.run_in_executor(None, lambda: hmac_turn_mon.start())
        loop.run_in_executor(None, lambda: coturn_mon.start())
        loop.run_in_executor(None, lambda: rtc_file_mon.start())
        loop.run_in_executor(None, lambda: system_mon.start())

        while True:
            loop.run_until_complete(signalling.connect())
            loop.run_until_complete(signalling.start())
            app.stop_pipeline()
    except Exception as e:
        logger.error("Caught exception: %s" % e)
        sys.exit(1)
    finally:
        webrtc_input.stop_clipboard()
        webrtc_input.disconnect()
        gpu_mon.stop()
        coturn_mon.stop()
        rtc_file_mon.stop()
        system_mon.stop()
        server.server.close()
        sys.exit(0)
    # [END main_start]

if __name__ == '__main__':
    main()
