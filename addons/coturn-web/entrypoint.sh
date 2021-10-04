#!/bin/bash

set -e
set -x

# Save basic auth htpasswd to file.
cat - > "${TURN_HTPASSWD_FILE:-"/etc/htpasswd"}" <<EOF
$(echo $HTPASSWD_DATA64 | base64 -d)
EOF

if [[ "${CLOUD_RUN:-false}" == true ]]; then
    export PROJECT_ID=$(curl "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
    export REGION=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/region" -H "Metadata-Flavor: Google" | sed "s/.*\///")
    export TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" -H "Metadata-Flavor: Google" | jq -r '.access_token')

    export TURN_REALM=$(curl -s "https://${REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${PROJECT_ID}/services/${K_SERVICE}" -H "Authorization: Bearer ${TOKEN}" | jq -r '.status.url')

    [[ -z "${TURN_REALM}" ]] && echo "WARN: Could not determine TURN_REALM from cloud run public URL."
fi

/usr/local/bin/coturn-web