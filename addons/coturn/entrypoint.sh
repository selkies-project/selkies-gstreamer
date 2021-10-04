#!/bin/sh

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

set -e
set -x

export EXTERNAL_IP="${EXTERNAL_IP:-$(detect_external_ip)}"

# NOTE That that listening IP must be bound to only the IPs you will be responding to.
# Binding to the wrong IP(s) can result in connectivity issues that are difficult to trace.
# Typically $(hostname -i) will return the primary IP to listen on.

turnserver \
    --verbose \
    --listening-ip=$(hostname -i) \
    --listening-port=${TURN_PORT:-3478} \
    --external-ip="${EXTERNAL_IP?missing env}" \
    --realm=${TURN_REALM:-example.com} \
    --use-auth-secret \
    --static-auth-secret=${TURN_SHARED_SECRET:-changeme} \
    --rest-api-separator="-" \
    --channel-lifetime=${TURN_CHANNEL_LIFETIME:-"-1"} \
    --min-port=${TURN_MIN_PORT:-25000} \
    --max-port=${TURN_MAX_PORT:-25004} ${EXTRA_ARGS}