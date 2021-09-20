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

from webrtc_input import WebRTCInput
from webrtc_signalling import WebRTCSignalling, WebRTCSignallingErrorNoPeer
from gstwebrtc_app import GSTWebRTCApp
from gpu_monitor import GPUMonitor
from system_monitor import SystemMonitor
from metrics import Metrics
from resize import resize_display


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
    auth_headers = {
        auth_header_name: user
    }

    conn.request("GET", parsed_uri.path, headers=auth_headers)
    resp = conn.getresponse()
    if resp.status >= 400:
        raise Exception(resp.reason)

    ice_servers = json.loads(resp.read())['iceServers']
    stun = turn = ice_servers[0]['urls'][0]
    stun_host = stun.split(":")[1]
    stun_port = stun.split(":")[2].split("?")[0]

    stun_uri = "stun://%s:%s" % (
        stun_host,
        stun_port
    )

    turn_uris = []
    for turn in ice_servers[1]['urls']:
        turn_host = turn.split(':')[1]
        turn_port = turn.split(':')[2].split('?')[0]
        turn_user = ice_servers[1]['username']
        turn_password = ice_servers[1]['credential']

        turn_uri = "turn://%s:%s@%s:%s" % (
            urllib.parse.quote(turn_user, safe=""),
            urllib.parse.quote(turn_password, safe=""),
            turn_host,
            turn_port
        )

        turn_uris.append(turn_uri)

    return stun_uri, turn_uris

def wait_for_app_ready(ready_file, app_auto_init = True):
    """Wait for streaming app ready signal.

    returns when either app_auto_init is True OR the file at ready_file exists.

    Keyword Arguments:
        app_auto_init {bool} -- skip wait for appready file (default: {True})
    """

    logging.info("Waiting for streaming app ready")
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
    parser.add_argument('--server',
                        default=os.environ.get(
                            'SIGNALLING_SERVER', 'ws://127.0.0.1:8080'),
                        help='Signalling server to connect to, default: "ws://127.0.0.1:8080"')
    parser.add_argument('--coturn_web_uri',
                        default=os.environ.get(
                            'COTURN_WEB_URI', 'http://localhost:8081'),
                        help='URI for coturn REST API service, example: http://localhost:8081')
    parser.add_argument('--coturn_web_username',
                        default=os.environ.get(
                            'COTURN_WEB_USERNAME', socket.gethostname()),
                        help='URI for coturn REST API service, default is the system hostname')
    parser.add_argument('--coturn_auth_header_name',
                        default=os.environ.get(
                            'COTURN_AUTH_HEADER_NAME', 'x-auth-user'),
                        help='header name to pass user to coturn web service')
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
            logging.error("failed to load json config from %s: %s" % (args.json_config, str(e)))

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

    # Initialize the signalling instance
    signalling = WebRTCSignalling(args.server, my_id, peer_id)

    # Handle errors from the signalling server.
    async def on_signalling_error(e):
        if isinstance(e, WebRTCSignallingErrorNoPeer):
            # Waiting for peer to connect, retry in 2 seconds.
            time.sleep(2)
            await signalling.setup_call()
        else:
            logging.error("signalling eror: %s", str(e))
    signalling.on_error = on_signalling_error

    # After connecting, attempt to setup call to peer.
    signalling.on_connect = signalling.setup_call

    # [START main_setup]
    # Fetch the turn server and credentials
    stun_server, turn_servers = fetch_coturn(
        args.coturn_web_uri, args.coturn_web_username, args.coturn_auth_header_name)

    # Extract args
    enable_audio = args.enable_audio == "true"
    enable_resize = args.enable_resize == "true"
    curr_fps = int(args.framerate)
    curr_video_bitrate = int(args.video_bitrate)
    curr_audio_bitrate = int(args.audio_bitrate)

    # Create instance of app
    app = GSTWebRTCApp(stun_server, turn_servers, args.enable_audio == "true", curr_fps, args.encoder, curr_video_bitrate, curr_audio_bitrate)

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
        logging.info(
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
    webrtc_input.on_set_fps = lambda fps: set_json_app_argument(args.json_config, "framerate", fps) and (fps != curr_fps) and app.send_reload_window() 

    # Write audio enabled arg to local config and then tell client to reload.
    webrtc_input.on_set_enable_audio = lambda enabled: set_json_app_argument(args.json_config, "enable_audio", enabled) and (enabled != enable_audio) and app.send_reload_window()

    # Initial binding of enable resize handler.
    if enable_resize:
        webrtc_input.on_resize = lambda res: resize_display(res) and app.send_reload_window()

    webrtc_input.on_ping_response = lambda latency: app.send_latency_time(latency)

    # Enable resize with resolution handler
    def enable_resize_handler(enabled, enable_res):
        set_json_app_argument(args.json_config, "enable_resize", enabled)
        if enabled:
            # Bind the handler
            webrtc_input.on_resize = lambda res: resize_display(res) and app.send_reload_window()

            # Trigger resize and reload if it changed.
            if resize_display(enable_res):
                app.send_reload_window()
        else:
            logging.info("removing handler for on_resize")
            webrtc_input.on_resize = lambda res: logging.warning("remote resize is disabled, skipping resize to %s" % res)

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
    try:
        metrics.start()
        loop.run_until_complete(webrtc_input.connect())
        loop.run_in_executor(None, lambda: webrtc_input.start_clipboard())
        loop.run_in_executor(None, lambda: gpu_mon.start())
        loop.run_in_executor(None, lambda: system_mon.start())
        loop.run_until_complete(signalling.connect())
        loop.run_until_complete(signalling.start())
    except Exception as e:
        logging.error("Caught exception: %s" % e)
        sys.exit(1)
    finally:
        webrtc_input.stop_clipboard()
        webrtc_input.disconnect()
        gpu_mon.stop()
        system_mon.stop()
        sys.exit(0)
    # [END main_start]

if __name__ == '__main__':
    main()