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

// Service Worker to support PWA
window.onload = () => {
    'use strict';
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js?ts=CACHE_VERSION');
    }
}

/**
 * Fetch the value of a cookie by name.
 * @param {string} a
 */
function getCookieValue(a) {
    // https://stackoverflow.com/questions/5639346/what-is-the-shortest-function-for-reading-a-cookie-by-name-in-javascript
    var b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

var ScaleLoader = VueSpinner.ScaleLoader;

var app = new Vue({

    el: '#app',

    components: {
        ScaleLoader
    },

    data() {
        return {
            appName: window.location.pathname.endsWith("/") && (window.location.pathname.split("/")[1]) || "webrtc",
            videoBitRate: 8000,
            videoBitRateOptions: [
                { text: '250 kbps', value: 250 },
                { text: '500 kbps', value: 500 },
                { text: '750 kbps', value: 750 },
                { text: '1 mbps', value: 1000 },
                { text: '2 mbps', value: 2000 },
                { text: '3 mbps', value: 3000 },
                { text: '4 mbps', value: 4000 },
                { text: '6 mbps', value: 6000 },
                { text: '8 mbps', value: 8000 },
                { text: '10 mbps', value: 10000 },
                { text: '12 mbps', value: 12000 },
                { text: '16 mbps', value: 16000 },
                { text: '20 mbps', value: 20000 },
                { text: '25 mbps', value: 25000 },
                { text: '30 mbps', value: 30000 },
                { text: '40 mbps', value: 40000 },
                { text: '50 mbps', value: 50000 },
                { text: '60 mbps', value: 60000 },
                { text: '75 mbps', value: 75000 },
                { text: '80 mbps', value: 80000 },
                { text: '100 mbps', value: 100000 },
                { text: '150 mbps', value: 150000 },
                { text: '200 mbps', value: 200000 },
                { text: '300 mbps', value: 300000 },
                { text: '400 mbps', value: 400000 },
            ],
            videoFramerate: 60,
            videoFramerateOptions: [
                { text: '10 fps', value: 10 },
                { text: '15 fps', value: 15 },
                { text: '30 fps', value: 30 },
                { text: '45 fps', value: 45 },
                { text: '60 fps', value: 60 },
                { text: '75 fps', value: 75 },
                { text: '90 fps', value: 90 },
                { text: '100 fps', value: 100 },
                { text: '120 fps', value: 120 },
                { text: '144 fps', value: 144 },
                { text: '165 fps', value: 165 },
                { text: '180 fps', value: 180 },
                { text: '200 fps', value: 200 },
                { text: '240 fps', value: 240 },
            ],
            audioBitRate: 64000,
            audioBitRateOptions: [
                { text: '24 kb/s', value: 24000 },
                { text: '32 kb/s', value: 32000 },
                { text: '48 kb/s', value: 48000 },
                { text: '64 kb/s', value: 64000 },
                { text: '96 kb/s', value: 96000 },
                { text: '128 kb/s', value: 128000 },
                { text: '192 kb/s', value: 192000 },
                { text: '256 kb/s', value: 256000 },
                { text: '320 kb/s', value: 320000 },
                { text: '510 kb/s', value: 510000 },
            ],
            showStart: false,
            showDrawer: false,
            logEntries: [],
            debugEntries: [],
            status: 'connecting',
            loadingText: '',
            clipboardStatus: 'disabled',
            gamepadState: 'disconnected',
            gamepadName: 'none',
            windowResolution: "",
            connectionStatType: "unknown",
            connectionLatency: 0,
            connectionVideoLatency: 0,
            connectionAudioLatency: 0,
            connectionAudioCodecName: "NA",
            connectionAudioBitrate: 0,
            connectionPacketsReceived: 0,
            connectionPacketsLost: 0,
            connectionBytesReceived: 0,
            connectionBytesSent: 0,
            connectionCodec: "unknown",
            connectionVideoDecoder: "unknown",
            connectionResolution: "",
            connectionFrameRate: 0,
            connectionVideoBitrate: 0,
            connectionAvailableBandwidth: 0,
            encoderName: "",
            serverCPUUsage: 0,
            gpuLoad: 0,
            gpuMemoryTotal: 0,
            gpuMemoryUsed: 0,
            serverMemoryTotal: 0,
            serverMemoryUsed: 0,
            serverLatency: 0,
            resizeRemote: true,
            scaleLocal: false,
            debug: false,
            turnSwitch: false,
            publishingAllowed: false,
            publishingIdle: false,
            publishingError: "",
            publishingAppName: "",
            publishingAppDisplayName: "",
            publishingAppDescription: "",
            publishingAppIcon: "",
            publishingValid: false,
            rules: {
                required: value => {
                    if (!value || value.length == 0)
                        return 'required.';
                    return true;
                },

                validname: value => {
                    if (value.length > 63) {
                        return 'must be less than 63 characters';
                    }
                    if (!new RegExp('^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$').exec(value)) {
                        return 'invalid name'
                    }
                    if (value === this.appName) {
                        return 'must be different than current name'
                    }
                    return true;
                },
            }
        }
    },

    methods: {
        getIntParam: (key, default_value) => {
            const prefixedKey = app.appName + "_" + key;
            return (parseInt(window.localStorage.getItem(prefixedKey)) || default_value);
        },
        setIntParam: (key, value) => {
            if (value === null) return;
            const prefixedKey = app.appName + "_" + key;
            window.localStorage.setItem(prefixedKey, value.toString());
        },
        getBoolParam: (key, default_value) => {
            const prefixedKey = app.appName + "_" + key;
            var v = window.localStorage.getItem(prefixedKey);
            if (v === null) {
                return default_value;
            } else {
                return (v.toString().toLowerCase() === "true");
            }
        },
        setBoolParam: (key, value) => {
            if (value === null) return;
            const prefixedKey = app.appName + "_" + key;
            window.localStorage.setItem(prefixedKey, value.toString());
        },
        getUsername: () => {
            if (app === undefined) return "webrtc";
            return (getCookieValue("broker_" + app.appName) || "webrtc").split("#")[0];
        },
        enterFullscreen() {
            // Request fullscreen mode.
            webrtc.element.parentElement.requestFullscreen();
        },
        playStream() {
            webrtc.playStream();
            audio_webrtc.playStream();
            this.showStart = false;
        },
        enableClipboard() {
            navigator.clipboard.readText()
                .then(text => {
                    webrtc._setStatus("clipboard enabled");
                    webrtc.sendDataChannelMessage("cr");
                })
                .catch(err => {
                    webrtc._setError('Failed to read clipboard contents: ' + err);
                });
        },
        publish() {
            var data = {
                name: this.publishingAppName,
                displayName: this.publishingAppDisplayName,
                description: this.publishingAppDescription,
                icon: this.publishingAppIcon,
            }
            console.log("Publishing new image", data);

            fetch("/publish/" + app.appName, {
                method: "POST",
                headers: {
                    "content-type": "application/json"
                },
                body: JSON.stringify(data),
            })
                .then(function (response) {
                    return response.json();
                })
                .then((response) => {
                    if (response.code === 201) {
                        this.publishingIdle = false;
                        checkPublishing();
                    } else {
                        this.publishingError = response.status;
                    }
                });
        }
    },

    watch: {
        videoBitRate(newValue) {
            if (newValue === null) return;
            webrtc.sendDataChannelMessage('vb,' + newValue);
            this.setIntParam("videoBitRate", newValue);
        },
        videoFramerate(newValue) {
            if (newValue === null) return;
            console.log("video framerate changed to " + newValue);
            webrtc.sendDataChannelMessage('_arg_fps,' + newValue);
            this.setIntParam("videoFramerate", newValue);
        },
        resizeRemote(newValue, oldValue) {
            if (newValue === null) return;
            console.log("resize remote changed from " + oldValue + " to " + newValue);
            app.windowResolution = webrtc.input.getWindowResolution();
            var res = app.windowResolution[0] + "x" + app.windowResolution[1];
            if (oldValue !== null && newValue !== oldValue) webrtc.sendDataChannelMessage('_arg_resize,' + newValue + "," + res);
            this.setBoolParam("resizeRemote", newValue);
        },
        scaleLocal(newValue, oldValue) {
            if (newValue === null) return;
            console.log("scaleLocal changed from " + oldValue + " to " + newValue);
            if (oldValue !== null && newValue !== oldValue) {
                if (newValue === true) {
                    webrtc.element.style.width = '';
                    webrtc.element.style.height = '';
                    webrtc.element.setAttribute("class", "video scale");
                } else {
                    webrtc.element.setAttribute("class", "video");
                }
            }
            this.setBoolParam("scaleLocal", newValue);
        },
        audioBitRate(newValue) {
            if (newValue === null) return;
            webrtc.sendDataChannelMessage('ab,' + newValue);
            this.setIntParam("audioBitRate", newValue);
        },
        turnSwitch(newValue, oldValue) {
            if (newValue === null) return;
            this.setBoolParam("turnSwitch", newValue);
            // Reload the page to force read of stored value on first load.
            if (webrtc === undefined || webrtc.peerConnection === null) return;
            setTimeout(() => {
                document.location.reload();
            }, 700);
        },
        debug(newValue, oldValue) {
            if (newValue === null) return;
            this.setBoolParam("debug", newValue);
            // Reload the page to force read of stored value on first load.
            if (webrtc === undefined || webrtc.peerConnection === null) return;
            setTimeout(() => {
                document.location.reload();
            }, 700);
        },
        appName(newValue) {
            document.title = "Selkies - " + newValue;
        },
        showDrawer(newValue) {
            // Detach inputs when menu is shown.
            if (newValue === true) {
                webrtc.input.detach();
            } else {
                webrtc.input.attach();
            }
        },
    },

    updated: () => {
        document.title = "Selkies - " + app.appName;
    },

});

// Fetch debug setting
app.debug = app.getBoolParam("debug", false);

// Fetch turn setting
app.turnSwitch = app.getBoolParam("turnSwitch", false);

// Fetch scale local settings
app.scaleLocal = app.getBoolParam("scaleLocal", !app.resizeRemote);

var videoElement = document.getElementById("stream");
if (videoElement === null) {
    throw 'videoElement not found on page';
}

videoElement.addEventListener('loadeddata', (e) => {
    webrtc.input.getCursorScaleFactor();
})

var audioElement = document.getElementById("audio_stream");
if (audioElement === null) {
    throw 'audioElement not found on page';
}

// WebRTC entrypoint, connect to the signalling server
/*global WebRTCDemoSignalling, WebRTCDemo*/
var protocol = (location.protocol == "http:" ? "ws://" : "wss://");
var signalling = new WebRTCDemoSignalling(new URL(protocol + window.location.host + "/" + app.appName + "/signalling/"));
var webrtc = new WebRTCDemo(signalling, videoElement, 1);
var audio_signalling = new WebRTCDemoSignalling(new URL(protocol + window.location.host + "/" + app.appName + "/signalling/"));
var audio_webrtc = new WebRTCDemo(audio_signalling, audioElement, 3);

// Function to add timestamp to logs.
var applyTimestamp = (msg) => {
    var now = new Date();
    var ts = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
    return "[" + ts + "]" + " " + msg;
}

// Send signalling status and error messages to logs.
signalling.onstatus = (message) => {
    app.loadingText = message;
    app.logEntries.push(applyTimestamp("[signalling] " + message));
};
signalling.onerror = (message) => { app.logEntries.push(applyTimestamp("[signalling] [ERROR] " + message)) };

signalling.ondisconnect = () => {
    var checkconnect = app.status == checkconnect;
    // if (app.status !== "connected") return;
    console.log("signalling disconnected");
    app.status = 'connecting';
    videoElement.style.cursor = "auto";
    webrtc.reset();
    app.status = 'checkconnect';
    if (!checkconnect) audio_signalling.disconnect();
}

audio_signalling.onstatus = (message) => {
    app.loadingText = message;
    app.logEntries.push(applyTimestamp("[audio signalling] " + message));
};
audio_signalling.onerror = (message) => { app.logEntries.push(applyTimestamp("[audio signalling] [ERROR] " + message)) };

audio_signalling.ondisconnect = () => {
    var checkconnect = app.status == checkconnect;
    // if (app.status !== "connected") return;
    console.log("audio signalling disconnected");
    app.status = 'connecting';
    videoElement.style.cursor = "auto";
    audio_webrtc.reset();
    app.status = 'checkconnect';
    if (!checkconnect) signalling.disconnect();
}

// Send webrtc status and error messages to logs.
webrtc.onstatus = (message) => { app.logEntries.push(applyTimestamp("[webrtc] " + message)) };
webrtc.onerror = (message) => { app.logEntries.push(applyTimestamp("[webrtc] [ERROR] " + message)) };
audio_webrtc.onstatus = (message) => { app.logEntries.push(applyTimestamp("[audio webrtc] " + message)) };
audio_webrtc.onerror = (message) => { app.logEntries.push(applyTimestamp("[audio webrtc] [ERROR] " + message)) };

if (app.debug) {
    signalling.ondebug = (message) => { app.debugEntries.push("[signalling] " + message); };
    audio_signalling.ondebug = (message) => { app.debugEntries.push("[audio signalling] " + message); };
    webrtc.ondebug = (message) => { app.debugEntries.push(applyTimestamp("[webrtc] " + message)) };
    audio_webrtc.ondebug = (message) => { app.debugEntries.push(applyTimestamp("[audio webrtc] " + message)) };
}

webrtc.ongpustats = (data) => {
    app.gpuLoad = Math.round(data.load * 100);
    app.gpuMemoryTotal = data.memory_total;
    app.gpuMemoryUsed = data.memory_used;
}

var videoConnected = "";
var audioConnected = "";
// Bind vue status to connection state.
function onBothStreamConnected() {
    // Start watching stats.
    var videoBytesReceivedStart = 0;
    var audioBytesReceivedStart = 0;
    var statsStart = new Date().getTime() / 1000;
    var statsLoop = () => {
        if (videoConnected !== "connected" || audioConnected !== "connected") return;
        webrtc.getConnectionStats().then((stats) => {
            if (videoConnected !== "connected" || audioConnected !== "connected") return;
            audio_webrtc.getConnectionStats().then((audioStats) => {
                if (videoConnected !== "connected" || audioConnected !== "connected") return;
                var now = new Date().getTime() / 1000;

                // Sum of video+audio+server latency in ms.
                app.connectionLatency = 0;
                app.connectionLatency += app.serverLatency;

                // Sum of video+audio packets.
                app.connectionPacketsReceived = 0;
                app.connectionPacketsLost = 0;

                // Connection stats
                app.connectionStatType = stats.general.connectionType == audioStats.general.connectionType ? stats.general.connectionType : (stats.general.connectionType + " / " + audioStats.general.connectionType);
                app.connectionBytesReceived = ((stats.general.bytesReceived + audioStats.general.bytesReceived) * 1e-6).toFixed(2) + " MBytes";
                app.connectionBytesSent = ((stats.general.bytesSent + audioStats.general.bytesSent) * 1e-6).toFixed(2) + " MBytes";
                app.connectionAvailableBandwidth = ((parseInt(stats.general.availableReceiveBandwidth) + parseInt(audioStats.general.availableReceiveBandwidth)) / 1e+6).toFixed(2) + " mbps";

                // Video stats.
                app.connectionVideoLatency = parseInt(stats.video.jitterBufferDelay * 1000);
                app.connectionLatency += stats.video.jitterBufferDelay * 1000;
                app.connectionPacketsReceived += stats.video.packetsReceived;
                app.connectionPacketsLost += stats.video.packetsLost;
                app.connectionCodec = stats.video.codecName;
                app.connectionVideoDecoder = stats.video.decoder;
                app.connectionResolution = stats.video.frameWidth + "x" + stats.video.frameHeight;
                app.connectionFrameRate = stats.video.framesPerSecond;
                app.connectionVideoBitrate = (((stats.video.bytesReceived - videoBytesReceivedStart) / (now - statsStart)) * 8 / 1e+6).toFixed(2);
                videoBytesReceivedStart = stats.video.bytesReceived;

                // Audio stats.
                app.connectionLatency += audioStats.audio.jitterBufferDelay * 1000;
                app.connectionPacketsReceived += audioStats.audio.packetsReceived;
                app.connectionPacketsLost += audioStats.audio.packetsLost;
                app.connectionAudioLatency = parseInt(audioStats.audio.jitterBufferDelay * 1000);
                app.connectionAudioCodecName = audioStats.audio.codecName;
                app.connectionAudioBitrate = (((audioStats.audio.bytesReceived - audioBytesReceivedStart) / (now - statsStart)) * 8 / 1e+3).toFixed(2);
                audioBytesReceivedStart = audioStats.audio.bytesReceived;

                // Format latency
                app.connectionLatency = parseInt(app.connectionLatency);

                statsStart = now;

                webrtc.sendDataChannelMessage("_stats_video," + JSON.stringify(stats.allReports));
                webrtc.sendDataChannelMessage("_stats_audio," + JSON.stringify(audioStats.allReports));

                // Stats refresh loop.
                setTimeout(statsLoop, 1000);
            });
        });
    };
    statsLoop();
}
webrtc.onconnectionstatechange = (state) => {
    videoConnected = state;
    if (videoConnected === "connected" && audioConnected === "connected") {
        app.status = state;
        onBothStreamConnected();
    } else {
        app.status = state === "connected" ? audioConnected : videoConnected;
    }
};
audio_webrtc.onconnectionstatechange = (state) => {
    audioConnected = state;
    if (videoConnected === "connected" && audioConnected === "connected") {
        app.status = state;
        onBothStreamConnected();
    } else {
        app.status = state === "connected" ? videoConnected : audioConnected;
    }
};

webrtc.ondatachannelopen = () => {
    // Bind gamepad connected handler.
    webrtc.input.ongamepadconnected = (gamepad_id) => {
        webrtc._setStatus('Gamepad connected: ' + gamepad_id);
        app.gamepadState = "connected";
        app.gamepadName = gamepad_id;
    }

    // Bind gamepad disconnect handler.
    webrtc.input.ongamepaddisconnected = () => {
        webrtc._setStatus('Gamepad disconnected: ' + gamepad_id);
        app.gamepadState = "disconnected";
        app.gamepadName = "none";
    }

    // Bind input handlers.
    webrtc.input.attach();

    // Send client-side metrics over data channel every 5 seconds
    setInterval(() => {
        if (app.connectionFrameRate === parseInt(app.connectionFrameRate, 10)) webrtc.sendDataChannelMessage('_f,' + app.connectionFrameRate);
        if (app.connectionLatency === parseInt(app.connectionLatency, 10)) webrtc.sendDataChannelMessage('_l,' + app.connectionLatency);
    }, 5000)
}

webrtc.ondatachannelclose = () => {
    webrtc.input.detach();
}

webrtc.input.onmenuhotkey = () => {
    app.showDrawer = !app.showDrawer;
}

webrtc.input.onfullscreenhotkey = () => {
    app.enterFullscreen();
}

webrtc.input.onresizeend = () => {
    app.windowResolution = webrtc.input.getWindowResolution();
    var newRes = parseInt(app.windowResolution[0]) + "x" + parseInt(app.windowResolution[1]);
    console.log(`Window size changed: ${app.windowResolution[0]}x${app.windowResolution[1]}, scaled to: ${newRes}`);
    webrtc.sendDataChannelMessage("r," + newRes);
    webrtc.sendDataChannelMessage("s," + window.devicePixelRatio);
}

webrtc.onplaystreamrequired = () => {
    app.showStart = true;
}

audio_webrtc.onplaystreamrequired = () => {
    app.showStart = true;
}

// Actions to take whenever window changes focus
window.addEventListener('focus', () => {
    // reset keyboard to avoid stuck keys.
    webrtc.sendDataChannelMessage("kr");

    // Send clipboard contents.
    navigator.clipboard.readText()
        .then(text => {
            webrtc.sendDataChannelMessage("cw," + stringToBase64(text))
        })
        .catch(err => {
            webrtc._setStatus('Failed to read clipboard contents: ' + err);
        });
});
window.addEventListener('blur', () => {
    // reset keyboard to avoid stuck keys.
    webrtc.sendDataChannelMessage("kr");
});

webrtc.onclipboardcontent = (content) => {
    if (app.clipboardStatus === 'enabled') {
        navigator.clipboard.writeText(content)
            .catch(err => {
                app._setDebug('Could not copy text to clipboard: ' + err);
            });
    }
}

webrtc.oncursorchange = (handle, curdata, hotspot, override) => {
    if (parseInt(handle) === 0) {
        videoElement.style.cursor = "auto";
        return;
    }
    if (override) {
        videoElement.style.cursor = override;
        return;
    }
    if (!webrtc.cursor_cache.has(handle)) {
        // Add cursor to cache.
        const cursor_url = "url('data:image/png;base64," + curdata + "')";
        webrtc.cursor_cache.set(handle, cursor_url);
    }
    var cursor_url = webrtc.cursor_cache.get(handle);
    if (hotspot) {
        cursor_url += ` ${hotspot.x} ${hotspot.y}, auto`;
    } else {
        cursor_url += ", auto";
    }
    videoElement.style.cursor = cursor_url;
}

webrtc.onsystemaction = (action) => {
    webrtc._setStatus("Executing system action: " + action);
    if (action === 'reload') {
        setTimeout(() => {
            // trigger webrtc.reset() by disconnecting from the signalling server.
            signalling.disconnect();
        }, 700);
    } else if (action.startsWith('framerate')) {
        // Server received framerate setting.
        const framerateSetting = app.getIntParam("videoFramerate", null);
        if (framerateSetting !== null) {
            app.videoFramerate = framerateSetting;
        } else {
            // Use the server setting.
            app.videoFramerate = parseInt(action.split(",")[1]);
        }
    } else if (action.startsWith('video_bitrate')) {
        // Server received video bitrate setting.
        const videoBitrateSetting = app.getIntParam("videoBitRate", null);
        if (videoBitrateSetting !== null) {
            // Prefer the user saved value.
            app.videoBitRate = videoBitrateSetting;
        } else {
            // Use the server setting.
            app.videoBitRate = parseInt(action.split(",")[1]);
        }
    } else if (action.startsWith('audio_bitrate')) {
        // Server received audio bitrate setting.
        const audioBitrateSetting = app.getIntParam("audioBitRate", null);
        if (audioBitrateSetting !== null) {
            // Prefer the user saved value.
            app.audioBitRate = audioBitrateSetting
        } else {
            // Use the server setting.
            app.audioBitRate = parseInt(action.split(",")[1]);
        }
    } else if (action.startsWith('resize')) {
        // Remote resize enabled/disabled action.
        const resizeSetting = app.getBoolParam("resize", null);
        if (resizeSetting !== null) {
            // Prefer the user saved value.
            app.resizeRemote = resizeSetting;
        } else {
            // Use server setting.
            app.resizeRemote = (action.split(",")[1].toLowerCase() === 'true');
            if (app.resizeRemote === false && app.getBoolParam("scaleLocal", null) === null) {
                // Enable local scaling if remote resize is disabled and there is no saved value.
                app.scaleLocal = true;
            }
        }
    } else if (action.startsWith("resolution")) {
        // Sent when remote resizing is enabled.
        // Match the CSS of the video element to the remote resolution.
        var remote_res = action.split(",")[1];
        console.log("received remote resolution of: " + remote_res);
        if (app.resizeRemote === true) {
            var toks = remote_res.split("x");
            webrtc.element.style.width = toks[0]/window.devicePixelRatio+'px';
            webrtc.element.style.height = toks[1]/window.devicePixelRatio+'px';

            // Update cursor scale factor
            webrtc.input.getCursorScaleFactor({ remoteResolutionEnabled: true });
        }
    } else if (action.startsWith("local_scaling")) {
        // Local scaling default pushed from server

        // Local scaling enabled/disabled action.
        const scalingSetting = app.getBoolParam("scaleLocal", null);
        if (scalingSetting !== null) {
            // Prefer the user saved value.
            app.scaleLocal = scalingSetting;
        } else {
            // Use server setting.
            app.scaleLocal = (action.split(",")[1].toLowerCase() === 'true');
        }
    } else if (action.startsWith("encoder")) {
        if (action.split(",")[1].startsWith("nv") || action.split(",")[1].startsWith("va")) {
            app.encoderName = "hardware" + " (" + action.split(",")[1] + ")";
        } else {
            app.encoderName = "software" + " (" + action.split(",")[1] + ")";
        }
    } else {
        webrtc._setStatus('Unhandled system action: ' + action);
    }
}

webrtc.onlatencymeasurement = (latency_ms) => {
    app.serverLatency = latency_ms;
}

webrtc.onsystemstats = (stats) => {
    if (stats.cpu_percent !== undefined) app.serverCPUUsage = stats.cpu_percent.toFixed(0);
    if (stats.mem_total !== undefined) app.serverMemoryTotal = stats.mem_total;
    if (stats.mem_used !== undefined) app.serverMemoryUsed = stats.mem_used;
}

// Safari without Permission API enabled fails
if (navigator.permissions) {
    navigator.permissions.query({
        name: 'clipboard-read'
    }).then(permissionStatus => {
        // Will be 'granted', 'denied' or 'prompt':
        if (permissionStatus.state === 'granted') {
            app.clipboardStatus = 'enabled';
        }

        // Listen for changes to the permission state
        permissionStatus.onchange = () => {
            if (permissionStatus.state === 'granted') {
                app.clipboardStatus = 'enabled';
            }
        };
    });
}

// Check if editing is allowed.
var checkPublishing = () => {
    fetch("/publish/" + app.appName)
        .then((response) => {
            return response.json();
        })
        .then((response) => {
            if (response.code < 400) {
                app.publishingAllowed = true;
                app.publishingIdle = true;
            }
            if (response.code === 201) {
                app.publishingIdle = false;
                setTimeout(() => {
                    checkPublishing();
                }, 1000);
            }
        });
}
// checkPublishing();

// Fetch RTC configuration containing STUN/TURN servers.
fetch("/turn/")
    .then(function (response) {
        return response.json();
    })
    .then((config) => {
        // for debugging, force use of relay server.
        webrtc.forceTurn = app.turnSwitch;
        audio_webrtc.forceTurn = app.turnSwitch;

        // get initial local resolution
        app.windowResolution = webrtc.input.getWindowResolution();

        if (app.scaleLocal === false) {
            webrtc.element.style.width = app.windowResolution[0]/window.devicePixelRatio+'px';
            webrtc.element.style.height = app.windowResolution[1]/window.devicePixelRatio+'px';
        }

        if (config.iceServers.length > 1) {
            app.debugEntries.push(applyTimestamp("[app] using TURN servers: " + config.iceServers[1].urls.join(", ")));
        } else {
            app.debugEntries.push(applyTimestamp("[app] no TURN servers found."));
        }
        webrtc.rtcPeerConfig = config;
        audio_webrtc.rtcPeerConfig = config;
        webrtc.connect();
        audio_webrtc.connect();
    });
