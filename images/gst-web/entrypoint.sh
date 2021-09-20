#!/bin/bash

# Copyright 2021 The Selkies Authors
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

set -e

# Update PWA manifest.json with app info and route.
sed -i \
    -e "s|PWA_APP_NAME|${PWA_APP_NAME:-WebRTC}|g" \
    -e "s|PWA_APP_PATH|${PWA_APP_PATH:-webrtc-desktop}|g" \
  /usr/share/nginx/html/manifest.json
sed -i \
  -e "s|PWA_CACHE|${PWA_APP_PATH:-webrtc-desktop}-webrtc-pwa|g" \
  /usr/share/nginx/html/sw.js

if [[ -n "${PWA_ICON_URL}" ]]; then
  echo "INFO: Converting icon to PWA standard"
  if [[ "${PWA_ICON_URL}" =~ "data:image/png;base64" ]]; then
    echo "${PWA_ICON_URL}" | cut -d ',' -f2 | base64 -d > /tmp/icon.png
  else
    curl -s -L "${PWA_ICON_URL}" > /tmp/icon.png
  fi
  if [[ -e /tmp/icon.png ]]; then
    echo "INFO: Creating PWA icon sizes"
    convert /tmp/icon.png /usr/share/nginx/html/icon.png
    rm -f /tmp/icon.png
    echo "192x192 512x512" | tr ' ' '\n' | \
      xargs -P4 -I{} convert -resize {} -size {} /usr/share/nginx/html/icon.png /usr/share/nginx/html/icon-{}.png || true
  else
    echo "WARN: failed to download PWA icon, PWA features may not be available: ${PWA_ICON_URL}"
  fi
fi

sed -i \
    -e 's/listen.*80;/listen '${GST_WEB_PORT}';/g' \
    -e 's|location /|location '${PATH_PREFIX}'|g' \
    -e 's|root.*/usr/share/nginx/html.*|alias /usr/share/nginx/html/;|g' \
  /etc/nginx/conf.d/default.conf

echo "INFO: Starting web server"
exec nginx -g 'daemon off;'
