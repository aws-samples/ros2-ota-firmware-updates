#!/bin/sh
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

set +m
echo "Starting Docker..."
dockerd > /dev/null 2>&1 &

echo "Starting Agent..."
. /venv/bin/activate && python -u /agent/agent.py
