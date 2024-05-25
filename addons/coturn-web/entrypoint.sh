#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

set -e

if [ -n "${HTPASSWD_DATA64}" ]; then
    # Save basic authentication htpasswd to file.
    export TURN_HTPASSWD_FILE="${TURN_HTPASSWD_FILE:-"/etc/htpasswd"}"
    cat - > ${TURN_HTPASSWD_FILE} <<EOF
$(echo $HTPASSWD_DATA64 | base64 -d)
EOF
fi

/usr/local/bin/coturn-web
