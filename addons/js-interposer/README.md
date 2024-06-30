# Selkies Joystick (Gamepad) Interposer

An `LD_PRELOAD` library for interposing application calls to open a Linux joystick/gamepad device and pass data through a unix domain socket.

This allows the Selkies-GStreamer WebRTC interface to pass gamepad events over the WebRTC `RTCDataChannel`, and translate them to joystick/gamepad events to emulate devices without requiring access to /dev/input/js0 or depending on kernel modules including `uinput`.

## Compiling

```bash
gcc -shared -fPIC -ldl -o selkies_joystick_interposer.so joystick_interposer.c
```

To compile the `i386` library for Wine and other 32-bit packages, add `-m32` with the `gcc-multilib` package installed.

## Installing

1. Install to your library path (may be `/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so` and `/usr/lib/i386-linux-gnu/selkies_joystick_interposer.so` for Ubuntu), also available as a tarball or `.deb` installer.

If using Wine with `x86_64`, both `/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so` and `/usr/lib/i386-linux-gnu/selkies_joystick_interposer.so` are likely required.

2. The following paths are required to exist for the Joystick Interposer to pass the joystick/gamepad input to various applications:

```bash
sudo mkdir -pm755 /dev/input
sudo touch /dev/input/js0 /dev/input/js1 /dev/input/js2 /dev/input/js3
```

3. Use the below command before running your target application as well as Selkies-GStreamer for the interposer library to intercept joystick/gamepad events (the single quotes are required in the first line).

```bash
export SELKIES_INTERPOSER='/usr/$LIB/selkies_joystick_interposer.so'
export LD_PRELOAD="${SELKIES_INTERPOSER}${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
```

Otherwise, if you only need one architecture, the below is an equivalent command.

```bash
export LD_PRELOAD="/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so${LD_PRELOAD:+:${LD_PRELOAD}}"
export SDL_JOYSTICK_DEVICE=/dev/input/js0
```

You can replace `/usr/$LIB/selkies_joystick_interposer.so` with any non-root path of your choice if using the `.tar.gz` tarball. Make sure the correct `selkies_joystick_interposer.so` is installed in that path.

## Testing

1. Start the Python joystick emulator:

```bash
python3 js-interposer-test.py
```

This creates a new unix domain socket at `/tmp/selkies_js0.sock` and simulates joystick button presses and axis motion when a connection from the interposer is detected.

2. Run `jstest` with the interposer library (`LD_PRELOAD` environment variable path can be set as adequate):

```bash
LD_PRELOAD='/usr/$LIB/selkies_joystick_interposer.so' jstest /dev/input/js0
```
