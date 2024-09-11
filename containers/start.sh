#!/bin/sh

set -eu

# Check if the user has permission to access the Docker daemon socket
if ! docker info >/dev/null 2>&1; then
    SUDO_PREFIX="sudo"
else
    SUDO_PREFIX=""
fi

export FIRMWARE_CERT_MOUNT_PATH=$(pwd)/certs
PROJECT_NAME="ros-ota"
$SUDO_PREFIX docker compose --project-name $PROJECT_NAME up --build
