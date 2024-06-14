# WebRTC and Firewall Issues

WebRTC uses the UDP protocol to transport your desktop.

Whilst this is the reason Selkies-GStreamer enjoys better performance compared to other solutions, your network firewall may still prevent you from connecting to your instance.

**(IMPORTANT) Instructions here are mandatory if the HTML5 web interface loads and the signaling connection says it works, but the WebRTC connection fails and therefore the remote desktop does not start.**

## The Easy Fix

### Self-Hosted Instances

For standalone self-hosted instances, open UDP ports 49152–65535 in your network. A configuration in your network router called `Full Cone NAT` or `Restricted Cone NAT` (otherwise called peer-to-peer/P2P mode or gaming mode) is another alternative.

### Containers

For an easy fix to when the HTML5 web interface and the signaling connection works, but the WebRTC connection fails in a container, add the option `--network=host` to your Docker command, or add `hostNetwork: true` under your Kubernetes YAML configuration file's pod `spec:` entry, which should be indented in the same depth as `containers:` (note that your cluster may have not allowed this, resulting in an error).

This exposes your container to the host network, which disables network isolation. If this does not fix the connection issue (normally when the server is behind another firewall) or you cannot use this fix for security or technical reasons, read the below text.

## TURN Server

**A TURN server is required if trying to use this project inside a Docker or Kubernetes container without host networking, or in other cases where the HTML5 web interface loads but the connection to the server fails. This is required for all WebRTC applications, especially since Selkies-GStreamer is self-hosted, unlike other proprietary services which provide a TURN server for you.**

In most cases when either of your server or client does not have a restrictive firewall, the default Google STUN server configuration will work without additional configuration. However, when connecting from networks that cannot be traversed with STUN, a TURN server is required.

[Open Relay](https://www.metered.ca/tools/openrelay) is a free TURN server instance that may be used for personal testing purposes, but may not be optimal for production usage. Otherwise, [Cloudflare](https://developers.cloudflare.com/calls/turn/overview/) and [Twilio](https://www.twilio.com/docs/stun-turn) also provide TURN server services.

An open-source TURN server for Linux or UNIX-like operating systems that may be used is [coTURN](https://github.com/coturn/coturn), available in major package repositories or as an example container [`coturn/coturn:latest`](https://hub.docker.com/r/coturn/coturn). Alternatively, the Selkies-GStreamer [`coturn`](/addons/coturn) and [`coturn-web`](/addons/coturn-web) images [`ghcr.io/selkies-project/selkies-gstreamer/coturn`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn) and [`ghcr.io/selkies-project/selkies-gstreamer/coturn-web`](https://github.com/selkies-project/selkies-gstreamer/pkgs/container/selkies-gstreamer%2Fcoturn-web) are also included in this repository, and may be used to host your own STUN/TURN infrastructure.

For all other major operating systems including Windows, [Pion TURN](https://github.com/pion/turn)'s `turn-server-simple` executable or [eturnal](https://eturnal.net) are recommended alternative TURN server implementations. [STUNner](https://github.com/l7mp/stunner) is a Kubernetes native STUN and TURN deployment if Helm is possible to be used.

## Install and run coTURN on a standalone machine or cloud instance

It is possible to install [coTURN](https://github.com/coturn/coturn) on your own server or PC from a package repository, as long as the listing port and the relay ports may be opened. In short, `/etc/turnserver.conf` must have the lines `listening-ip=0.0.0.0` and `realm=example.com` (change the realm as appropriate), and either the lines `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)`, or the lines `lt-cred-mech` and `user=yourusername:yourpassword`. It is strongly recommended to set the `min-port=` and `max-port=` parameters which specifies your relay ports between TURN servers (all ports between this range must be open). Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

The `cert=` and `pkey=` options, which lead to the certificate and the private key from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), are required for using TURN over TLS/DTLS, but are otherwise optional.

### Deploy coTURN with Docker

In order to deploy a coTURN container, use the following command (consult this [example configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) for more options which may also be used as command-line arguments). You should be able to expose these ports to the internet. Modify the relay ports `-p 49160-49200:49160-49200/udp` and `--min-port=49160 --max-port=49200` as appropriate (at least one relay port is required). Simply using `--network=host` instead of specifying `-p 49160-49200:49160-49200/udp` is also fine if possible. The relay ports and the listening port must all be open to the internet. Add the `--no-udp-relay` behind `-n` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or `--no-tcp-relay` behind `-n` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

For time-limited shared secret TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --listening-ip=0.0.0.0 --realm=example.com --min-port=49160 --max-port=49200 --use-auth-secret --static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)
```

For legacy long-term TURN authentication:

```
docker run -d -p 3478:3478 -p 3478:3478/udp -p 49160-49200:49160-49200/udp coturn/coturn -n --listening-ip=0.0.0.0 --realm=example.com --min-port=49160 --max-port=49200 --lt-cred-mech --user=yourusername:yourpassword
```

If you want to use TURN over TLS/DTLS, you must have a valid hostname, and also provision a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS), and provide the certificate and private files to the coTURN container with `-v /mylocalpath/coturncert.pem:/etc/coturncert.pem -v /mylocalpath/coturnkey.pem:/etc/coturnkey.pem`, then add the command-line arguments `-n --cert=/etc/coturncert.pem --pkey=/etc/coturnkey.pem` (the specified paths are an example).

More information available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Deploy coTURN With Kubernetes

Before you read, [STUNner](https://github.com/l7mp/stunner) is a pretty good method to deploy a TURN or STUN server on Kubernetes if you are able to use Helm.

You are recommended to use a `ConfigMap` for creating the configuration file for coTURN. Use the [example coTURN configuration](https://github.com/coturn/coturn/blob/master/examples/etc/turnserver.conf) as a reference to create a `ConfigMap` which mounts to `/etc/turnserver.conf`. The only mandatory lines are the lines `listening-ip=0.0.0.0` and `realm=example.com` (change the realm as appropriate), and either `use-auth-secret` and `static-auth-secret=(PUT RANDOM 64 BYTE BASE64 KEY HERE)` or `lt-cred-mech` and `user=yourusername:yourpassword`, but specifying `min-port=` and `max-port=` are strongly recommended to restrict the range of the relay ports.

Use `Deployment` or `DaemonSet` and use `containerPort` and `hostPort` under `ports:` to open the listening port 3478 (or any other port you set in `/etc/turnserver.conf` with `listening-port=`).

Then you must also open all ports between `min-port=` and `max-port=` that you set in `/etc/turnserver.conf`, but this may be skipped if `hostNetwork: true` is used instead. The relay ports and the listening port must all be open to the internet. Add the line `no-udp-relay` if you cannot open the UDP `min-port=` to `max-port=` port ranges, or the line `no-tcp-relay` if you cannot open the TCP `min-port=` to `max-port=` port ranges.

Under `args:` set `-c /etc/turnserver.conf` and use the `coturn/coturn:latest` image.

If you want to use TURN over TLS/DTLS, use [cert-manager](https://cert-manager.io) to issue a valid certificate with the correct hostname from preferably ZeroSSL (Let's Encrypt may have issues based on the OS), then mount the certificate and private key in the container. Do not forget to include the options `cert=` and `pkey=` in `/etc/turnserver.conf` to the correct path of the certificate and the key.

More information is available in the [coTURN container image](https://hub.docker.com/r/coturn/coturn) or the [coTURN repository](https://github.com/coturn/coturn) website.

### Start Selkies-GStreamer with the TURN server credentials

Provide the TURN server host address (the environment variable `SELKIES_TURN_HOST` or the command-line option `--turn_host`), port (the environment variable `SELKIES_TURN_PORT` or the command-line option `--turn_port`), and the shared secret (`SELKIES_TURN_SHARED_SECRET`/`--turn_shared_secret`) or the legacy long-term authentication username/password (`SELKIES_TURN_USERNAME`/`--turn_username` and `SELKIES_TURN_PASSWORD`/`--turn_password`) in order to take advantage of the TURN relay capabilities and guarantee connection success.

You may set the environment variable `SELKIES_TURN_PROTOCOL` to `tcp` or set the command-line option `--turn_protocol=tcp` if you are unable to open the UDP listening port to the internet for the coTURN container, or if the UDP protocol is blocked or throttled in your client network.

You may also set `SELKIES_TURN_TLS` to `true` or set `--turn_tls=true` if TURN over TLS/DTLS was properly configured from the TURN server with a valid certificate issued from a legitimate certificate authority such as [ZeroSSL](https://zerossl.com/features/acme/) (Let's Encrypt may have issues depending on the OS).