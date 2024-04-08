# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

FROM python:3-alpine

RUN pip3 install flask

COPY app.py /

WORKDIR /

# Replace environment with customized TURN server
ENV TURN_SHARED_SECRET openrelayprojectsecret
ENV TURN_HOST staticauth.openrelay.metered.ca
ENV TURN_PORT 443
ENV TURN_TLS true
ENV TURN_PROTOCOL tcp

EXPOSE 8008

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=8008"]
