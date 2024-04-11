---
name: Bug report
about: Bugs that affect usage
title: ''
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error or issue

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

 - Host OS Version: [e.g. Ubuntu 24.04, Arch Linux ‎2024.01.01]
 - Host GPU Model and Driver/Encoder Version: [e.g. Intel UHD Graphics 750, libva 1.22.0 from `vainfo` / NVIDIA RTX 3070, 535.129.03 driver]
 - GStreamer Version: [e.g. 1.24.1]
 - Browser Version [e.g. Chrome 123, Safari 17.4]

**Additional context**
Add any other context about the problem here.

 - ALL BUGS: upload the output log from `selkies-gstreamer` regardless of whether the bug is caused by the web browser or the host. Read the error. If you are using `docker-*-desktop` container, upload all log files in `/tmp`.
 - If the issue relates to `ximagesrc` and therefore screen capture, upload the Xorg.*.log (such as `/var/log/Xorg.0.log` or `~/.local/share/xorg/Xorg.0.log`).
 - If the issue relates to `webrtcbin` or the web browser, upload contents of `chrome://webrtc-internals` and check in the browser console (F12) to see if there are any errors or warnings. In the browser console, check that the codec is supported in the web browser with `console.log(RTCRtpReceiver.getCapabilities('video').codecs)` after putting in `allow pasting`.
 - Check your TURN server configuration and see if it is valid and connectable. In case the ISP throttles a certain protocol, try turning on TURN over TCP or TURN over TLS.
 - If the issue relates to encoders or `videoconvert`/`cudaconvert`/`vapostproc`, explain your setup and driver installation as precisely as possible.
