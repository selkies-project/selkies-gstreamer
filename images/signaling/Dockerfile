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

FROM python:3.7 as build

ARG GIT_TAG=e1de93cf40677220a516e85969b8c7626cb66988

RUN \
    git clone https://gitlab.freedesktop.org/gstreamer/gst-examples.git && \
    cd gst-examples/webrtc/signalling && \
    git checkout ${GIT_TAG} && \
    cp -R * /opt/

FROM python:3-alpine

# Add Tini
RUN apk add --no-cache tini

WORKDIR /opt/

COPY --from=build /opt/simple_server.py ./

RUN pip3 install websockets

ENV PORT=8081

CMD /sbin/tini -- python3 -u simple_server.py --addr 0.0.0.0 --port ${PORT} --disable-ssl
