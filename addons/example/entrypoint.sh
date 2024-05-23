#!/bin/bash -ex

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Setup coturn server
echo "#!/bin/bash -ex\n\
exec turnserver\n\
    --verbose\n\
    --listening-ip=0.0.0.0\n\
    --listening-port=\${SELKIES_TURN_PORT:-3478}\n\
    --realm=\${TURN_REALM:-example.com}\n\
    --min-port=\${TURN_MIN_PORT:-49152}\n\
    --max-port=\${TURN_MAX_PORT:-65535}\n\
    --lt-cred-mech\n\
    --user selkies:\${TURN_RANDOM_PASSWORD}\n\
    --no-cli\n\
    --allow-loopback-peers\n\
    --db /tmp/coturn-turndb\n\
    \${EXTRA_ARGS} \$@\n\
" > /etc/start-turnserver.sh

chmod +x /etc/start-turnserver.sh

# Create and modify permissions of XDG_RUNTIME_DIR
mkdir -pm700 /tmp/runtime-user
chown -f ubuntu:ubuntu /tmp/runtime-user
chmod -f 700 /tmp/runtime-user

export DISPLAY="${DISPLAY:-:0}"

# Configure joystick interposer
export LD_PRELOAD="selkies_joystick_interposer.so${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
mkdir -pm777 /dev/input || sudo-root mkdir -pm777 /dev/input || echo 'Failed to create joystick interposer directory'
touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3 || sudo-root touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3 || echo 'Failed to create joystick interposer devices'

# Export environment variables requried for selkies-gstreamer process
export SELKIES_ENCODER=${SELKIES_ENCODER:-x264enc}
export SELKIES_ENABLE_RESIZE=${SELKIES_ENABLE_RESIZE:-true}

if ( [ -z "${SELKIES_TURN_USERNAME}" ] || [ -z "${SELKIES_TURN_PASSWORD}" ] ) && [ -z "${SELKIES_TURN_SHARED_SECRET}" ] || [ -z "${SELKIES_TURN_HOST}" ] || [ -z "${SELKIES_TURN_PORT}" ]; then
  TURN_RANDOM_PASSWORD="$(tr -dc A-Za-z0-9 </dev/urandom | head -c 24)"
  export TURN_RANDOM_PASSWORD=${TURN_RANDOM_PASSWORD}
  /etc/start-turnserver.sh &
  export SELKIES_TURN_HOST=$(curl -fsSL checkip.amazonaws.com)
  export SELKIES_TURN_PORT=${SELKIES_TURN_PORT:-3478}
  export SELKIES_TURN_USERNAME=selkies
  export SELKIES_TURN_PASSWORD=${TURN_RANDOM_PASSWORD}
fi
export SELKIES_TURN_PROTOCOL=${SELKIES_TURN_PROTOCOL:-tcp}

# Start X server with required extensions
Xvfb -screen :0 8192x4096x24 +extension "COMPOSITE" +extension "DAMAGE" +extension "GLX" +extension "RANDR" +extension "RENDER" +extension "MIT-SHM" +extension "XFIXES" +extension "XTEST" +iglx +render -nolisten "tcp" -noreset -shmem >/tmp/Xvfb.log 2>&1 &

# Wait for X server to start
until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done
echo 'X Server is ready'

# Pulse-server socket location
export PULSE_SERVER=unix:/tmp/runtime-user/pulse/native

# Start Xfce4 Desktop session
[ "${START_XFCE4:-true}" = "true" ] && rm -rf ~/.config/xfce4 && vglrun -d "${VGL_DISPLAY:-egl}" +wm xfce4-session &

read