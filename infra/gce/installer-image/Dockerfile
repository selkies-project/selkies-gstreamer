# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

FROM hashicorp/terraform:1.0.7 AS terraform

FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine

COPY --from=terraform /bin/terraform /bin/

COPY deploy.sh /

WORKDIR /workspace

ENTRYPOINT ["/deploy.sh"]