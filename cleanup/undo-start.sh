#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -eu

PROJECT_NAME="ros-ota"

# Check if the user has permission to access the Docker daemon socket
if ! docker info >/dev/null 2>&1; then
    SUDO_PREFIX="sudo"
else
    SUDO_PREFIX=""
fi

# Stop and remove Docker Compose services
$SUDO_PREFIX docker compose --project-name $PROJECT_NAME down

# Remove Docker images
$SUDO_PREFIX docker image rm $($SUDO_PREFIX docker image ls --format "{{.Repository}}:{{.Tag}}" | grep "$PROJECT_NAME")

# Remove the certs directory if it exists
FIRMWARE_CERT_MOUNT_PATH=$(pwd)/certs
if [ -d "$FIRMWARE_CERT_MOUNT_PATH" ]; then
    echo "Removing $FIRMWARE_CERT_MOUNT_PATH directory"
    rm -rf "$FIRMWARE_CERT_MOUNT_PATH"
fi

echo "Removing volume"
$SUDO_PREFIX docker volume rm ros-ota_greengrass-data