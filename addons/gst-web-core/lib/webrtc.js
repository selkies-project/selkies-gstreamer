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


/*eslint no-unused-vars: ["error", { "vars": "local" }]*/

import { GamepadManager } from './gamepad.js';
import { Input } from './input.js';
import { WebRTCDemoSignalling } from './signalling.js';

/**
 * @typedef {Object} WebRTCDemo
 * @property {function} ondebug - Callback fired when new debug message is set.
 * @property {function} onstatus - Callback fired when new status message is set.
 * @property {function} onerror - Callback fired when new error message is set.
 * @property {function} onconnectionstatechange - Callback fired when peer connection state changes.
 * @property {function} ondatachannelclose - Callback fired when data channel is closed.
 * @property {function} ondatachannelopen - Callback fired when data channel is opened.
 * @property {function} onplaystreamrequired - Callback fired when user interaction is required before playing the stream.
 * @property {function} onclipboardcontent - Callback fired when clipboard content from the remote host is received.
 * @property {function} getConnectionStats - Returns promise that resolves with connection stats.
 * @property {Objet} rtcPeerConfig - RTC configuration containing ICE servers and other connection properties.
 * @property {boolean} forceTurn - Force use of TURN server.
 * @property {fucntion} sendDataChannelMessage - Send a message to the peer though the data channel.
 */
export class WebRTCDemo {
    /**
     * Interface to WebRTC demo.
     *
     * @constructor
     * @param {WebRTCDemoSignalling} [signalling]
     *    Instance of WebRTCDemoSignalling used to communicate with signalling server.
     * @param {Element} [element]
     *    Element to attach stream to.
     */
    constructor(signalling, element, peer_id) {
        /**
         * @type {WebRTCDemoSignalling}
         */
        this.signalling = signalling;

        /**
         * @type {Element}
         */
        this.element = element;

        /**
         * @type {Element}
         */
        this.peer_id = peer_id;

        /**
         * @type {boolean}
         */
        this.forceTurn = false;

        /**
         * @type {Object}
         */
        this.rtcPeerConfig = {
            "lifetimeDuration": "86400s",
            "iceServers": [
                {
                    "urls": [
                        "stun:stun.l.google.com:19302"
                    ]
                },
            ],
            "blockStatus": "NOT_BLOCKED",
            "iceTransportPolicy": "all"
        };

        /**
         * @type {RTCPeerConnection}
         */
        this.peerConnection = null;

        /**
         * @type {function}
         */
        this.onstatus = null;

        /**
         * @type {function}
         */
        this.ondebug = null;

        /**
         * @type {function}
         */
        this.onerror = null;

        /**
         * @type {function}
         */
        this.onconnectionstatechange = null;

        /**
         * @type {function}
         */
        this.ondatachannelopen = null;

        /**
         * @type {function}
         */
        this.ondatachannelclose = null;

        /**
         * @type {function}
         */
        this.ongpustats = null;

        /**
         * @type {function}
         */
        this.onlatencymeasurement = null;

        /**
         * @type {function}
         */
        this.onplaystreamrequired = null;

        /**
         * @type {function}
         */
        this.onclipboardcontent = null;

        /**
         * @type {function}
         */
        this.onsystemaction = null;

        /**
         * @type {function}
         */
        this.oncursorchange = null;

         /**
          * @type {Map}
          */
        this.cursor_cache = new Map();

        /**
         * @type {function}
         */
        this.onsystemstats = null;

        // Bind signalling server callbacks.
        this.signalling.onsdp = this._onSDP.bind(this);
        this.signalling.onice = this._onSignallingICE.bind(this);

        /**
         * @type {boolean}
         */
        this._connected = false;

        /**
         * @type {RTCDataChannel}
         */
        this._send_channel = null;

        /**
         * @type {Input}
         */
        this.input = new Input(this.element, (data) => {
            if (this._connected && this._send_channel !== null && this._send_channel.readyState === 'open') {
                this._setDebug("data channel: " + data);
                this._send_channel.send(data);
            }
        });
    }

    /**
     * Sets status message.
     *
     * @private
     * @param {String} message
     */
    _setStatus(message) {
        if (this.onstatus !== null) {
            this.onstatus(message);
        }
    }

    /**
     * Sets debug message.
     *
     * @private
     * @param {String} message
     */
    _setDebug(message) {
        if (this.ondebug !== null) {
            this.ondebug(message);
        }
    }

    /**
     * Sets error message.
     *
     * @private
     * @param {String} message
     */
    _setError(message) {
        if (this.onerror !== null) {
            this.onerror(message);
        }
    }

    /**
     * Sets connection state
     * @param {String} state
     */
    _setConnectionState(state) {
        if (this.onconnectionstatechange !== null) {
            this.onconnectionstatechange(state);
        }
    }

    /**
     * Handles incoming ICE candidate from signalling server.
     *
     * @param {RTCIceCandidate} icecandidate
     */
    _onSignallingICE(icecandidate) {
        this._setDebug("received ice candidate from signalling server: " + JSON.stringify(icecandidate));
        if (this.forceTurn && JSON.stringify(icecandidate).indexOf("relay") < 0) { // if no relay address is found, assuming it means no TURN server
            this._setDebug("Rejecting non-relay ICE candidate: " + JSON.stringify(icecandidate));
            return;
        }
        this.peerConnection.addIceCandidate(icecandidate).catch(this._setError);
    }

    /**
     * Handler for ICE candidate received from peer connection.
     * If ice is null, then all candidates have been received.
     *
     * @event
     * @param {RTCPeerConnectionIceEvent} event - The event: https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnectionIceEvent
     */
    _onPeerICE(event) {
        if (event.candidate === null) {
            this._setStatus("Completed ICE candidates from peer connection");
            return;
        }
        this.signalling.sendICE(event.candidate);
    }

    /**
     * Handles incoming SDP from signalling server.
     * Sets the remote description on the peer connection,
     * creates an answer with a local description and sends that to the peer.
     *
     * @param {RTCSessionDescription} sdp
     */
    _onSDP(sdp) {
        if (sdp.type != "offer") {
            this._setError("received SDP was not type offer.");
            return;
        }
        console.log("Received remote SDP", sdp);
        this.peerConnection.setRemoteDescription(sdp).then(() => {
            this._setDebug("received SDP offer, creating answer");
            this.peerConnection.createAnswer()
                .then((local_sdp) => {
                    // Set sps-pps-idr-in-keyframe=1
                    if (!(/[^-]sps-pps-idr-in-keyframe=1[^\d]/gm.test(local_sdp.sdp)) && (/[^-]packetization-mode=/gm.test(local_sdp.sdp))) {
                        console.log("Overriding WebRTC SDP to include sps-pps-idr-in-keyframe=1");
                        if (/[^-]sps-pps-idr-in-keyframe=\d+/gm.test(local_sdp.sdp)) {
                            local_sdp.sdp = local_sdp.sdp.replace(/sps-pps-idr-in-keyframe=\d+/gm, 'sps-pps-idr-in-keyframe=1');
                        } else {
                            local_sdp.sdp = local_sdp.sdp.replace('packetization-mode=', 'sps-pps-idr-in-keyframe=1;packetization-mode=');
                        }
                    }
                    if (local_sdp.sdp.indexOf('multiopus') === -1) {
                        // Override SDP to enable stereo on WebRTC Opus with Chromium, must be munged before the Local Description
                        if (!(/[^-]stereo=1[^\d]/gm.test(local_sdp.sdp)) && (/[^-]useinbandfec=/gm.test(local_sdp.sdp))) {
                            console.log("Overriding WebRTC SDP to allow stereo audio");
                            if (/[^-]stereo=\d+/gm.test(local_sdp.sdp)) {
                                local_sdp.sdp = local_sdp.sdp.replace(/stereo=\d+/gm, 'stereo=1');
                            } else {
                                local_sdp.sdp = local_sdp.sdp.replace('useinbandfec=', 'stereo=1;useinbandfec=');
                            }
                        }
                        // OPUS_FRAME: Override SDP to reduce packet size to 10 ms
                        if (!(/[^-]minptime=10[^\d]/gm.test(local_sdp.sdp)) && (/[^-]useinbandfec=/gm.test(local_sdp.sdp))) {
                            console.log("Overriding WebRTC SDP to allow low-latency audio packet");
                            if (/[^-]minptime=\d+/gm.test(local_sdp.sdp)) {
                                local_sdp.sdp = local_sdp.sdp.replace(/minptime=\d+/gm, 'minptime=10');
                            } else {
                                local_sdp.sdp = local_sdp.sdp.replace('useinbandfec=', 'minptime=10;useinbandfec=');
                            }
                        }
                    }
                    console.log("Created local SDP", local_sdp);
                    this.peerConnection.setLocalDescription(local_sdp).then(() => {
                        this._setDebug("Sending SDP answer");
                        this.signalling.sendSDP(this.peerConnection.localDescription);
                    });
                }).catch(() => {
                    this._setError("Error creating local SDP");
                });
        });
    }

    /**
     * Handles local description creation from createAnswer.
     *
     * @param {RTCSessionDescription} local_sdp
     */
    _onLocalSDP(local_sdp) {
        this._setDebug("Created local SDP: " + JSON.stringify(local_sdp));
    }

    /**
     * Handles incoming track event from peer connection.
     *
     * @param {Event} event - Track event: https://developer.mozilla.org/en-US/docs/Web/API/RTCTrackEvent
     */
    _ontrack(event) {
        this._setStatus("Received incoming " + event.track.kind + " stream from peer");
        if (!this.streams) this.streams = [];
        this.streams.push([event.track.kind, event.streams]);
        if (event.track.kind === "video" || event.track.kind === "audio") {
            this.element.srcObject = event.streams[0];
            this.playStream();
        }
    }

    /**
     * Handles incoming data channel events from the peer connection.
     *
     * @param {RTCdataChannelEvent} event
     */
    _onPeerdDataChannel(event) {
        this._setStatus("Peer data channel created: " + event.channel.label);

        // Bind the data channel event handlers.
        this._send_channel = event.channel;
        this._send_channel.onmessage = this._onPeerDataChannelMessage.bind(this);
        this._send_channel.onopen = () => {
            if (this.ondatachannelopen !== null)
                this.ondatachannelopen();
        };
        this._send_channel.onclose = () => {
            if (this.ondatachannelclose !== null)
                this.ondatachannelclose();
        };
    }

    /**
     * Handles messages from the peer data channel.
     *
     * @param {MessageEvent} event
     */
    _onPeerDataChannelMessage(event) {
        // Attempt to parse message as JSON
        var msg;
        try {
            msg = JSON.parse(event.data);
        } catch (e) {
            if (e instanceof SyntaxError) {
                this._setError("error parsing data channel message as JSON: " + event.data);
            } else {
                this._setError("failed to parse data channel message: " + event.data);
            }
            return;
        }

        this._setDebug("data channel message: " + event.data);

        if (msg.type === 'pipeline') {
            this._setStatus(msg.data.status);
        } else if (msg.type === 'gpu_stats') {
            if (this.ongpustats !== null) {
                this.ongpustats(msg.data);
            }
        } else if (msg.type === 'clipboard') {
            if (msg.data !== null) {
                var content = msg.data.content;
                var stringBytes = atob(content);
                var bytes = Uint8Array.from(stringBytes, (m) => m.codePointAt(0));
                var text = new TextDecoder().decode(bytes);
                this._setDebug("received clipboard contents, length: " + content.length);

                if (this.onclipboardcontent !== null) {
                    this.onclipboardcontent(text);
                }
            }
        } else if (msg.type === 'cursor') {
            if (this.oncursorchange !== null && msg.data !== null) {
                var curdata = msg.data.curdata;
                var handle = msg.data.handle;
                var hotspot = msg.data.hotspot;
                var override = msg.data.override;
                this._setDebug(`received new cursor contents, handle: ${handle}, hotspot: ${JSON.stringify(hotspot)} image length: ${curdata.length}`);
                this.oncursorchange(handle, curdata, hotspot, override);
            }
        } else if (msg.type === 'system') {
            if (msg.action !== null) {
                this._setDebug("received system msg, action: " + msg.data.action);
                var action = msg.data.action;
                if (this.onsystemaction !== null) {
                    this.onsystemaction(action);
                }
            }
        } else if (msg.type === 'ping') {
            this._setDebug("received server ping: " + JSON.stringify(msg.data));
            this.sendDataChannelMessage("pong," + new Date().getTime() / 1000);
        } else if (msg.type === 'system_stats') {
            this._setDebug("received systems stats: " + JSON.stringify(msg.data));
            if (this.onsystemstats !== null) {
                this.onsystemstats(msg.data);
            }
        } else if (msg.type === 'latency_measurement') {
            if (this.onlatencymeasurement !== null) {
                this.onlatencymeasurement(msg.data.latency_ms);
            }
        } else {
            this._setError("Unhandled message received: " + msg.type);
        }
    }

    /**
     * Handler for peer connection state change.
     * Possible values for state:
     *   connected
     *   disconnected
     *   failed
     *   closed
     * @param {String} state
     */
    _handleConnectionStateChange(state) {
        switch (state) {
            case "connected":
                this._setStatus("Connection complete");
                this._connected = true;
                break;

            case "disconnected":
                this._setError("Peer connection disconnected");
                if (this._send_channel !== null && this._send_channel.readyState === 'open') {
                    this._send_channel.close();
                }
                this.element.load();
                break;

            case "failed":
                this._setError("Peer connection failed");
                this.element.load();
                break;
            default:
        }
    }

    /**
     * Sends message to peer data channel.
     *
     * @param {String} message
     */
    sendDataChannelMessage(message) {
        if (this._send_channel !== null && this._send_channel.readyState === 'open') {
            this._send_channel.send(message);
        } else {
            this._setError("attempt to send data channel message before channel was open.");
        }
    }

    /**
     * Handler for gamepad disconnect message.
     *
     * @param {number} gp_num - the gamepad number
     */
    onGamepadDisconnect(gp_num) {
        this._setStatus("gamepad: " + gp_num + ", disconnected");
    }

    /**
     * Gets connection stats. returns new promise.
     */
    getConnectionStats() {
        var pc = this.peerConnection;
        var connectionDetails = {
            // General connection stats
            general: {
                bytesReceived: 0, // from transport or candidate-pair
                bytesSent: 0, // from transport or candidate-pair
                connectionType: "NA", // from candidate-pair => remote-candidate
                currentRoundTripTime: null, // from candidate-pair
                availableReceiveBandwidth: 0, // from candidate-pair
            },

            // Video stats
            video: {
                bytesReceived: 0, //from incoming-rtp
                decoder: "NA", // from incoming-rtp
                frameHeight: 0, // from incoming-rtp
                frameWidth: 0, // from incoming-rtp
                framesPerSecond: 0, // from incoming-rtp
                packetsReceived: 0, // from incoming-rtp
                packetsLost: 0, // from incoming-rtp
                codecName: "NA", // from incoming-rtp => codec
                jitterBufferDelay: 0, // from incoming-rtp.jitterBufferDelay
                jitterBufferEmittedCount: 0, // from incoming-rtp.jitterBufferEmittedCount
            },

            // Audio stats
            audio: {
                bytesReceived: 0, // from incoming-rtp
                packetsReceived: 0, // from incoming-rtp
                packetsLost: 0, // from incoming-rtp
                codecName: "NA", // from incoming-rtp => codec
                jitterBufferDelay: 0, // from incoming-rtp.jitterBufferDelay
                jitterBufferEmittedCount: 0, // from incoming-rtp.jitterBufferEmittedCount
            },

            // DataChannel stats
            data: {
                bytesReceived: 0, // from data-channel
                bytesSent: 0, // from data-channel
                messagesReceived: 0, // from data-channel
                messagesSent: 0, // from data-channel
            }
        };

        return new Promise(function (resolve, reject) {
            // Statistics API:
            // https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_Statistics_API
            pc.getStats().then((stats) => {
                var reports = {
                    transports: {},
                    candidatePairs: {},
                    selectedCandidatePairId: null,
                    remoteCandidates: {},
                    codecs: {},
                    videoRTP: null,
                    videoTrack: null,
                    audioRTP: null,
                    audioTrack: null,
                    dataChannel: null,
                };

                var allReports = [];

                stats.forEach((report) => {
                    allReports.push(report);
                    if (report.type === "transport") {
                        reports.transports[report.id] = report;
                    } else if (report.type === "candidate-pair") {
                        reports.candidatePairs[report.id] = report;
                        if (report.selected === true) {
                            reports.selectedCandidatePairId = report.id;
                        }
                    } else if (report.type === "inbound-rtp") {
                        // Audio or video stat
                        // https://w3c.github.io/webrtc-stats/#streamstats-dict*
                        if (report.kind === "video") {
                            reports.videoRTP = report;
                        } else if (report.kind === "audio") {
                            reports.audioRTP = report;
                        }
                    } else if (report.type === "track") {
                        // Audio or video track
                        // https://w3c.github.io/webrtc-stats/#dom-rtcinboundrtpstreamstats-slicount
                        if (report.kind === "video") {
                            reports.videoTrack = report;
                        } else if (report.kind === "audio") {
                            reports.audioTrack = report;
                        }
                    } else if (report.type === "data-channel") {
                        reports.dataChannel = report;
                    } else if (report.type === "remote-candidate") {
                        reports.remoteCandidates[report.id] = report;
                    } else if (report.type === "codec") {
                        reports.codecs[report.id] = report;
                    }
                });

                // Extract video related stats.
                var videoRTP = reports.videoRTP;
                if (videoRTP !== null) {
                    connectionDetails.video.bytesReceived = videoRTP.bytesReceived;
                    // Recent WebRTC specs only expose decoderImplementation with media context capturing state
                    connectionDetails.video.decoder = videoRTP.decoderImplementation || "unknown";
                    connectionDetails.video.frameHeight = videoRTP.frameHeight;
                    connectionDetails.video.frameWidth = videoRTP.frameWidth;
                    connectionDetails.video.framesPerSecond = videoRTP.framesPerSecond;
                    connectionDetails.video.packetsReceived = videoRTP.packetsReceived;
                    connectionDetails.video.packetsLost = videoRTP.packetsLost;

                    // Extract video codec from found codecs.
                    var codec = reports.codecs[videoRTP.codecId];
                    if (codec !== undefined) {
                        connectionDetails.video.codecName = codec.mimeType.split("/")[1].toUpperCase();
                    }
                }

                // Extract audio related stats.
                var audioRTP = reports.audioRTP;
                if (audioRTP !== null) {
                    connectionDetails.audio.bytesReceived = audioRTP.bytesReceived;
                    connectionDetails.audio.packetsReceived = audioRTP.packetsReceived;
                    connectionDetails.audio.packetsLost = audioRTP.packetsLost;

                    // Extract audio codec from found codecs.
                    var codec = reports.codecs[audioRTP.codecId];
                    if (codec !== undefined) {
                        connectionDetails.audio.codecName = codec.mimeType.split("/")[1].toUpperCase();
                    }
                }

                var dataChannel = reports.dataChannel;
                if (dataChannel !== null) {
                    connectionDetails.data.bytesReceived = dataChannel.bytesReceived;
                    connectionDetails.data.bytesSent = dataChannel.bytesSent;
                    connectionDetails.data.messagesReceived = dataChannel.messagesReceived;
                    connectionDetails.data.messagesSent =  dataChannel.messagesSent;
                }

                // Extract transport stats (RTCTransportStats.selectedCandidatePairId or RTCIceCandidatePairStats.selected)
                if (Object.keys(reports.transports).length > 0) {
                    var transport = reports.transports[Object.keys(reports.transports)[0]];
                    connectionDetails.general.bytesReceived = transport.bytesReceived;
                    connectionDetails.general.bytesSent = transport.bytesSent;
                    reports.selectedCandidatePairId = transport.selectedCandidatePairId;
                } else if (reports.selectedCandidatePairId !== null) {
                    connectionDetails.general.bytesReceived = reports.candidatePairs[reports.selectedCandidatePairId].bytesReceived;
                    connectionDetails.general.bytesSent = reports.candidatePairs[reports.selectedCandidatePairId].bytesSent;
                }

                // Get the connection-pair
                if (reports.selectedCandidatePairId !== null) {
                    var candidatePair = reports.candidatePairs[reports.selectedCandidatePairId];
                    if (candidatePair !== undefined) {
                        if (candidatePair.availableIncomingBitrate !== undefined) {
                            connectionDetails.general.availableReceiveBandwidth = candidatePair.availableIncomingBitrate;
                        }
                        if (candidatePair.currentRoundTripTime !== undefined) {
                            connectionDetails.general.currentRoundTripTime = candidatePair.currentRoundTripTime;
                        }
                        var remoteCandidate = reports.remoteCandidates[candidatePair.remoteCandidateId];
                        if (remoteCandidate !== undefined) {
                            connectionDetails.general.connectionType = remoteCandidate.candidateType;
                        }
                    }
                }

                // Compute total packets received and lost
                connectionDetails.general.packetsReceived = connectionDetails.video.packetsReceived + connectionDetails.audio.packetsReceived;
                connectionDetails.general.packetsLost = connectionDetails.video.packetsLost + connectionDetails.audio.packetsLost;

                // Compute jitter buffer delay for video
                if (reports.videoRTP !== null) {
                    connectionDetails.video.jitterBufferDelay = reports.videoRTP.jitterBufferDelay;
                    connectionDetails.video.jitterBufferEmittedCount = reports.videoRTP.jitterBufferEmittedCount;
                }

                // Compute jitter buffer delay for audio
                if (reports.audioRTP !== null) {
                    connectionDetails.audio.jitterBufferDelay = reports.audioRTP.jitterBufferDelay;
                    connectionDetails.audio.jitterBufferEmittedCount = reports.audioRTP.jitterBufferEmittedCount;
                }

                // DEBUG
                connectionDetails.reports = reports;
                connectionDetails.allReports = allReports;

                resolve(connectionDetails);
            }).catch( (e) => reject(e));
        });
    }

    /**
     * Starts playing the stream.
     * Note that this must be called after some DOM interaction has already occured.
     * Chrome does not allow auto playing of videos without first having a DOM interaction.
     */
    // [START playStream]
    playStream() {
        this.element.load();

        var playPromise = this.element.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                this._setDebug("Stream is playing.");
            }).catch(() => {
                if (this.onplaystreamrequired !== null) {
                    this.onplaystreamrequired();
                } else {
                    this._setDebug("Stream play failed and no onplaystreamrequired was bound.");
                }
            });
        }
    }
    // [END playStream]

    /**
     * Initiate connection to signalling server.
     */
    connect() {
        // Create the peer connection object and bind callbacks.
        this.peerConnection = new RTCPeerConnection(this.rtcPeerConfig);
        this.peerConnection.ontrack = this._ontrack.bind(this);
        this.peerConnection.onicecandidate = this._onPeerICE.bind(this);
        this.peerConnection.ondatachannel = this._onPeerdDataChannel.bind(this);

        this.peerConnection.onconnectionstatechange = () => {
            // Local event handling.
            this._handleConnectionStateChange(this.peerConnection.connectionState);

            // Pass state to event listeners.
            this._setConnectionState(this.peerConnection.connectionState);
        };

        if (this.forceTurn) {
            this._setStatus("forcing use of TURN server");
            var config = this.peerConnection.getConfiguration();
            config.iceTransportPolicy = "relay";
            this.peerConnection.setConfiguration(config);
        }

        this.signalling.peer_id = this.peer_id;
        this.signalling.connect();
    }

    /**
     * Attempts to reset the webrtc connection by:
     *   1. Closing the data channel gracefully.
     *   2. Closing the RTC Peer Connection gracefully.
     *   3. Reconnecting to the signaling server.
     */
    reset() {
        // Clear cursor cache.
        this.cursor_cache = new Map();
        if (! this.peerConnection) {
            return;
        }
        var signalState = this.peerConnection.signalingState;
        if (this._send_channel !== null && this._send_channel.readyState === "open") {
            this._send_channel.close();
        }
        if (this.peerConnection !== null) this.peerConnection.close();
        if (signalState !== "stable") {
            setTimeout(() => {
                this.connect();
            }, 3000);
        } else {
            this.connect();
        }
    }

    capture_setup() {
        this.capture_canvas = document.getElementById("capture");
        this.capture_context = this.capture_canvas.getContext('2d');
        this.capture_canvas.width = this.input.m.frameW;
        this.capture_canvas.height = this.input.m.frameH;
    }

    capture() {
        this.capture_context.drawImage(this.element, 0, 0, this.capture_canvas.width, this.capture_canvas.height);
        var contextImageData = this.capture_context.getImageData(
            0,
            this.capture_canvas.height * 0.99,
            this.capture_canvas.width * 0.01,
            this.capture_canvas.height * 0.01,
        );
        return contextImageData.data;
    }

    send_escape_key() {
        this.sendDataChannelMessage("kd,65307");
        this.sendDataChannelMessage("ku,65307");
    }

    async sleep(milliseconds) {
        await new Promise((resolve, reject) => {
            setTimeout(() => {
                resolve();
            }, milliseconds);
        });
    }

    async fun() {
        this.capture_setup();
        this.have_fun = true;
        while (this.have_fun) {
            console.log('Capturing...');
            this.send_escape_key();
            const average_frame_brightnesses = [];
            const frame_durations = [];
            for (let frame_index = 0; frame_index < 20; frame_index++) {
                const frame_start = Date.now();
                const image_data = this.capture();
                const pixel_brightnesses = [];
                for (let pixel_index = 0; pixel_index < image_data.length / 4; pixel_index += 1) {
                    const r = image_data[pixel_index * 4 + 0];
                    const g = image_data[pixel_index * 4 + 1];
                    const b = image_data[pixel_index * 4 + 2];
                    const pixel_brightness = (r + g + b) / (255 * 3);
                    pixel_brightnesses.push(pixel_brightness);
                }
                const total_pixel_brightness = pixel_brightnesses.reduce((a, b) => a + b, 0);
                const average_pixel_brightness = total_pixel_brightness / pixel_brightnesses.length;
                average_frame_brightnesses.push(average_pixel_brightness);
                const frame_end = Date.now();
                frame_durations.push(frame_end - frame_start);
            }
            console.log('Average frame brightnesses over time (bottom-left 1% of screen):', average_frame_brightnesses.map(x => Math.round(100 * x)));
            const average_frame_durations = frame_durations.reduce((a, b) => a + b, 0) / frame_durations.length;
            console.log('Average milliseconds between capture frames:', Math.round(average_frame_durations));
            await this.sleep(1000);
        }
    }
}
