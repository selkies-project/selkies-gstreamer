# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from flask import Flask, request
import os, time, hmac, hashlib, base64, json
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def turn_rest():
    shared_secret = os.environ.get('TURN_SHARED_SECRET')
    turn_host = os.environ.get('TURN_HOST')
    turn_port = os.environ.get('TURN_PORT')

    turn_tls = request.values.get('tls').lower() == 'true' or os.environ.get('TURN_TLS').lower() == 'true'
    protocol = request.values.get('protocol').lower() or os.environ.get('TURN_PROTOCOL').lower() or 'tcp'
    if protocol.lower() != 'udp':
        protocol = 'tcp'
    service_input = request.values.get('service') or 'turn'
    username_input = request.values.get('username') or request.headers.get('x-auth-user') or 'turn-rest'

    # Sanitize user for credential compatibility
    user = username_input.replace(":", "-")

    # credential expires in 24hrs
    expiry_hour = 24

    exp = int(time.time()) + expiry_hour * 3600
    username = "{}:{}".format(exp, user)

    # Generate HMAC credential.
    hashed = hmac.new(bytes(shared_secret, "utf-8"), bytes(username, "utf-8"), hashlib.sha1).digest()
    password = base64.b64encode(hashed).decode()

    rtc_config = {}
    rtc_config["lifetimeDuration"] = "{}s".format(expiry_hour * 3600)
    rtc_config["blockStatus"] = "NOT_BLOCKED"
    rtc_config["iceTransportPolicy"] = "all"
    rtc_config["iceServers"] = []
    rtc_config["iceServers"].append({
        "urls": [
            "stun:{}:{}".format(turn_host, turn_port)
        ]
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
