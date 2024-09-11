#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -eu

export AWS_PAGER=""
NUM_DEVICES=2
DEVICE_TYPES=("firmware" "agent")

ENTRIES=""

for device_num in $(seq 1 $NUM_DEVICES)
do
    for device_type in ${DEVICE_TYPES[@]}
    do
    THING_NAME="device-thing-${device_num}-${device_type}"
    ENTRIES="$ENTRIES thingName=$THING_NAME"
    done
done

aws greengrassv2 batch-disassociate-client-device-from-core-device \
    --core-device-thing-name RosProvisioningGreengrassCore \
    --entries $ENTRIES