#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

set +m
echo "Starting Firmware..."

echo "TOPIC $TOPIC"
echo "THING_NAME $THING_NAME"
echo "VERSION $VERSION"
echo "HEALTH $HEALTH"
echo "TIMER PERIOD $TIMER_PERIOD"

source /opt/ros/humble/setup.bash
source /ros_ws/install/local_setup.bash
export IOT_CONFIG_FILE=/config/iot_config.json

ros2 run service service --ros-args --param path_for_config:=$IOT_CONFIG_FILE --param topic:=$TOPIC --param client_id:=$THING_NAME --param version:=\'$VERSION\' --param timer_period:=$TIMER_PERIOD --log-level debug