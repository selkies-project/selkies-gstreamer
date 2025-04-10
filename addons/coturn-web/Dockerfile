# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#   Copyright 2019 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

FROM golang:alpine AS build
WORKDIR /go/src/coturn-web
COPY *.go ./
RUN go mod init github.com/selkies-project/selkies-gstreamer/coturn-web && go get -u ./... && go mod tidy && go build -a -mod=mod

FROM alpine

# Install tools
RUN apk add -u bash jq bind-tools curl

# Copy build from previous layer
COPY --from=build /go/src/coturn-web/coturn-web /usr/local/bin/coturn-web

COPY entrypoint.sh /etc/
RUN chmod -f +x /etc/entrypoint.sh

ENTRYPOINT ["/etc/entrypoint.sh"]
