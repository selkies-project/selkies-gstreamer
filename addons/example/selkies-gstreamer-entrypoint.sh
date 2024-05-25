#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

set -e

# Set default display
export DISPLAY="${DISPLAY:-:0}"
# PulseAudio server socket path
export PULSE_SERVER="unix:${XDG_RUNTIME_DIR}/pulse/native"

# Source environment for GStreamer
. /opt/gstreamer/gst-env

# Export environment variables required for Selkies-GStreamer
export GST_DEBUG="${GST_DEBUG:-*:2}"
export GSTREAMER_PATH=/opt/gstreamer

export SELKIES_ENCODER="${SELKIES_ENCODER:-x264enc}"
export SELKIES_ENABLE_RESIZE="${SELKIES_ENABLE_RESIZE:-true}"
if ( [ -z "${SELKIES_TURN_USERNAME}" ] || [ -z "${SELKIES_TURN_PASSWORD}" ] ) && [ -z "${SELKIES_TURN_SHARED_SECRET}" ] || [ -z "${SELKIES_TURN_HOST}" ] || [ -z "${SELKIES_TURN_PORT}" ]; then
  export TURN_RANDOM_PASSWORD="$(tr -dc A-Za-z0-9 </dev/urandom | head -c 24)"
  export SELKIES_TURN_HOST="$(curl -fsSL checkip.amazonaws.com)"
  export SELKIES_TURN_PORT="3478"
  export SELKIES_TURN_USERNAME="selkies"
  export SELKIES_TURN_PASSWORD="${TURN_RANDOM_PASSWORD}"
  /etc/start-turnserver.sh &
fi
export SELKIES_TURN_PROTOCOL="${SELKIES_TURN_PROTOCOL:-tcp}"

# Set password for basic authentication
if [ "${ENABLE_BASIC_AUTH,,}" != "false" ] && [ -z "${BASIC_AUTH_PASSWORD}" ]; then export BASIC_AUTH_PASSWORD="${PASSWD}"; fi

# Wait for X server to start
echo "Waiting for X socket"
until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done
echo "X socket is ready"

# Clear the cache registry
rm -rf "${HOME}/.cache/gstreamer-1.0"

# Preset the resolution
selkies-gstreamer-resize 1920x1080

# Start the selkies-gstreamer WebRTC HTML5 remote desktop application
selkies-gstreamer \
    --addr="0.0.0.0" \
    --port="8080" \
    $@
