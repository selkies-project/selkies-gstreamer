# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import os
import struct
import socket
import time
from queue import Queue
from input_event_codes import *
from signal import (
    signal,
    SIGINT,
)

import logging
logger = logging.getLogger("selkies_gamepad")
logger.setLevel(logging.INFO)

STANDARD_XPAD_CONFIG = {
    # Browser detects xpad as 4 axes 17 button controller.
    # Linux xpad has 11 buttons and 8 axes.

    "name": "Selkies Controller",
    "vendor": 0x045e,  # Microsoft
    "product": 0x028e, # Xbox360 Wired Controller
    "version": 1,
    "btn_map": [
        BTN_A,      # 0
        BTN_B,      # 1
        BTN_X,      # 2
        BTN_Y,      # 3
        BTN_TL,     # 4
        BTN_TR,     # 5
        BTN_SELECT, # 6
        BTN_START,  # 7
        BTN_MODE,   # 8
        BTN_THUMBL, # 9
        BTN_THUMBR  # 10
    ],
    "axes_map": [
        ABS_X,      # 0
        ABS_Y,      # 1
        ABS_Z,      # 2
        ABS_RX,     # 3
        ABS_RY,     # 4
        ABS_RZ,     # 5
        ABS_HAT0X,  # 6
        ABS_HAT0Y   # 7
    ],


    # Input mapping from javascript:
    #   Axis 0: Left thumbstick X
    #   Axis 1: Left thumbstick Y
    #   Axis 2: Right thumbstick X
    #   Axis 3: Right thumbstick Y
    #   Button 0: A
    #   Button 1: B
    #   Button 2: X
    #   Button 3: Y
    #   Button 4: L1
    #   Button 5: R1
    #   Button 6: L2 (abs)
    #   Button 7: R2 (abs)
    #   Button 8: Select
    #   Button 9: Start
    #   Button 10: L3
    #   Button 11: R3
    #   Button 12: DPad Up
    #   Button 13: DPad Down
    #   Button 14: DPad Left
    #   Button 15: DPad Right
    #   Button 16: Xbox Button
    "mapping": {
        # Remap some buttons to axes
        "axes_to_btn": {
            2: (6,),     # ABS_Z to L2
            5: (7,),     # ABS_RZ to R2
            6: (15, 14), # ABS_HAT0X to DPad Left and DPad Right
            7: (13, 12)  # ABS_HAT0Y to DPad Down and DPad Up
        },
        # Remap axis, done in conjunction with axes_to_btn_map
        "axes": {
            2: 3, # Right Thumbstick X to ABS_RX
            3: 4, # Right Thumbstick Y to ABS_RY
        },
        # Because some buttons are remapped to axis, remap the other buttons to match target mapping.
        "btns": {
            8: 6,    # Select to BTN_SELECT
            9: 7,    # Start to BTN_START
            10: 9,   # L3 to BTN_THUMBL
            11: 10,  # R2 to BTN_THUMBR
            16: 8    # BTN_MODE
        },
        # Treat triggers as full range single axes
        "trigger_axes": [
            2, # ABS_Z
            5  # ABS_RZ
        ]
    }
}

# Vendor and product IDs to configs.
XPAD_CONFIG_MAP = {
    ("045e", "0b12"): STANDARD_XPAD_CONFIG,   # Xbox Series S/X
}

# From /usr/include/linux/joystick.h
JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02

# Max num of buttons and axes
MAX_BTNS = 512
MAX_AXES = 64

# Range for axis values
ABS_MIN = -32767
ABS_MAX = 32767

def normalize_axis_val(val):
    return round(ABS_MIN + ((val+1) * (ABS_MAX - ABS_MIN)) / 2)


def normalize_trigger_val(val):
    return round(val * (ABS_MAX - ABS_MIN)) + ABS_MIN

class SelkiesInterposerSocket(socket.socket):
    '''Subclass of socket to add interposer client config and support dynamic word length for 64bit vs 32bit clients.'''
    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
        super().__init__(family, type, proto, fileno)
        self.word_length = 8

    def set_word_length(self, length):
        self.word_length = length

    def get_word_length(self):
        return self.word_length

    def accept(self):
        '''Override accept so that new clients are also instnaces of InterposerSocket'''
        newsock, addr = super().accept()
        # Use detach() to take over the file descriptor and create a new instance of the subclass.
        mysock = SelkiesInterposerSocket(newsock.family, newsock.type, newsock.proto, fileno=newsock.detach())
        return mysock, addr

class SelkiesGamepadBase:
    def __init__(self, js_index, socket_path, loop, gamepad_mapper_class):
        self.js_index = js_index
        self.socket_path = socket_path
        self.loop = loop

        # socket server
        self.server = None
        self.send_event_task = None

        # Use default joystick config.
        self.config = STANDARD_XPAD_CONFIG

        # Map of client file descriptors to sockets.
        self.clients = {}

        # queue of events to send.
        self.events = Queue()

        # flag indicating that loop is running.
        self.running = False

        # class used for mapping gamepad events
        self.gamepad_mapper_class = gamepad_mapper_class

        # Gamepad input mapper instance
        self.mapper = self.gamepad_mapper_class(self.config)

    def __make_config(self):
        '''
        Build config message to be sent to new clients.
        Requires that self.config has been set first.
        '''
        if not self.config:
            logger.error("could not make js config because it has not yet been set.")
            return None

        name = f"{self.config["name"]} {self.js_index + 1}"
        vendor = self.config["vendor"]
        product = self.config["product"]
        version = self.config["version"]
        num_btns = len(self.config["btn_map"])
        num_axes = len(self.config["axes_map"])

        # zero fill array to max length.
        btn_map = [i for i in self.config["btn_map"]]
        axes_map = [i for i in self.config["axes_map"]]

        btn_map[num_btns:MAX_BTNS] = [0 for i in range(num_btns, MAX_BTNS)]
        axes_map[num_axes:MAX_AXES] = [0 for i in range(num_axes, MAX_AXES)]

        struct_fmt = "255sHHHHH%dH%dB" % (MAX_BTNS, MAX_AXES)
        data = struct.pack(struct_fmt,
                           name.encode(),
                           vendor,
                           product,
                           version,
                           num_btns,
                           num_axes,
                           *btn_map,
                           *axes_map
                           )
        return data

    async def __send_events(self):
        while self.running:
            if self.events.empty():
                await asyncio.sleep(0.001)
                continue
            while self.running and not self.events.empty():
                await self.__send_event(self.events.get())

    def send_btn(self, btn_num, btn_val):
        if not self.mapper:
            logger.warning("failed to send js button event because mapper was not set")
            return
        event = self.mapper.get_mapped_btn(btn_num, btn_val)
        if event is not None:
            self.events.put(event)

    def send_axis(self, axis_num, axis_val):
        if not self.mapper:
            logger.warning("failed to send js axis event because mapper was not set")
            return
        event = self.mapper.get_mapped_axis(axis_num, axis_val)
        if event is not None:
            self.events.put(event)

    async def __send_event(self, event):
        if len(self.clients) < 1:
            return

        closed_clients = []
        for fd in self.clients:
            try:
                client = self.clients[fd]
                logger.debug("Sending event to client with fd: %d" % fd)
                await self.loop.sock_sendall(client, event.get_data(client.get_word_length()))
            except BrokenPipeError:
                logger.info("Client %d disconnected" % fd)
                closed_clients.append(fd)
                client.close()

        for fd in closed_clients:
            del self.clients[fd]

    async def __setup_client(self, client):
        logger.info("Sending config to client with fd: %d, socket_path: %s, js_index=%d" % (client.fileno(), self.socket_path, self.js_index))
        try:
            config_data = self.__make_config()
            if not config_data:
                return
            await self.loop.sock_sendall(client, config_data)

            # Read the interposer config back.
            interposer_cfg = await self.loop.sock_recv(client, 1)
            logger.info(f"Got interposer config: {interposer_cfg[0]}")
            client.set_word_length(interposer_cfg[0])

        except BrokenPipeError:
            client.close()
            logger.info("Client disconnected")

    async def run_server(self):
        try:
            os.unlink(self.socket_path)
        except OSError:
            if os.path.exists(self.socket_path):
                raise
        self.clients = {}
        with SelkiesInterposerSocket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            logger.info('Listening for connections on %s' % self.socket_path)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(self.socket_path)
            server.listen(8)
            server.setblocking(False)

            self.running = True

            # start loop to process event queue.
            self.send_event_task = self.loop.create_task(self.__send_events())

            while self.running:
                try:
                    client, _ = await asyncio.wait_for(self.loop.sock_accept(server), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                fd = client.fileno()
                logger.info("Client connected with fd: %d" % fd)

                # Send client the joystick configuration
                await self.__setup_client(client)

                # Add client to dictionary to receive events.
                self.clients[fd] = client
        
        logger.info("Stopped gamepad socket server for %s" % self.socket_path)

    def stop_server(self):
        logger.info("Stopping gamepad socket server for %s" % self.socket_path)
        self.running = False

class SelkiesGamepad:
    def __init__(self, js_index, js_socket_path, ev_socket_path, loop):
        self.js_index = js_index
        self.js_socket_path = js_socket_path
        self.ev_socket_path = ev_socket_path
        self.loop = loop

        self.js_gamepad = SelkiesJSGamepad(js_index, js_socket_path, loop)
        self.ev_gamepad = SelkiesEVGamepad(js_index, ev_socket_path, loop)

    def send_btn(self, btn_num, btn_val):
        self.js_gamepad.send_btn(btn_num, btn_val)
        self.ev_gamepad.send_btn(btn_num, btn_val)

    def send_axis(self, axis_num, axis_val):
        self.js_gamepad.send_axis(axis_num, axis_val)
        self.ev_gamepad.send_axis(axis_num, axis_val)

    def run_server(self):
        asyncio.ensure_future(self.js_gamepad.run_server(), loop=self.loop)
        asyncio.ensure_future(self.ev_gamepad.run_server(), loop=self.loop)

    def stop_server(self):
        self.js_gamepad.stop_server()
        self.ev_gamepad.stop_server()

class GamepadMapperBase:
    def __init__(self, config):
        self.config = config

    def get_btn_event(self, btn_num, btn_val):
        raise Exception("get_btn_event not implemented")

    def get_axis_event(self, axis_num, axis_val):
        raise Exception("get_axis_event not implemented")

    def get_mapped_btn(self, btn_num, btn_val):
        '''
        return either a button or axis event based on mapping. 
        '''

        # Check to see if button is mapped to an axis
        axis_num = None
        axis_sign = 1
        for axis, mapping in self.config["mapping"]["axes_to_btn"].items():
            if btn_num in mapping:
                axis_num = axis
                if len(mapping) > 1:
                    axis_sign = 1 if mapping[0] == btn_num else -1
                break

        if axis_num is not None:
            # Remap button to axis
            # Normalize for input between -1 and 1
            axis_val = normalize_axis_val(btn_val*axis_sign)

            if axis_num in self.config["mapping"]["trigger_axes"]:
                # Normalize to full range for input between 0 and 1.
                axis_val = normalize_trigger_val(btn_val)
            
            return self.get_axis_event(axis_num, axis_val)

        # Perform button mapping.
        mapped_btn = self.config["mapping"]["btns"].get(btn_num, btn_num)
        if mapped_btn >= len(self.config["btn_map"]):
            logger.error("cannot send button num %d, max num buttons is %d" % (
                mapped_btn, len(self.config["btn_map"]) - 1))
            return None
        
        return self.get_btn_event(mapped_btn, int(btn_val))

    def get_mapped_axis(self, axis_num, axis_val):
        mapped_axis = self.config["mapping"]["axes"].get(axis_num, axis_num)
        if mapped_axis >= len(self.config["axes_map"]):
            logger.error("cannot send axis %d, max axis num is %d" %
                         (mapped_axis, len(self.config["axes_map"]) - 1))
            return None

        # Normalize axis value to be within range.
        return self.get_axis_event(mapped_axis, normalize_axis_val(axis_val))

class EventBase:
    def __init__(self):
        self.struct_format_64 = None
        self.struct_format_32 = None

    def get_struct_fmt(self, word_len=8):
        assert self.struct_format_64 is not None
        assert self.struct_format_32 is not None
        if word_len == 8:
            return self.struct_format_64
        return self.struct_format_32

class JSEvent(EventBase):
    # https://www.kernel.org/doc/Documentation/input/joystick-api.txt
    # struct js_event {
    #    __u32 time;     /* event timestamp in milliseconds */
    #    __s16 value;    /* value */
    #    __u8 type;      /* event type */
    #    __u8 number;    /* axis/button number */
    # };
    def __init__(self):
        super().__init__()
        self.struct_format_64 = 'IhBB'
        self.struct_format_32 = self.struct_format_64
        self.ts = None
        self.value = None
        self.event_type = None
        self.number = None

    def get_data(self, word_len=8):
        event = struct.pack(self.get_struct_fmt(word_len),
                           self.ts,
                           self.value,
                           self.event_type,
                           self.number)
        logger.debug(struct.unpack(self.get_struct_fmt(word_len), event))
        return event

class JSButtonEvent(JSEvent):
    def __init__(self, btn_num, btn_val):
        super().__init__()
        self.ts = int((time.time() * 1000) % 1000000000)
        self.event_type = JS_EVENT_BUTTON
        self.value = btn_val
        self.number = btn_num

class JSAxisEvent(JSEvent):
    def __init__(self, axis_num, axis_val):
        super().__init__()
        self.ts = int((time.time() * 1000) % 1000000000)
        self.event_type = JS_EVENT_AXIS
        self.value = axis_val
        self.number = axis_num

class JSGamepadMapper(GamepadMapperBase):
    def __init__(self, config):
        super().__init__(config)

    def get_btn_event(self, btn_num, btn_val):
        return JSButtonEvent(btn_num, btn_val)

    def get_axis_event(self, axis_num, axis_val):
        return JSAxisEvent(axis_num, axis_val)

class EVEvent(EventBase):
    # https://www.kernel.org/doc/Documentation/input/joystick-api.txt
    # struct input_event {
    # 	struct timeval time;
    # 	unsigned short type;
    # 	unsigned short code;
    # 	unsigned int value;
    # };
    def __init__(self):
        super().__init__()
        now = time.time()
        self.ts_sec = int(now)
        self.ts_usec = int((now *1e6) % 1e6)

        # Double the input_event to include sycn, EV_SYN event.
        self.struct_format_64 = 'llHHillHHi'
        self.struct_format_32 = 'iiHHiiiHHi'

        self.event_type = None
        self.code = None
        self.value = None

    def get_data(self, word_len=8):
        event = struct.pack(self.get_struct_fmt(word_len),
            self.ts_sec, self.ts_usec, self.event_type, self.code, self.value,
            self.ts_sec, self.ts_usec, EV_SYN, SYN_REPORT, 0)
        logger.debug(struct.unpack(self.get_struct_fmt(word_len), event))
        return event

class EVButtonEvent(EVEvent):
    def __init__(self, ev_code, btn_val):
        super().__init__()
        self.code = ev_code
        self.event_type = EV_KEY
        self.value = btn_val

class EVAxisEvent(EVEvent):
    def __init__(self, ev_code, axis_val):
        super().__init__()
        self.code = ev_code
        self.event_type = EV_ABS
        self.value = axis_val

class EVGamepadMapper(GamepadMapperBase):
    def __init__(self, config):
        super().__init__(config)

    def get_btn_event(self, btn_num, btn_val):
        # evdev expects ev key codes, not button numbers
        ev_code = self.config["btn_map"][btn_num]
        return EVButtonEvent(ev_code, btn_val)

    def get_axis_event(self, axis_num, axis_val):
        # evdev expects ev key codes, not axis numbers
        ev_code = self.config["axes_map"][axis_num]
        return EVAxisEvent(ev_code, axis_val)

class SelkiesJSGamepad(SelkiesGamepadBase):
    def __init__(self, js_index, socket_path, loop):
        super().__init__(js_index, socket_path, loop, JSGamepadMapper)

class SelkiesEVGamepad(SelkiesGamepadBase):
    def __init__(self, js_index, socket_path, loop):
        super().__init__(js_index, socket_path, loop, EVGamepadMapper)

if __name__ == "__main__":
    '''Starts gamepad test program that uses keyboard presses as buttons and axes
    Keyboard shortcuts:
        z -> button 0
        x -> button 1
        a -> button 2
        s -> button 3
        up/down/left/right -> HAT0 (d-pad)
    '''
    import curses

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s\r")
    logger = logging.getLogger("Selkies Gamepad")

    logger.info(f"Starting standalone gamepad test")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    js_index = 0
    js_socket_path = "/tmp/selkies_js0.sock"
    ev_socket_path = "/tmp/selkies_event1000.sock"
    js = SelkiesGamepad(js_index, js_socket_path, ev_socket_path, loop)

    logger.info("Starting server")
    js.run_server()

    btn_keymap = {
        "z": 0,
        "x": 1,
        "a": 2,
        "s": 3,
    }
    axis_keymap = {
        259: (7, -1), # Up arrow HAT0 up
        258: (7, 1),  # Down arrow HAT0 down
        260: (6, -1), # Left arrao HAT0 left
        261: (6, 1),  # Right arrow HAT0 left
    }

    async def read_keys(stdscr, key_press_handler, key_release_handler):
        # Configure curses to not wait for input and not echo keys
        stdscr.nodelay(True)
        curses.noecho()
        curses.cbreak()
        while True:
            key = stdscr.getch()
            if key != -1:
                key_press_handler(key)
                await asyncio.sleep(0.05)
                key_release_handler(key)
            await asyncio.sleep(0.01)

    def key_press_handler(key):
        if key in axis_keymap:
            axis_num, axis_value = axis_keymap[key]
            js.send_axis(axis_num, axis_value)
            logger.info(f"Axis Pressed: {key} -> axis {axis_num}")
        else:
            try:
                ch = chr(key)
                btn_num = btn_keymap.get(ch, 0)
                js.send_btn(btn_num, 1)
                logger.info(f"Key Pressed: {key}({ch}) -> button {btn_num}")
            except ValueError:
                pass

    def key_release_handler(key):
        if key in axis_keymap:
            axis_num, _ = axis_keymap[key]
            js.send_axis(axis_num, 0)
            logger.info(f"Axis Released: {key} -> axis {axis_num}")
        else:
            try:
                ch = chr(key)
                btn_num = btn_keymap.get(ch, 0)
                js.send_btn(btn_num, 0)
                logger.info(f"Key Released: {ch} -> button {btn_num}")
            except ValueError:
                pass

    async def main(stdscr):
        while True:
            await read_keys(stdscr, key_press_handler, key_release_handler)

    def curses_main(stdscr):
        asyncio.run(main(stdscr))

    loop.run_in_executor(None, lambda: curses.wrapper(curses_main))

    loop.run_forever()