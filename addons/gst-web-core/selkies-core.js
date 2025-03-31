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

import { GamepadManager } from './lib/gamepad.js';
import { Input } from './lib/input.js';
import { WebRTCDemo } from './lib/webrtc.js';
import { WebRTCDemoSignalling } from './lib/signalling.js';

var webrtc;
var audio_webrtc;
var signalling;
var audio_signalling;

window.onload = () => {
  'use strict';
}

function getCookieValue(a) {
  var b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
  return b ? b.pop() : '';
}

const appName = window.location.pathname.endsWith("/") &&
  (window.location.pathname.split("/")[1]) || "webrtc";
let videoBitRate = 8000;
let videoFramerate = 60;
let audioBitRate = 128000;
let showStart = true;
const logEntries = [];
const debugEntries = [];
let status = 'connecting';
let loadingText = '';
let clipboardStatus = 'disabled';
let windowResolution = "";
let encoderName = "";
const gamepad = {
  gamepadState: 'disconnected',
  gamepadName: 'none',
};
const connectionStat = {
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
  connectionAvailableBandwidth: 0
};
const gpuStat = {
  gpuLoad: 0,
  gpuMemoryTotal: 0,
  gpuMemoryUsed: 0
};
const cpuStat = {
  serverCPUUsage: 0,
  serverMemoryTotal: 0,
  serverMemoryUsed: 0
};
let serverLatency = 0;
let resizeRemote = true;
let scaleLocal = false;
let debug = false;
let turnSwitch = false;
let publishingAllowed = false;
let publishingIdle = false;
let publishingError = "";
let publishingAppName = "";
let publishingAppDisplayName = "";
let publishingAppDescription = "";
let publishingAppIcon = "";
let publishingValid = false;

let statusDisplayElement;
let videoElement;
let audioElement;
let playButtonElement;
let spinnerElement;


const getIntParam = (key, default_value) => {
  const prefixedKey = appName + "_" + key;
  return (parseInt(window.localStorage.getItem(prefixedKey)) || default_value);
};

const setIntParam = (key, value) => {
  if (value === null) return;
  const prefixedKey = appName + "_" + key;
  window.localStorage.setItem(prefixedKey, value.toString());
};

const getBoolParam = (key, default_value) => {
  const prefixedKey = appName + "_" + key;
  var v = window.localStorage.getItem(prefixedKey);
  if (v === null) {
    return default_value;
  } else {
    return (v.toString().toLowerCase() === "true");
  }
};

const setBoolParam = (key, value) => {
  if (value === null) return;
  const prefixedKey = appName + "_" + key;
  window.localStorage.setItem(prefixedKey, value.toString());
};

const getUsername = () => {
  return (getCookieValue("broker_" + appName) || "webrtc").split("#")[0];
};

const enterFullscreen = () => {
  if (webrtc && 'input' in webrtc && 'enterFullscreen' in webrtc.input) {
    webrtc.input.enterFullscreen();
  }
};

const playStream = () => {
  webrtc.playStream();
  audio_webrtc.playStream();
  showStart = false;
  playButtonElement.classList.add('hidden');
  statusDisplayElement.classList.add('hidden');
};

const enableClipboard = () => {
  navigator.clipboard.readText()
    .then(text => {
      webrtc._setStatus("clipboard enabled");
      webrtc.sendDataChannelMessage("cr");
    })
    .catch(err => {
      webrtc._setError('Failed to read clipboard contents: ' + err);
    });
};

const publish = () => {
  var data = {
    name: publishingAppName,
    displayName: publishingAppDisplayName,
    description: publishingAppDescription,
    icon: publishingAppIcon,
  }
  console.log("Publishing new image", data);

  fetch("./publish/" + appName, {
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
        publishingIdle = false;
        checkPublishing();
      } else {
        publishingError = response.status;
        updatePublishingErrorDisplay();
      }
    });
};


const updateStatusDisplay = () => {
  statusDisplayElement.textContent = loadingText;
};

const appendLogEntry = (message) => {
  logEntries.push(applyTimestamp("[signalling] " + message));
  updateLogOutput();
};

const appendLogError = (message) => {
  logEntries.push(applyTimestamp("[signalling] [ERROR] " + message));
  updateLogOutput();
};

const appendDebugEntry = (message) => {
  debugEntries.push("[signalling] " + message);
  updateDebugOutput();
};


const updateLogOutput = () => {
  // need messsage posts
};

const updateDebugOutput = () => {
  // need message posts
};


const updatePublishingErrorDisplay = () => {
  //publishingErrorElement.textContent = publishingError;
};

const injectCSS = () => {
  const style = document.createElement('style');
  style.textContent = `
body {
  font-family: sans-serif;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #000;
  color: #fff;
}
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.video-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  position: relative;
}
video {
  max-width: 100%;
  max-height: 100%;
  width: 100vw;
  height: 100vh;
  object-fit: contain;
}
.spinner-container {
  position: absolute;
  top: calc(50% - 1rem);
  left: calc(50% - 1rem);
  width: 2rem;
  height: 2rem;
  border: 0.25rem solid #ffc000;
  border-bottom: 0.25rem solid rgba(255,255,255,0);
  border-radius: 50%;
  -webkit-animation: spin 1s linear infinite;
  animation: spin 1s linear infinite;
  z-index: 9999;
  background-color: #000;
}
.spinner--hidden {
  display: none;
}
@-webkit-keyframes spin {
  to {
    -webkit-transform: rotate(360deg);
    transform: rotate(360deg);
  }
}
@keyframes spin {
  to {
    -webkit-transform: rotate(360deg);
    transform: rotate(360deg);
  }
}
.hidden {
  display: none !important;
}
.video.scale {
  width: auto;
  height: auto;
}
.video {}
.status-bar {
  padding: 5px;
  background-color: #000;
  color: #fff;
  text-align: center;
}
#playButton {
  padding: 15px 30px;
  font-size: 1.5em;
  cursor: pointer;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  backdrop-filter: blur(5px);
}
  `;
  document.head.appendChild(style);
};


const initializeUI = () => {
  injectCSS();

  document.title = "Selkies - " + appName;

  const appDiv = document.getElementById('app');

  statusDisplayElement = document.createElement('div');
  statusDisplayElement.id = 'status-display';
  statusDisplayElement.className = 'status-bar';
  statusDisplayElement.textContent = 'Connecting...';
  appDiv.appendChild(statusDisplayElement);

  const videoContainer = document.createElement('div');
  videoContainer.className = 'video-container';
  appDiv.appendChild(videoContainer);

  videoElement = document.createElement('video');
  videoElement.id = 'stream';
  videoElement.className = 'video';
  videoElement.autoplay = true;
  videoElement.playsInline = true;
  videoContainer.appendChild(videoElement);

  audioElement = document.createElement('audio');
  audioElement.id = 'audio_stream';
  audioElement.style.display = 'none';
  audioElement.autoplay = true;
  audioElement.playsInline = true;
  videoContainer.appendChild(audioElement);

  spinnerElement = document.createElement('div');
  spinnerElement.id = 'spinner';
  spinnerElement.className = 'spinner-container';
  videoContainer.appendChild(spinnerElement);

  playButtonElement = document.createElement('button');
  playButtonElement.id = 'playButton';
  playButtonElement.className = 'hidden';
  playButtonElement.textContent = 'Play Stream';
  videoContainer.appendChild(playButtonElement);


  videoBitRate = getIntParam("videoBitRate", videoBitRate);
  videoFramerate = getIntParam("videoFramerate", videoFramerate);
  audioBitRate = getIntParam("audioBitRate", audioBitRate);
  resizeRemote = getBoolParam("resizeRemote", resizeRemote);
  scaleLocal = getBoolParam("scaleLocal", scaleLocal);
  debug = getBoolParam("debug", debug);
  turnSwitch = getBoolParam("turnSwitch", turnSwitch);

  updateStatusDisplay();
  updateLogOutput();
  updateDebugOutput();
  updatePublishingErrorDisplay();

  playButtonElement.addEventListener('click', playStream);
};


window.addEventListener('message', receiveMessage, false);

function receiveMessage(event) {
  if (event.origin !== window.location.origin) {
    console.log("Message received from:", event.origin,
      "ignored, expected origin:", window.location.origin);
    return;
  }

  var message = event.data;
  if (typeof message === 'object' && message !== null) {
    if (message.type === 'settings') {
      handleSettingsMessage(message.settings);
    } else if (message.type === 'getStats') {
      sendStatsMessage();
    }
  }
}

function handleSettingsMessage(settings) {
  console.log("Settings received via message:", settings);
  if (settings.videoBitRate !== undefined) {
    videoBitRate = parseInt(settings.videoBitRate);
    webrtc.sendDataChannelMessage('vb,' + videoBitRate);
    setIntParam("videoBitRate", videoBitRate);
  }
  if (settings.videoFramerate !== undefined) {
    videoFramerate = parseInt(settings.videoFramerate);
    console.log("video framerate changed to " + videoFramerate);
    webrtc.sendDataChannelMessage('_arg_fps,' + videoFramerate);
    setIntParam("videoFramerate", videoFramerate);
  }
  if (settings.resizeRemote !== undefined) {
    resizeRemote = settings.resizeRemote;
    console.log("resize remote changed to " + resizeRemote);
    windowResolution = webrtc.input.getWindowResolution();
    var res = windowResolution[0] + "x" + windowResolution[1];
    webrtc.sendDataChannelMessage('_arg_resize,' + resizeRemote + "," + res);
    setBoolParam("resizeRemote", resizeRemote);
  }
  if (settings.scaleLocal !== undefined) {
    scaleLocal = settings.scaleLocal;
    console.log("scaleLocal changed to " + scaleLocal);
    if (scaleLocal === true) {
      videoElement.style.width = '';
      videoElement.style.height = '';
      videoElement.setAttribute("class", "video scale");
    } else {
      videoElement.setAttribute("class", "video");
    }
    setBoolParam("scaleLocal", scaleLocal);
  }
  if (settings.audioBitRate !== undefined) {
    audioBitRate = parseInt(settings.audioBitRate);
    webrtc.sendDataChannelMessage('ab,' + audioBitRate);
    setIntParam("audioBitRate", audioBitRate);
  }
  if (settings.turnSwitch !== undefined) {
    turnSwitch = settings.turnSwitch;
    setBoolParam("turnSwitch", turnSwitch);
    if (webrtc === undefined || webrtc.peerConnection === null) return;
    setTimeout(() => {
      document.location.reload();
    }, 700);
  }
  if (settings.debug !== undefined) {
    debug = settings.debug;
    setBoolParam("debug", debug);
    if (webrtc === undefined || webrtc.peerConnection === null) return;
    setTimeout(() => {
      document.location.reload();
    }, 700);
  }
}

function sendStatsMessage() {
  const stats = {
    connection: connectionStat,
    gpu: gpuStat,
    cpu: cpuStat,
    encoderName: encoderName
  };
  window.parent.postMessage({ type: 'stats', data: stats },
    window.location.origin);
}


document.addEventListener('DOMContentLoaded', () => {
  initializeUI();


  videoElement.addEventListener('loadeddata', (e) => {
    webrtc.input.getCursorScaleFactor();
  });

  var pathname = window.location.pathname;
  var pathname = pathname.slice(0, pathname.lastIndexOf("/") + 1);
  var protocol = (location.protocol == "http:" ? "ws://" : "wss://");
  signalling = new WebRTCDemoSignalling(
    new URL(protocol + window.location.host + pathname + appName +
      "/signalling/"));
  webrtc = new WebRTCDemo(signalling, videoElement, 1);
  audio_signalling = new WebRTCDemoSignalling(
    new URL(protocol + window.location.host + pathname + appName +
      "/signalling/"));
  audio_webrtc = new WebRTCDemo(audio_signalling, audioElement, 3);
  signalling.setInput(webrtc.input);
  audio_signalling.setInput(audio_webrtc.input);

  window.applyTimestamp = (msg) => {
    var now = new Date();
    var ts = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
    return "[" + ts + "]" + " " + msg;
  };

  signalling.onstatus = (message) => {
    loadingText = message;
    appendLogEntry(message);
    updateStatusDisplay();
  };
  signalling.onerror = (message) => { appendLogError(message) };

  signalling.ondisconnect = () => {
    var checkconnect = status == checkconnect;
    console.log("signalling disconnected");
    status = 'connecting';
    updateStatusDisplay();
    videoElement.style.cursor = "auto";
    webrtc.reset();
    status = 'checkconnect';
    if (!checkconnect) audio_signalling.disconnect();
  };

  audio_signalling.onstatus = (message) => {
    loadingText = message;
    appendLogEntry(message);
    updateStatusDisplay();
  };
  audio_signalling.onerror = (message) => { appendLogError(message) };

  audio_signalling.ondisconnect = () => {
    var checkconnect = status == checkconnect;
    console.log("audio signalling disconnected");
    status = 'connecting';
    updateStatusDisplay();
    videoElement.style.cursor = "auto";
    audio_webrtc.reset();
    status = 'checkconnect';
    if (!checkconnect) signalling.disconnect();
  };

  webrtc.onstatus = (message) => {
    appendLogEntry(applyTimestamp("[webrtc] " + message))
  };
  webrtc.onerror = (message) => {
    appendLogError(applyTimestamp("[webrtc] [ERROR] " + message))
  };
  audio_webrtc.onstatus = (message) => {
    appendLogEntry(applyTimestamp("[audio webrtc] " + message))
  };
  audio_webrtc.onerror = (message) => {
    appendLogError(applyTimestamp("[audio webrtc] [ERROR] " + message))
  };

  if (debug) {
    signalling.ondebug = (message) => {
      appendDebugEntry("[signalling] " + message);
    };
    audio_signalling.ondebug = (message) => {
      appendDebugEntry("[audio signalling] " + message);
    };
    webrtc.ondebug = (message) => {
      appendDebugEntry(applyTimestamp("[webrtc] " + message))
    };
    audio_webrtc.ondebug = (message) => {
      appendDebugEntry(applyTimestamp("[audio webrtc] " + message))
    };
  }

  webrtc.ongpustats = async (data) => {
    gpuStat.gpuLoad = Math.round(data.load * 100);
    gpuStat.gpuMemoryTotal = data.memory_total;
    gpuStat.gpuMemoryUsed = data.memory_used;
  };

  var videoConnected = "";
  var audioConnected = "";
  var statWatchEnabled = false;
  function enableStatWatch() {
    var videoBytesReceivedStart = 0;
    var audioBytesReceivedStart = 0;
    var previousVideoJitterBufferDelay = 0.0;
    var previousVideoJitterBufferEmittedCount = 0;
    var previousAudioJitterBufferDelay = 0.0;
    var previousAudioJitterBufferEmittedCount = 0;
    var statsStart = new Date().getTime() / 1000;
    var statsLoop = setInterval(async () => {
      if (videoConnected !== "connected" || audioConnected !== "connected") {
        clearInterval(statsLoop);
        statWatchEnabled = false;
        return;
      }
      webrtc.getConnectionStats().then((stats) => {
        if (videoConnected !== "connected" || audioConnected !== "connected") {
          clearInterval(statsLoop);
          statWatchEnabled = false;
          return;
        }
        audio_webrtc.getConnectionStats().then((audioStats) => {
          if (videoConnected !== "connected" ||
            audioConnected !== "connected") {
            clearInterval(statsLoop);
            statWatchEnabled = false;
            return;
          }
          statWatchEnabled = true;

          var now = new Date().getTime() / 1000;

          connectionStat.connectionStatType =
            stats.general.connectionType == audioStats.general.connectionType ?
            stats.general.connectionType :
            (stats.general.connectionType + " / " +
              audioStats.general.connectionType);
          connectionStat.connectionBytesReceived =
            ((stats.general.bytesReceived + audioStats.general.bytesReceived) *
              1e-6).toFixed(2) + " MBytes";
          connectionStat.connectionBytesSent =
            ((stats.general.bytesSent + audioStats.general.bytesSent) *
              1e-6).toFixed(2) + " MBytes";
          connectionStat.connectionAvailableBandwidth =
            ((parseInt(stats.general.availableReceiveBandwidth) +
              parseInt(audioStats.general.availableReceiveBandwidth)) /
              1e+6).toFixed(2) + " mbps";

          connectionStat.connectionPacketsReceived = stats.video.packetsReceived;
          connectionStat.connectionPacketsLost = stats.video.packetsLost;
          connectionStat.connectionCodec = stats.video.codecName;
          connectionStat.connectionVideoDecoder = stats.video.decoder;
          connectionStat.connectionResolution =
            stats.video.frameWidth + "x" + stats.video.frameHeight;
          connectionStat.connectionFrameRate = stats.video.framesPerSecond;
          connectionStat.connectionVideoBitrate =
            (((stats.video.bytesReceived - videoBytesReceivedStart) /
              (now - statsStart)) * 8 / 1e+6).toFixed(2);
          videoBytesReceivedStart = stats.video.bytesReceived;

          connectionStat.connectionPacketsReceived +=
            audioStats.audio.packetsReceived;
          connectionStat.connectionPacketsLost += audioStats.audio.packetsLost;
          connectionStat.connectionAudioCodecName = audioStats.audio.codecName;
          connectionStat.connectionAudioBitrate =
            (((audioStats.audio.bytesReceived - audioBytesReceivedStart) /
              (now - statsStart)) * 8 / 1e+3).toFixed(2);
          audioBytesReceivedStart = audioStats.audio.bytesReceived;

          connectionStat.connectionVideoLatency = parseInt(Math.round(
            connectionStat.connectionVideoLatency +
            (1000.0 * (stats.video.jitterBufferDelay -
              previousVideoJitterBufferDelay) /
              (stats.video.jitterBufferEmittedCount -
                previousVideoJitterBufferEmittedCount) || 0)));
          previousVideoJitterBufferDelay = stats.video.jitterBufferDelay;
          previousVideoJitterBufferEmittedCount =
            stats.video.jitterBufferEmittedCount;
          connectionStat.connectionAudioLatency = parseInt(Math.round(
            connectionStat.connectionAudioLatency +
            (1000.0 * (audioStats.audio.jitterBufferDelay -
              previousAudioJitterBufferDelay) /
              (audioStats.audio.jitterBufferEmittedCount -
                previousAudioJitterBufferEmittedCount) || 0)));
          previousAudioJitterBufferDelay = audioStats.audio.jitterBufferDelay;
          previousAudioJitterBufferEmittedCount =
            audioStats.audio.jitterBufferEmittedCount;

          connectionStat.connectionLatency = parseInt(Math.round(Math.max(
            connectionStat.connectionVideoLatency,
            connectionStat.connectionAudioLatency)));

          statsStart = now;


          sendStatsMessage();

          webrtc.sendDataChannelMessage("_stats_video," +
            JSON.stringify(stats.allReports));
          webrtc.sendDataChannelMessage("_stats_audio," +
            JSON.stringify(audioStats.allReports));
        });
      });
    }, 1000);
  }

  webrtc.onconnectionstatechange = (state) => {
    videoConnected = state;
    if (videoConnected === "connected") {
      webrtc.peerConnection.getReceivers().forEach((receiver) => {
        let intervalLoop = setInterval(async () => {
          if (receiver.track.readyState !== "live" ||
            receiver.transport.state !== "connected") {
            clearInterval(intervalLoop);
            return;
          } else {
            receiver.jitterBufferTarget = receiver.jitterBufferDelayHint =
              receiver.playoutDelayHint = 0;
          }
        }, 15);
      });
    }
    if (videoConnected === "connected" && audioConnected === "connected") {
      status = state;
      updateStatusDisplay();
      if (!statWatchEnabled) {
        enableStatWatch();
      }
    } else {
      status = state === "connected" ? audioConnected : videoConnected;
      updateStatusDisplay();
    }
  };
  audio_webrtc.onconnectionstatechange = (state) => {
    audioConnected = state;
    if (audioConnected === "connected") {
      audio_webrtc.peerConnection.getReceivers().forEach((receiver) => {
        let intervalLoop = setInterval(async () => {
          if (receiver.track.readyState !== "live" ||
            receiver.transport.state !== "connected") {
            clearInterval(intervalLoop);
            return;
          } else {
            receiver.jitterBufferTarget = receiver.jitterBufferDelayHint =
              receiver.playoutDelayHint = 0;
          }
        }, 15);
      });
    }
    if (audioConnected === "connected" && videoConnected === "connected") {
      status = state;
      updateStatusDisplay();
      if (!statWatchEnabled) {
        enableStatWatch();
      }
    } else {
      status = state === "connected" ? videoConnected : audioConnected;
      updateStatusDisplay();
    }
  };

  webrtc.ondatachannelopen = () => {
    webrtc.input.ongamepadconnected = (gamepad_id) => {
      webrtc._setStatus('Gamepad connected: ' + gamepad_id);
      gamepad.gamepadState = "connected";
      gamepad.gamepadName = gamepad_id;
    }

    webrtc.input.ongamepaddisconnected = () => {
      webrtc._setStatus('Gamepad disconnected: ' + gamepad_id);
      gamepad.gamepadState = "disconnected";
      gamepad.gamepadName = "none";
    }

    webrtc.input.attach();

    setInterval(async () => {
      if (connectionStat.connectionFrameRate ===
        parseInt(connectionStat.connectionFrameRate, 10))
        webrtc.sendDataChannelMessage('_f,' +
          connectionStat.connectionFrameRate);
      if (connectionStat.connectionLatency ===
        parseInt(connectionStat.connectionLatency, 10))
        webrtc.sendDataChannelMessage('_l,' +
          connectionStat.connectionLatency);
    }, 5000);
  };

  webrtc.ondatachannelclose = () => {
    webrtc.input.detach();
  };

  webrtc.input.onmenuhotkey = () => {
    // toggleDrawer(); // Drawer toggle removed
  };

  webrtc.input.onresizeend = () => {
    windowResolution = webrtc.input.getWindowResolution();
    var newRes = parseInt(windowResolution[0]) + "x" +
      parseInt(windowResolution[1]);
    console.log(`Window size changed: ${windowResolution[0]}x${
      windowResolution[1]}, scaled to: ${newRes}`);
    webrtc.sendDataChannelMessage("r," + newRes);
    webrtc.sendDataChannelMessage("s," + window.devicePixelRatio);
  };

  webrtc.onplaystreamrequired = () => {
    statusDisplayElement.classList.add('hidden');
    spinnerElement.classList.add('hidden');
    if (showStart) {
      playButtonElement.classList.remove('hidden');
    }
  };

  audio_webrtc.onplaystreamrequired = () => {
    statusDisplayElement.classList.add('hidden');
    spinnerElement.classList.add('hidden');
    if (showStart) {
      playButtonElement.classList.remove('hidden');
    }
  };

  window.addEventListener('focus', () => {
    webrtc.sendDataChannelMessage("kr");

    navigator.clipboard.readText()
      .then(text => {
        webrtc.sendDataChannelMessage("cw," + btoa(text));
      })
      .catch(err => {
        webrtc._setStatus('Failed to read clipboard contents: ' + err);
      });
  });
  window.addEventListener('blur', () => {
    webrtc.sendDataChannelMessage("kr");
  });

  webrtc.onclipboardcontent = (content) => {
    if (clipboardStatus === 'enabled') {
      navigator.clipboard.writeText(content)
        .catch(err => {
          webrtc._setStatus('Could not copy text to clipboard: ' + err);
        });
    }
  };

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
  };

  webrtc.onsystemaction = (action) => {
    webrtc._setStatus("Executing system action: " + action);
    if (action === 'reload') {
      setTimeout(() => {
        signalling.disconnect();
      }, 700);
    } else if (action.startsWith('framerate')) {
      const framerateSetting = getIntParam("videoFramerate", null);
      if (framerateSetting !== null) {
        videoFramerate = framerateSetting;
      } else {
        videoFramerate = parseInt(action.split(",")[1]);
      }
    } else if (action.startsWith('video_bitrate')) {
      const videoBitrateSetting = getIntParam("videoBitRate", null);
      if (videoBitrateSetting !== null) {
        videoBitRate = videoBitrateSetting;
      } else {
        videoBitRate = parseInt(action.split(",")[1]);
      }
    } else if (action.startsWith('audio_bitrate')) {
      const audioBitrateSetting = getIntParam("audioBitRate", null);
      if (audioBitrateSetting !== null) {
        audioBitRate = audioBitrateSetting;
      } else {
        audioBitRate = parseInt(action.split(",")[1]);
      }
    } else if (action.startsWith('resize')) {
      const resizeSetting = getBoolParam("resize", null);
      if (resizeSetting !== null) {
        resizeRemote = resizeSetting;
      } else {
        resizeRemote = (action.split(",")[1].toLowerCase() === 'true');
        if (resizeRemote === false && getBoolParam("scaleLocal", null) === null) {
          scaleLocal = true;
        }
      }
    } else if (action.startsWith("resolution")) {
      var remote_res = action.split(",")[1];
      console.log("received remote resolution of: " + remote_res);
      if (resizeRemote === true) {
        var toks = remote_res.split("x");
        videoElement.style.width = toks[0] / window.devicePixelRatio + 'px';
        videoElement.style.height = toks[1] / window.devicePixelRatio + 'px';

        webrtc.input.getCursorScaleFactor({ remoteResolutionEnabled: true });
      }
    } else if (action.startsWith("local_scaling")) {
      const scalingSetting = getBoolParam("scaleLocal", null);
      if (scalingSetting !== null) {
        scaleLocal = scalingSetting;
      } else {
        scaleLocal = (action.split(",")[1].toLowerCase() === 'true');
      }
      if (scaleLocal === true) {
        videoElement.style.width = '';
        videoElement.style.height = '';
        videoElement.setAttribute("class", "video scale");
      } else {
        videoElement.setAttribute("class", "video");
      }
    } else if (action.startsWith("encoder")) {
      if (action.split(",")[1].startsWith("nv") ||
        action.split(",")[1].startsWith("va")) {
        encoderName = "hardware" + " (" + action.split(",")[1] + ")";
      } else {
        encoderName = "software" + " (" + action.split(",")[1] + ")";
      }
    } else {
      webrtc._setStatus('Unhandled system action: ' + action);
    }
  };

  webrtc.onlatencymeasurement = (latency_ms) => {
    serverLatency = latency_ms * 2.0;
  };

  webrtc.onsystemstats = async (stats) => {
    if (stats.cpu_percent !== undefined || stats.mem_total !== undefined ||
      stats.mem_used !== undefined) {
      if (stats.cpu_percent !== undefined)
        cpuStat.serverCPUUsage = stats.cpu_percent.toFixed(0);
      if (stats.mem_total !== undefined)
        cpuStat.serverMemoryTotal = stats.mem_total;
      if (stats.mem_used !== undefined)
        cpuStat.serverMemoryUsed = stats.mem_used;
    }
  };

  if (navigator.permissions) {
    navigator.permissions.query({
      name: 'clipboard-read'
    }).then(permissionStatus => {
      if (permissionStatus.state === 'granted') {
        clipboardStatus = 'enabled';
      }

      permissionStatus.onchange = () => {
        if (permissionStatus.state === 'granted') {
          clipboardStatus = 'enabled';
        }
      };
    });
  }

  var checkPublishing = () => {
    fetch("./publish/" + appName)
      .then((response) => {
        return response.json();
      })
      .then((response) => {
        if (response.code < 400) {
          publishingAllowed = true;
          publishingIdle = true;
        }
        if (response.code === 201) {
          publishingIdle = false;
          setTimeout(() => {
            checkPublishing();
          }, 1000);
        }
      });
  };

  fetch("./turn")
    .then(function (response) {
      return response.json();
    })
    .then((config) => {
      webrtc.forceTurn = turnSwitch;
      audio_webrtc.forceTurn = turnSwitch;

      windowResolution = webrtc.input.getWindowResolution();

      if (scaleLocal === false) {
        videoElement.style.width = windowResolution[0] / window.devicePixelRatio + 'px';
        videoElement.style.height = windowResolution[1] / window.devicePixelRatio + 'px';
      }

      if (config.iceServers.length > 1) {
        appendDebugEntry(applyTimestamp("[app] using TURN servers: " +
          config.iceServers[1].urls.join(", ")));
      } else {
        appendDebugEntry(applyTimestamp("[app] no TURN servers found."));
      }
      webrtc.rtcPeerConfig = config;
      audio_webrtc.rtcPeerConfig = config;
      webrtc.connect();
      audio_webrtc.connect();
    });
});
