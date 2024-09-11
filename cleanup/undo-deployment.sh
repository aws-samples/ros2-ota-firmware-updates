#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -eu

export AWS_PAGER=""

# Get the core device ARN from the deployment-template.json file
CORE_DEVICE_ARN=$(jq -r '.targetArn' ../containers/greengrass/deployment.json)

if [ -n "$CORE_DEVICE_ARN" ]; then
    # Get all deployment IDs for the core device ARN
    DEPLOYMENT_IDS=$(aws greengrassv2 list-deployments --target-arn "$CORE_DEVICE_ARN" --query "deployments[].deploymentId" --output text)

    if [ -n "$DEPLOYMENT_IDS" ]; then
        echo "Canceling and deleting deployments for core device $CORE_DEVICE_ARN..."

        # Cancel and delete each deployment
        for DEPLOYMENT_ID in $DEPLOYMENT_IDS; do
            echo "Canceling deployment $DEPLOYMENT_ID..."
            aws greengrassv2 cancel-deployment --deployment-id "$DEPLOYMENT_ID"

            echo "Deleting deployment $DEPLOYMENT_ID..."
            aws greengrassv2 delete-deployment --deployment-id "$DEPLOYMENT_ID"

        done
    else
        echo "No deployments found for core device $CORE_DEVICE_ARN."
    fi
else
    echo "No core device ARN found in deployment-template.json."
fi