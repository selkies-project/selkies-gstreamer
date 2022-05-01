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

FROM nginx:alpine

# Install dependencies
RUN \
    apk add -u --no-cache imagemagick bash

WORKDIR /opt/gst-web
COPY . .
RUN INSTALL_DIR="/usr/share/nginx/html" ./install.sh

# Create release tarball
RUN cp -R /usr/share/nginx/html /tmp/gst-web && \
    cd /tmp && tar zcvf /opt/gst-web.tgz gst-web && \
    rm -rf /tmp/gst-web

ENV GST_WEB_PORT 80
ENV PATH_PREFIX /

COPY entrypoint.sh /entrypoint.sh
CMD /entrypoint.sh
