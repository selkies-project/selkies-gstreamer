export DISPLAY=:0
unset WAYLAND_DISPLAY
export XSERVER=${XSERVER:-XVFB}

SCRIPT_DIR=$(dirname $(readlink -f $0))

function cleanup() {
    kill -9 $(pidof turnserver) 1>/dev/null 2>&1|| true
    pgrep -af '.*selkies-gstreamer.*' | cut -d' ' -f1 | xargs kill -9 1>/dev/null 2>&1|| true
    pgrep -afi '.*xfce4.*' | cut -d' ' -f1 | xargs kill -9 1>/dev/null 2>&1|| true
    pgrep -afi '.*fluxbox.*' | cut -d' ' -f1 | xargs kill -9 1>/dev/null 2>&1|| true
    sudo /usr/bin/pulseaudio -k 1>/dev/null 2>&1  || true
    kill -9 $(pidof Xvfb) 1>/dev/null 2>&1 || true
    exit
}
trap cleanup SIGINT SIGKILL EXIT

# Start Xvfb Xserver
if [ "${XSERVER}" = "XVFB" ]; then
    Xvfb -screen :0 8192x4096x24 +extension RANDR +extension GLX +extension MIT-SHM -nolisten tcp -noreset -shmem 2>&1 >/tmp/Xvfb.log &
fi

# Wait for X11 to start
echo "Waiting for X socket"
until [ -S "/tmp/.X11-unix/X${DISPLAY/:/}" ]; do sleep 1; done
echo "X socket is ready"

# Disable screen saver
xset s off
# Disable screen blanking
xset s noblank
# Disable power management
xset -dpms

# Start pulse audio server
export PULSE_SERVER=tcp:127.0.0.1:4713
sudo /usr/bin/pulseaudio -k >/dev/null 2>&1
sudo /usr/bin/pulseaudio --daemonize --system --verbose --log-target=file:/tmp/pulseaudio.log --realtime=true --disallow-exit -L 'module-native-protocol-tcp auth-ip-acl=127.0.0.0/8 port=4713 auth-anonymous=1'

# Create /dev/input/jsX if they don't already exists
sudo mkdir -p /dev/input
sudo touch /dev/input/{js0,js1,js2,js3}

# If installed, add the joystick interposer to the LD_PRELOAD environment
if [ -e /usr/lib/x86_64-linux-gnu/selkies-js-interposer/joystick_interposer.so ]; then
    export SELKIES_INTERPOSER='/usr/$LIB/selkies-js-interposer/joystick_interposer.so'
    export LD_PRELOAD="${LD_PRELOAD}:${SELKIES_INTERPOSER}"
    export SDL_JOYSTICK_DEVICE=/dev/input/js0
fi

# Start desktop environment
case ${DESKTOP:-XFCE} in
    FLUXBOX)
        startfluxbox &
        ;;
    XFCE)
        xfce4-session &
        ;;
    *)
        echo "WARN: Unsupported DESTKOP: '${DESKTOP}'"
        ;;
esac

# Source gstreamer environment
. /opt/gstreamer/gst-env

# Start turnserver
${SCRIPT_DIR}/start-turnserver.sh &

# Start Selkies
selkies-gstreamer-resize 1920x1080
selkies-gstreamer \
    --addr="0.0.0.0" \
    --port="${WEB_PORT:-6080}" \
    --metrics_port=${WEBRTC_METRICS_PORT:-19090} \
    --cursor_size=${WEBRTC_CURSOR_SIZE:-"-1"} \
    --enable_resize=${WEBRTC_ENABLE_RESIZE:-true} \
    --turn_host=${TURN_HOST:-localhost} \
    --turn_port=${TURN_PORT:-3478} \
    --turn_username=${TURN_USERNAME:-selkies} \
    --turn_password=${TURN_PASSWORD:-selkies} \
    --turn_protocol=${TURN_PROTOCOL:-tcp} \
    $@
