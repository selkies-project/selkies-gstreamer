#!/bin/bash

exec turnserver \
    --verbose \
    --no-tls \
    --listening-ip=0.0.0.0 \
    --listening-port=${TURN_PORT:-3478} \
    --realm=${TURN_REALM:-example.com} \
    --channel-lifetime=${TURN_CHANNEL_LIFETIME:-"-1"} \
    --min-port=${TURN_MIN_PORT:-49152} \
    --max-port=${TURN_MAX_PORT:-65535} \
    --user selkies:selkies \
    --no-cli \
    --cli-password selkies \
    --allow-loopback-peers \
    --db ${HOME}/.config/turndb \
    --pidfile ${HOME}/.config/turnserver.pid \
    ${EXTRA_ARGS} $@
