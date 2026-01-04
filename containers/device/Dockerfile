# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM docker:24-dind

COPY docker-daemon.json /etc/docker/daemon.json

RUN mkdir -p /certs /agent

RUN apk add py3-virtualenv

RUN python -m virtualenv /venv && . /venv/bin/activate && pip3 install docker awsiotsdk

COPY agent /agent
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
