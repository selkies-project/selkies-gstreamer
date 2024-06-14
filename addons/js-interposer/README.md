# Selkies Joystick (Gamepad) Interposer

`LD_PRELOAD` library for interposing application calls to open a Linux joystick device and pass data via a unix domain socket.

This allows the Selkies-GStreamer WebRTC interface to pass gamepad events over `RTCDataChannel`, and translate them to joystick events without requiring access to /dev/input/js0 or depending on kernel modules such as uinput to emulate devices.

## Compiling

```bash
gcc -shared -fPIC -o selkies_joystick_interposer.so joystick_interposer.c -ldl
```

To compile the `i386` library for Wine and other 32-bit packages, add `-m32` with the `gcc-multilib` package installed.

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
