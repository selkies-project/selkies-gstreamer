# Selkies Joystick (Gamepad) Interposer

LD_PRELOAD library for interposing application calls to open a Linux joystick device and pass data via a unix domain socket.

This allows the selkies-gstreamer WebRTC interface to pass gamepad events over the Data Channel and translate them to joystick events without requiring access to /dev/input/js0 or depend kernel modules like uinput to emulate devices.  

## Compiling

```bash
gcc -shared -fPIC -o joystick_interposer.so joystick_interposer.c -ldl
```

## Testing

1. Start the python joystick emulator:

```bash
python3 js-interposer-test.py
```

This creates a new unix domain socket at `/tmp/selkies_js0.sock` and simulates joystick button presses and axis motion when a connection from the interposer is detected.

2. Run `jstest` with the interposer library:

```bash
LD_PRELOAD=${PWD}/joystick_interposer.so jstest /dev/input/js0
```