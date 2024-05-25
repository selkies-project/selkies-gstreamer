#!/bin/sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#   Copyright 2019 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

set -e -x

export EXTERNAL_IP="${EXTERNAL_IP:-$(detect_external_ip)}"

# NOTE That that listening IP must be bound to only the IPs you will be responding to.
# Binding to the wrong IP(s) can result in connectivity issues that are difficult to trace.
# Typically $(hostname -i) will return the primary IP to listen on.

turnserver \
    --verbose \
    --no-tls \
    --listening-ip=$(hostname -i) \
    --listening-port=${TURN_PORT:-80} \
    --aux-server="$(hostname -i):${TURN_ALT_PORT:-443}" \
    --external-ip="${EXTERNAL_IP?missing env}" \
    --realm=${TURN_REALM:-example.com} \
    --use-auth-secret \
    --static-auth-secret=${TURN_SHARED_SECRET:-changeme} \
    --rest-api-separator="-" \
    --channel-lifetime=${TURN_CHANNEL_LIFETIME:-"-1"} \
    --min-port=${TURN_MIN_PORT:-49152} \
    --max-port=${TURN_MAX_PORT:-65535} \
    --prometheus ${EXTRA_ARGS}
