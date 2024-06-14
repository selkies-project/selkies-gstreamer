# Troubleshooting and FAQs

## The HTML5 web interface loads and the signaling connection works, but the WebRTC connection fails or the remote desktop does not start.

First of all, use HTTPS or HTTP port forwarding to localhost as much as possible. Browsers do not support WebRTC or relevant features including pointer and keyboard lock in HTTP outside localhost. Also check if the WebRTC video codec is supported in the web browser, as the server may panic if the codecs do not match. Moreover, ensure that there is a running PulseAudio or PipeWire-Pulse session as the interface does not establish without an audio server.

Then, please read [Using a TURN server](firewall.md).

Make sure to also check that you enabled automatic login with your display manager, as the remote desktop cannot access the initial login screen after boot without login. If you created the TURN server or the example container inside a VPN-enabled environment or virtual machine and the WebRTC connection fails, then you may need to add the `SELKIES_TURN_HOST` environment variable to the private VPN IP of the TURN server host, such as `192.168.0.2`.

## The HTML5 web interface is slow and laggy.

**Usually, the issue arises from using a Wi-Fi router with bufferbloat issues, especially if you observe stuttering. Try using the [Bufferbloat Test](https://www.waveform.com/tools/bufferbloat) to identify the issue first before moving on.**

First of all, there is an issue with CPU congestion from the web interface when the side panel is open. Please make sure to test your experience when the side panel is closed.

If this is the case, first try enabling `--congestion_control`, meant to mitigate such issues in coordination with the web browser. Moreover, always make sure that there are minimal background network processes, as live interactive streaming much is less tolerant to network fluctuation compared with other forms of video that can load the stream in advance. Using wired ethernet or a good 5GHz Wi-Fi connection is important (wired ethernet will eliminate all remaining issues of a good but slightly stuttering Wi-Fi connection). Ensure that the latency to your TURN server from the server and the client is ideally under 50 ms. If the latency is too high, your connection may be too laggy for any interactive 3D application. Also note that a higher framerate will improve performance if you have sufficient bandwidth. This is because one screen refresh from a 60 fps screen takes 16.67 ms at a time, while one screen refresh from a 15 fps screen inevitably takes 66.67 ms, and therefore inherently causes a visible lag. Also try to keep the total bitrate reasonable, keeping around your service level agreement (SLA) bandwidth (which might be different from your maximum bandwidth contract).

If the latency becomes higher while the screen is idle or when the tab is not focused, the internal efficiency control mechanism of the web browser may activate, which will be resolved automatically after a few seconds if there is new activity. If it does not, disable all power saving or efficiency features available in the web browser. In Windows 10 or 11, try `Start > Settings > System > Power & battery > Power mode > Best performance`. Also, note that if you saturate your CPU or GPU with an application on the host, the remote desktop interface will also substantially slow down as it cannot use the CPU or GPU enough to decode the screen.

However, it might be that the parameters for the WebRTC interface, video encoders, the RTSP payloader, or other [GStreamer](https://gstreamer.freedesktop.org) plugins are not optimized enough. If you find that it is the case, we always welcome contributions. If your changes show noticeably better results in the same conditions, please make a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls), or tell us about the parameters in any channel that we can reach so that we could also test.

## The web interface refuses to start up in the terminal after rebooting my computer or restarting my desktop in a standalone instance.

This is because the desktop session starts as `root` when the user is not logged in. Next time, set up automatic login in the settings with the user you want to use. In order to use the web interface when this is not possible (or when you are using SSH or remote access), check `sudo systemctl status sddm`, `sudo systemctl status lightdm`, or `sudo systemctl status gdm3` (use your display session manager) and find the path next to the `-auth` argument. Set the environment variable `XAUTHORITY` to the path you found while running Selkies-GStreamer as `root`.

## My touchpad does not move while pressing a key with the keyboard.

This is a setting from the client operating system and will show the same behavior with any other application. In Windows, go to `Settings > Bluetooth & devices > Touchpad > Taps` to increase your touchpad sensitivity. In Linux or Mac, turn off the setting `Touchpad > Disable while typing`.

## I want to pass multiple screens within a server to another client using the WebRTC HTML5 web interface.

You can start a new instance of Selkies-GStreamer by changing the `DISPLAY` environment variable and setting a different web interface port in a different terminal to pass a different screen simultaneously to your current screen. Reverse proxies supporting WebSocket such as `nginx` can be utilized to expose the interfaces to multiple users in different paths.

## I want to test a shared secret TURN server by manually generating a TURN credential from a shared secret.

Try the [turn-rest](/addons/turn-rest) Flask web application. This will output TURN credentials automatically.

The below steps can be used when you want to test your TURN server configured with a shared secret instead of the legacy username/password authentication.

1. Run the test container:

```bash
docker-compose run --service-ports test
```

2. From inside the test container, call the `generate_rtc_config` method.

```bash
export SELKIES_TURN_HOST="Your TURN Host"
export SELKIES_TURN_PORT="Your TURN Port"
export SELKIES_TURN_SECRET="Your Shared Secret"
export SELKIES_TURN_USER="user"

python3 -c 'import os;from selkies_gstreamer.signaling_web import generate_rtc_config; print(generate_rtc_config(os.environ["SELKIES_TURN_HOST"], os.environ["SELKIES_TURN_PORT"], os.environ["SELKIES_TURN_SECRET"], os.environ["SELKIES_TURN_USER"]))'
```

> You can then test your TURN server configuration from the [Trickle ICE](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/) webpage.
