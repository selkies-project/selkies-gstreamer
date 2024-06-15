# Selkies Joystick (Gamepad) Interposer

An `LD_PRELOAD` library for interposing application calls to open a Linux joystick/gamepad device and pass data through a unix domain socket.

This allows the Selkies-GStreamer WebRTC interface to pass gamepad events over the WebRTC `RTCDataChannel`, and translate them to joystick/gamepad events to emulate devices without requiring access to /dev/input/js0 or depending on kernel modules including `uinput`.

## Compiling and Installing

```bash
gcc -shared -fPIC -ldl -o selkies_joystick_interposer.so joystick_interposer.c
```

To compile the `i386` library for Wine and other 32-bit packages, add `-m32` with the `gcc-multilib` package installed.

Install to your library path (may be `/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so` and `/usr/lib/i386-linux-gnu/selkies_joystick_interposer.so` for Ubuntu), also available as a tarball or `.deb` installer.

If using Wine with x86_64, both `/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so` and `/usr/lib/i386-linux-gnu/selkies_joystick_interposer.so` are likely required.

Use the below command before running your target application as well as Selkies-GStreamer for the interposer library to intercept joystick/gamepad events (the single quotes are required in the first line).

```bash
export SELKIES_INTERPOSER='/usr/$LIB/selkies_joystick_interposer.so'
export LD_PRELOAD="${SELKIES_INTERPOSER}${LD_PRELOAD:+:${LD_PRELOAD}}"
```

Otherwise, if you only need one architecture, the below is an equivalent command.

```bash
export LD_PRELOAD="/usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so${LD_PRELOAD:+:${LD_PRELOAD}}"
```

## Testing

1. Start the Python joystick emulator:

```bash
python3 js-interposer-test.py
```

This creates a new unix domain socket at `/tmp/selkies_js0.sock` and simulates joystick button presses and axis motion when a connection from the interposer is detected.

2. Run `jstest` with the interposer library:

```bash
LD_PRELOAD=${PWD}/selkies_joystick_interposer.so jstest /dev/input/js0
```
