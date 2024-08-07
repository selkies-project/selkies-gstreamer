# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from flask import Flask, request
import os, time, hmac, hashlib, base64, json

shared_secret = os.environ.get('TURN_SHARED_SECRET', 'openrelayprojectsecret')
turn_host = os.environ.get('TURN_HOST', 'staticauth.openrelay.metered.ca')
if turn_host:
    turn_host = turn_host.lower()
turn_port = os.environ.get('TURN_PORT', '443')
if not turn_port.isdigit():
    turn_port = '3478'
stun_host = os.environ.get('STUN_HOST', turn_host)
if stun_host:
    stun_host = stun_host.lower()
stun_port = os.environ.get('STUN_PORT', turn_port)
if not stun_port.isdigit():
    stun_host, stun_port = 'stun.l.google.com', '19302'
turn_protocol_default = os.environ.get('TURN_PROTOCOL', 'udp')
turn_tls_default = os.environ.get('TURN_TLS', 'false')

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def turn_rest():
    service_input = request.values.get('service') or 'turn'
    if service_input:
        service_input = service_input.lower()

    username_input = request.values.get('username') or request.headers.get('x-auth-user') or request.headers.get('x-turn-username') or 'turn-rest'
    if username_input:
        username_input = username_input.lower()
    protocol = request.values.get('protocol') or request.headers.get('x-turn-protocol') or turn_protocol_default
    if protocol.lower() != 'tcp':
        protocol = 'udp'
    turn_tls = request.values.get('tls') or request.headers.get('x-turn-tls') or turn_tls_default
    if turn_tls.lower() == 'true':
        turn_tls = True
    else:
        turn_tls = False

    # Sanitize user for credential compatibility
    user = username_input.replace(":", "-")

    # Credential expires in 24 hours
    expiry_hour = 24

    exp = int(time.time()) + expiry_hour * 3600
    username = "{}:{}".format(exp, user)

    # Generate HMAC credential
    hashed = hmac.new(bytes(shared_secret, "utf-8"), bytes(username, "utf-8"), hashlib.sha1).digest()
    password = base64.b64encode(hashed).decode()

    # Configure STUN servers
    stun_list = ["stun:{}:{}".format(turn_host, turn_port)]
    if stun_host is not None and stun_port is not None and (stun_host != turn_host or str(stun_port) != str(turn_port)):
        stun_list.insert(0, "stun:{}:{}".format(stun_host, stun_port))
    if stun_host != "stun.l.google.com" or (str(stun_port) != "19302"):
        stun_list.append("stun:stun.l.google.com:19302")

    rtc_config = {}
    rtc_config["lifetimeDuration"] = "{}s".format(expiry_hour * 3600)
    rtc_config["blockStatus"] = "NOT_BLOCKED"
    rtc_config["iceTransportPolicy"] = "all"
    rtc_config["iceServers"] = []
    rtc_config["iceServers"].append({
        "urls": stun_list
    })
    rtc_config["iceServers"].append({
        "urls": [
            "{}:{}:{}?transport={}".format('turns' if turn_tls else 'turn', turn_host, turn_port, protocol)
        ],
        "username": username,
        "credential": password
    })

    return json.dumps(rtc_config, indent=2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8008")
