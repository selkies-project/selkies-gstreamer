/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following copyright and
 * permission notice:
 *
 *   Copyright 2019 Google LLC
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

// Based on https://github.com/parsec-cloud/web-client/blob/master/src/gamepad.js

/*eslint no-unused-vars: ["error", { "vars": "local" }]*/

const GP_TIMEOUT = 20;
const MAX_GAMEPADS = 4;

// Map of gamepad buttons to uinput buttons
// Mapping from sc-controller:
//   https://github.com/kozec/sc-controller/blob/master/default_profiles/XBox%20Controller.sccprofile
const UINPUT_BTN_MAP = {
    0: 304, // BTN_GAMEPAD
    1: 305, // BTN_EAST
    2: 307, // BTN_NORTH
    3: 308, // BTN_WEST
    4: 310, // BTN_TL
    5: 311, // BTN_TR
    6: 10004, // [axis 4] ABS_Z
    7: 10005, // [axis 5] ABS_RZ
    8: 314, // BTN_SELECT
    9: 315, // BTN_START
    10: 317, // BTN_THUMBL
    11: 318, // BTN_THUMBR
    12: -20007, // [axis 17 -] ABS_HAT0Y
    13: 20007, // [axis 17 +] ABS_HAT0Y
    14: -20006, // [axis 16 -] ABS_HAT0X 
    15: 20006, // [axis 16 +] ABS_HAT0X
    16: 316, // BTN_MODE
}

// Map of gamepad axis to uinput axis
const UINPUT_AXIS_MAP = {
    0: 0, // ABS_X
    1: 1, // ABS_Y
    2: 3, // ABS_RX
    3: 4, // ABS_RY
    4: 2, // ABS_Z
    5: 5, // ABS_RZ
    6: 16, // ABS_HAT0X
    7: 17, // ABS_HAT0Y
}

class GamepadManager {
    constructor(gamepad, onButton, onAxis, onDisconnect) {
        this.gamepad = gamepad;
        this.onButton = onButton;
        this.onAxis = onAxis;
        this.onDisconnect = onDisconnect;
        this.state = {};
        this.buttonMap = UINPUT_BTN_MAP;
        this.axisMap = UINPUT_AXIS_MAP;
        this.numButtons = Object.keys(this.buttonMap).length;
        this.numAxes = Object.keys(this.axisMap).length;

        this.interval = setInterval(() => {
            this._poll();
        }, GP_TIMEOUT);
    }

    _poll() {
        const gamepads = navigator.getGamepads();

        for (let i = 0; i < MAX_GAMEPADS; i++) {
            if (gamepads[i]) {
                let gp = this.state[i];

                if (!gp)
                    gp = this.state[i] = { axes: [], buttons: [] };

                for (let x = 0; x < gamepads[i].buttons.length; x++) {
                    const value = gamepads[i].buttons[x].value;

                    if (gp.buttons[x] !== undefined && gp.buttons[x] !== value) { //eslint-disable-line no-undefined
                        var axisNum;
                        if (Math.abs(this.buttonMap[x]) > 20000) {
                            // translate to HAT axis.
                            axisNum = Math.abs(this.buttonMap[x]) - 20000;
                            var axisVal = Math.sign(this.buttonMap[x]) * value;
                            this.onAxis(i, this.axisMap[axisNum], this.normalizeAxisValue(axisNum, axisVal));
                        } else if (this.buttonMap[x] > 10000) {
                            // translate to Z, RZ (trigger) axis
                            axisNum = Math.abs(this.buttonMap[x]) - 10000;
                            this.onAxis(i, this.axisMap[axisNum], this.normalizeAxisValue(axisNum, value));
                        } else {
                            // send button
                            this.onButton(i, this.buttonMap[x], Math.round(value));
                        }
                    }

                    gp.buttons[x] = value;
                }

                for (let x = 0; x < gamepads[i].axes.length; x++) {
                    let val = gamepads[i].axes[x];
                    if (Math.abs(val) < 0.05) val = 0;

                    if (gp.axes[x] !== undefined && gp.axes[x] !== val) //eslint-disable-line no-undefined
                        this.onAxis(i, this.axisMap[x], this.normalizeAxisValue(x, val));

                    gp.axes[x] = val;
                }

            } else if (this.state[i]) {
                delete this.state[i];
                this.onDisconnect(i);
            }
        }
    }

    normalizeAxisValue(axisNum, value) {
        // gamepad values are between [-1, 1], normalize them to their respective ranges.
        switch (axisNum) {
            case 0:
            case 1:
            case 2:
            case 3:
            case 4:
            case 5:
                // range: [-32768, 32767]
                return Math.round(-32768 + ((value + 1) * 65535) / 2);
            case 6:
            case 7:
                // range: [-1, 1]
                return Math.round(value);
        }

    }

    destroy() {
        clearInterval(this.interval);
    }
}