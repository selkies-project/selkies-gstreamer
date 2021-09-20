#!/bin/bash

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

echo "Waiting for X server"
until [[ -e /var/run/appconfig/xserver_ready ]]; do sleep 1; done
[[ -f /var/run/appconfig/.Xauthority ]] && cp /var/run/appconfig/.Xauthority ${HOME}/
echo "X server is ready"

echo "Waiting for session to start"
until [[ $(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: ${BROKER_COOKIE?}" -H "Host: ${BROKER_HOST?}" ${BROKER_SESSION_ENDPOINT?}) -eq 200 ]]; do
    sleep 2
done
SESSION_DATA=$(curl -s -H "Cookie: ${BROKER_COOKIE?}" -H "Host: ${BROKER_HOST?}" ${BROKER_SESSION_ENDPOINT?})
export DIR_TIMESTAMP=$(jq -r '.session_start' <<< "$SESSION_DATA")
export VDI_USER=$(jq -r '.user' <<< "$SESSION_DATA")
echo "Session is ready, user=$VDI_USER, session_start=$DIR_TIMESTAMP"

SECONDS_PER_FILE=${SECONDS_PER_FILE:-60}
# Convert to ns
((max_size_time=SECONDS_PER_FILE*1000000000))

MAX_FILES=${MAX_FILES:-0}
RECORDING_TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
DEST_DIR=/tmp/recording/${VDI_USER}/${DIR_TIMESTAMP}/data/${VDI_USER}/${VDI_APP}/${RECORDING_TIMESTAMP}
mkdir -p "$DEST_DIR"

# Note directory for cleanup, called by lifecycle hook.
echo "/tmp/recording/${VDI_USER}/${DIR_TIMESTAMP}" > /tmp/cleanup_dir

echo "INFO: Saving recordings to: ${DEST_DIR}"

# Set the max window size.
# If window size being recorded is larger than this, gstreamer will crash.
# Setting the limits here will force the window into these dimensions before starting the recording.
IFS='x' read -ra maxres <<< $(xrandr | head | grep -o "maximum.*" | sed 's/maximum//' | tr -d ' ')
MAX_WINDOW_WIDTH=${maxres[0]}
MAX_WINDOW_HEIGHT=${maxres[1]}

echo "INFO: Maximum capture resolution: ${MAX_WINDOW_WIDTH}x${MAX_WINDOW_HEIGHT}, larger windows will be resized to fit."

if [[ "${VDI_enableXpra}" == "true" ]]; then
    # Capture every window into separate files.
    declare -a xids
    while true; do
        IFS="," read -ra xids <<< $(xprop -root | grep "^_NET_CLIENT_LIST(WINDOW)" | cut -d# -f2 | tr -d ' ')

        for xid in ${xids[*]}; do
            # Gather window info
            XWININFO=$(xwininfo -id $xid)
            XPROP_DATA=$(xprop -id $xid)

            # Extract process name from window props.
            wm_class=$(grep "^WM_CLASS" <<< "${XPROP_DATA}" | cut -d= -f2 | tr -d ' ' | cut -d, -f1 | tr -d '"')
            [[ -z "${wm_class}" ]] && wm_class="null-wm_class"

            # Get the current geometry of the window.
            CURR_SIZE=$(grep "geometry" <<< "${XWININFO}" | cut -d' ' -f4 | cut -d'+' -f1)

            # Compute max width and height
            IFS="x" read -ra dim <<< "${CURR_SIZE}"
            curr_w=${dim[0]}
            curr_h=${dim[1]}
            new_w=$(( curr_w > MAX_WINDOW_WIDTH ? MAX_WINDOW_WIDTH : curr_w ))
            new_h=$(( curr_h > MAX_WINDOW_HEIGHT ? MAX_WINDOW_HEIGHT : curr_h ))
            if [[ "${CURR_SIZE}" != "${new_w}x${new_h}" ]]; then
                echo "WARN: window size for '${wm_class}' (${xid}): ${CURR_SIZE} is outside max recording dimensions of ${MAX_WINDOW_WIDTH}x${MAX_WINDOW_HEIGHT}, resizing."
                xdotool windowsize $xid $new_w $new_h
                continue
            fi
            
            # Extract the Map State from the window info, if window is not mapped, it cannot be recorded. 
            # Window is mapped once Xpra has lauched and reparented all entrypoint windows.
            MAP_STATE=$(echo "${XWININFO}" | grep "Map State" | cut -d: -f2 | tr -d ' ')

            # Recording is started if it's not currently running and is visible or if the window size has changed.
            START_REC=false

            CURR_PID=$(pgrep -f gst-launch-1.0.*xid=$xid)
            if [[ ${CURR_PID} ]]; then
                # Check if window size has changed. If so, kill and restart the stream.
                # Note that resizing the window down crashes the stream: https://gitlab.freedesktop.org/gstreamer/gst-plugins-good/issues/453
                REC_SIZE=$(cat /proc/${CURR_PID}/environ | tr '\0' '\n' | grep WINDOW_SIZE | cut -d'=' -f2)
                if [[ "${REC_SIZE}" != "${CURR_SIZE}" ]]; then
                    echo "INFO: window size for '${wm_class}' (${xid}) changed from ${REC_SIZE} to ${CURR_SIZE}, restarting recording."
                    kill ${CURR_PID}
                    START_REC=true
                fi
            elif [[ "${MAP_STATE}" == "IsViewable" ]]; then
                START_REC=true
            else
                echo "WARN: window '$wm_class' ($xid) is unviewable per xwininfo Map State, cannot start recording."
            fi

            if [[ ${START_REC} == true ]]; then
                # Start new recording.
                ts=$(date +%s)
                
                # Save props to file to save for additional metadata.
                echo "${XPROP_DATA}" > ${DEST_DIR?}/stream_${ts}_${wm_class}_${xid}_xprop.txt

                # Inject window resolution to gst-launch-1.0 environment so that it can be compared later to detect resizing.
                export WINDOW_SIZE="${CURR_SIZE}"

                echo "INFO: starting recording for ${wm_class}, xid=${xid}, ts=${ts}, geometry=${WINDOW_SIZE}"

                gst-launch-1.0 \
                    ximagesrc xid=${xid} show-pointer=1 remote=1 use-damage=0 \
                    ! video/x-raw,framerate=${REC_VIDEO_FRAMERATE:-5}/1 \
                    ! videoconvert ! x264enc bitrate=${REC_VIDEO_BITRATE:-500} speed-preset=3 \
                    ! splitmuxsink muxer=mp4mux use-robust-muxing=1 async-finalize=1 muxer-properties=properties,reserved-moov-update-period=1000000000,reserved-max-duration=10000000000 max-files=${MAX_FILES?} max-size-time=${max_size_time?} location=${DEST_DIR?}/stream_${ts}_${wm_class}_${xid}_${CURR_SIZE}_%04d.mp4 >/tmp/recording/stream_${ts}_${wm_class}_${xid}.log 2>&1 &
            fi                
        done

        # Delay long enough for recordings that have been killed to shutdown
        # If too short, the pgrep will detect the terminating process and think it's still active.
        sleep 5
    done
else
    # Full desktop capture
    REC_RES=$(xdpyinfo | awk '/dimensions/{print $2}')
    while true; do
        START_REC=false
        CURR_PID=$(pgrep -f gst-launch-1.0)
        CURR_RES=$(xdpyinfo | awk '/dimensions/{print $2}')

        if [[ ${CURR_PID} ]]; then
            # Recording is active, check for resolution change.
            if [[ "${REC_RES}" != "${CURR_RES}" ]]; then
                echo "WARN: resolution changed from ${REC_RES} to ${CURR_RES}, restarting recording."
                kill ${CURR_PID}
                START_REC=true
            fi
        else
            # Not yet running or terminated, restart
            START_REC=true
        fi

        if [[ ${START_REC} == true ]]; then
            ts=$(date +%s)
            REC_RES=$(xdpyinfo | awk '/dimensions/{print $2}')
            echo "INFO: Starting recording with timestamp ${ts} at resolution of ${REC_RES}"

            if command -v nvidia-smi >/dev/null; then
                # Use hardware encoder
                gst-launch-1.0 \
                    ximagesrc show-pointer=1 remote=1 blocksize=16384 use-damage=0 \
                    ! video/x-raw,framerate=${REC_VIDEO_FRAMERATE:-15}/1 \
                    ! cudaupload ! cudaconvert ! video/x-raw\(memory:CUDAMemory\),format=I420 ! nvh264enc bitrate=${REC_VIDEO_BITRATE:-500} rc-mode=cbr preset=default \
                    ! h264parse \
                    ! splitmuxsink muxer=mp4mux use-robust-muxing=1 async-finalize=1 muxer-properties=properties,reserved-moov-update-period=1000000000,reserved-max-duration=10000000000 max-files=${MAX_FILES?} max-size-time=${max_size_time?} location=${DEST_DIR?}/stream_${ts}_${REC_RES}_%04d.mp4 >/tmp/recording/recording_${ts}.log 2>&1 &
            else
                # Use software encoder
                gst-launch-1.0 \
                    ximagesrc show-pointer=1 remote=1 use-damage=0 \
                    ! video/x-raw,framerate=${REC_VIDEO_FRAMERATE:-5}/1 \
                    ! videoconvert ! x264enc bitrate=${REC_VIDEO_BITRATE:-500} speed-preset=3 \
                    ! splitmuxsink muxer=mp4mux use-robust-muxing=1 async-finalize=1 muxer-properties=properties,reserved-moov-update-period=1000000000,reserved-max-duration=10000000000 max-files=${MAX_FILES?} max-size-time=${max_size_time?} location=${DEST_DIR?}/stream_${ts}_${REC_RES}_%04d.mp4 >/tmp/recording/recording_${ts}.log 2>&1 &
            fi
        fi

        sleep 5
    done
fi

# Cleanup on exit
trap '{ kill $(pgrep gst-launch-1.0); }' EXIT