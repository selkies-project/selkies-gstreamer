# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# write joystick events to an fd

# import ctypes
import os
import struct
import time
import asyncio
import socket

# Types from https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/include/uapi/linux/input-event-codes.h#n380
BTN_MISC = 0x100
BTN_0 = 0x100
BTN_1 = 0x101
BTN_2 = 0x102
BTN_3 = 0x103
BTN_4 = 0x104
BTN_5 = 0x105
BTN_6 = 0x106
BTN_7 = 0x107
BTN_8 = 0x108
BTN_9 = 0x109

BTN_MOUSE = 0x110
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114
BTN_FORWARD = 0x115
BTN_BACK = 0x116
BTN_TASK = 0x117

BTN_JOYSTICK = 0x120
BTN_TRIGGER = 0x120
BTN_THUMB = 0x121
BTN_THUMB2 = 0x122
BTN_TOP = 0x123
BTN_TOP2 = 0x124
BTN_PINKIE = 0x125
BTN_BASE = 0x126
BTN_BASE2 = 0x127
BTN_BASE3 = 0x128
BTN_BASE4 = 0x129
BTN_BASE5 = 0x12a
BTN_BASE6 = 0x12b
BTN_DEAD = 0x12f

BTN_GAMEPAD = 0x130
BTN_SOUTH = 0x130
BTN_A = BTN_SOUTH
BTN_EAST = 0x131
BTN_B = BTN_EAST
BTN_C = 0x132
BTN_NORTH = 0x133
BTN_X = BTN_NORTH
BTN_WEST = 0x134
BTN_Y = BTN_WEST
BTN_Z = 0x135
BTN_TL = 0x136
BTN_TR = 0x137
BTN_TL2 = 0x138
BTN_TR2 = 0x139
BTN_SELECT = 0x13a
BTN_START = 0x13b
BTN_MODE = 0x13c
BTN_THUMBL = 0x13d
BTN_THUMBR = 0x13e

ABS_X = 0x00
ABS_Y = 0x01
ABS_Z = 0x02
ABS_RX = 0x03
ABS_RY = 0x04
ABS_RZ = 0x05
ABS_THROTTLE = 0x06
ABS_RUDDER = 0x07
ABS_WHEEL = 0x08
ABS_GAS = 0x09
ABS_BRAKE = 0x0a
ABS_HAT0X = 0x10
ABS_HAT0Y = 0x11
ABS_HAT1X = 0x12
ABS_HAT1Y = 0x13
ABS_HAT2X = 0x14
ABS_HAT2Y = 0x15
ABS_HAT3X = 0x16
ABS_HAT3Y = 0x17
ABS_PRESSURE = 0x18
ABS_DISTANCE = 0x19
ABS_TILT_X = 0x1a
ABS_TILT_Y = 0x1b
ABS_TOOL_WIDTH = 0x1c
ABS_VOLUME = 0x20
ABS_PROFILE = 0x21

SOCKET_PATH = "/tmp/selkies_js0.sock"

# From /usr/include/linux/joystick.h
JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02

# Max num of buttons and axes
MAX_BTNS = 512
MAX_AXES = 64

# Joystick event struct
# https://www.kernel.org/doc/Documentation/input/joystick-api.txt
# struct js_event {
#    __u32 time;     /* event timestamp in milliseconds */
#    __s16 value;    /* value */
#    __u8 type;      /* event type */
#    __u8 number;    /* axis/button number */
# };

# Map of client file descriptors to sockets.
clients = {}

XPAD_CONFIG = {
    "name": "Xbox 360 Controller",
    "btn_map": [
        BTN_A,
        BTN_B,
        BTN_X,
        BTN_Y,
        BTN_TL,
        BTN_TR,
        BTN_SELECT,
        BTN_START,
        BTN_MODE,
        BTN_THUMBL,
        BTN_THUMBR
    ],
    "axes_map": [
        ABS_X,
        ABS_Y,
        ABS_Z,
        ABS_RX,
        ABS_RY,
        ABS_RZ,
        ABS_HAT0X,
        ABS_HAT0Y
    ]
}


def get_btn_event(btn_num, btn_val):
    ts = int((time.time() * 1000) % 1000000000)

    # see js_event struct definition above.
    # https://docs.python.org/3/library/struct.html
    struct_format = 'IhBB'
    event = struct.pack(struct_format, ts, btn_val, JS_EVENT_BUTTON, btn_num)

    # debug
    print(struct.unpack(struct_format, event))

    return event


def get_axis_event(axis_num, axis_val):
    ts = int((time.time() * 1000) % 1000000000)

    # see js_event struct definition above.
    # https://docs.python.org/3/library/struct.html
    struct_format = 'IhBB'
    event = struct.pack(struct_format, ts, axis_val, JS_EVENT_AXIS, axis_num)

    # debug
    print(struct.unpack(struct_format, event))

    return event


def make_config():
    cfg = XPAD_CONFIG
    num_btns = len(cfg["btn_map"])
    num_axes = len(cfg["axes_map"])

    # zero fill array to max lenth.
    btn_map = [i for i in cfg["btn_map"]]
    axes_map = [i for i in cfg["axes_map"]]

    btn_map[num_btns:MAX_BTNS] = [0 for i in range(num_btns, MAX_BTNS)]
    axes_map[num_axes:MAX_AXES] = [0 for i in range(num_axes, MAX_AXES)]

    struct_fmt = "255sHH%dH%dB" % (MAX_BTNS, MAX_AXES)
    data = struct.pack(struct_fmt,
                       cfg["name"].encode(),
                       num_btns,
                       num_axes,
                       *btn_map,
                       *axes_map
                       )
    return data


async def send_events():
    loop = asyncio.get_event_loop()
    btn_num = 0
    btn_val = 0
    while True:
        if len(clients) < 1:
            await asyncio.sleep(0.1)
            continue

        closed_clients = []
        for fd in clients:
            try:
                client = clients[fd]
                print("Sending event to client: %d" % fd)
                await loop.sock_sendall(client, get_btn_event(btn_num, btn_val))
            except BrokenPipeError:
                print("Client %d disconnected" % fd)
                closed_clients.append(fd)
                client.close()

        for fd in closed_clients:
            del clients[fd]

        await asyncio.sleep(0.5)
        btn_val = 0 if btn_val == 1 else 1

        if btn_val == 1:
            btn_num = (btn_num + 1) % 11


async def run_server():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    server.setblocking(False)

    loop = asyncio.get_event_loop()

    print('Listening for connections on %s' % SOCKET_PATH)

    # Create task that sends events to all connected clients.
    loop.create_task(send_events())

    try:
        while True:
            client, _ = await loop.sock_accept(server)
            fd = client.fileno()
            print("Client connected with fd: %d" % fd)

            # Send client the joystick configuration
            await loop.sock_sendall(client, make_config())

            # Add client to dictionary to receive events.
            clients[fd] = client
    finally:
        server.shutdown(1)
        server.close()

if __name__ == "__main__":
    # remove the socket file if it already exists
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        if os.path.exists(SOCKET_PATH):
            raise

    asyncio.run(run_server())
