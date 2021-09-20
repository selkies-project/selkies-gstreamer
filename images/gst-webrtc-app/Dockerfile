# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:20.04

RUN \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        build-essential \
        python3-pip \
        python3-dev \
        python3-gi \
        tzdata \
        sudo \
        udev \
        xclip \
        x11-utils \
        xdotool \
        wmctrl \
        jq \
        gdebi-core \
        x11-xserver-utils

RUN \
    pip3 install websockets xlib gputil python-uinput prometheus_client msgpack pynput psutil

# Install selkies-gstreamer GStreamer build
WORKDIR /opt/selkies-gstreamer
ADD selkies-gstreamer-latest.tgz .
RUN bash selkies-gstreamer-install.sh

# Install selkies-gstreamer python app
RUN python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps selkies-gstreamer-disla

# Add Tini
ARG TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-amd64 /tini
RUN chmod +x /tini

# Copy app
WORKDIR /opt/app
#COPY *.py debug.sh /opt/app/

ENV PYTHONPATH=/usr/local/lib/python3.8/dist-packages:/usr/lib/python3.8/site-packages
ENV PATH=/usr/local/nvidia/bin:${PATH}

# Test selkies-gstreamer
#RUN python3 /opt/app/gst-python-test.py && \
#    rm -f /root/.cache/gstreamer-1.0/registry.x86_64.bin

# Add entrypoint script
COPY entrypoint.sh record.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/tini", "--", "/entrypoint.sh"]