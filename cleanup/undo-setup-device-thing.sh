#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

export AWS_PAGER=""

NUM_DEVICES=2
DEVICE_TYPES=("firmware" "agent")

IOT_POLICY_NAME="device-thing-policy"

for device_num in $(seq 1 $NUM_DEVICES)
do
    for device_type in ${DEVICE_TYPES[@]}
    do
        THING_NAME="device-thing-${device_num}-${device_type}"
        echo "Processing Thing $THING_NAME"

        # Check if the Thing exists
        THING_EXISTS=$(aws iot list-things --query "things[?thingName=='$THING_NAME']" --output text)
        if [ -z "$THING_EXISTS" ]; then
            echo "Thing $THING_NAME does not exist, skipping"
            continue
        fi

        # Detach the policy from the certificate
        CERT_ARN=$(aws iot list-thing-principals --thing-name $THING_NAME --query "principals[0]" --output text || echo "")
        if [ -n "$CERT_ARN" ]; then
            ATTACHED_POLICIES=$(aws iot list-attached-policies --target $CERT_ARN --output text --query 'policies[].policyName')
            if echo "$ATTACHED_POLICIES" | grep -q "$IOT_POLICY_NAME"; then            
                echo "Detaching policy $IOT_POLICY_NAME from $CERT_ARN"
                aws iot detach-policy --policy-name $IOT_POLICY_NAME --target $CERT_ARN
            fi
        else
            echo "No certificate found for Thing $THING_NAME"
        fi

        # Detach the certificate from the Thing
        if [ -n "$CERT_ARN" ]; then
            echo "Detaching certificate $CERT_ARN from Thing $THING_NAME"
            aws iot detach-thing-principal --thing-name $THING_NAME --principal $CERT_ARN || true
        fi

        # Extract the certificate ID from the ARN
        CERT_ID=$(echo $CERT_ARN | awk -F'/' '{print $NF}' || echo "")

        # Detach all policies from the certificate
        if [ -n "$CERT_ID" ]; then
            ATTACHED_POLICIES=$(aws iot list-attached-policies --target $CERT_ARN --output text --query 'policies[*].policyName')
            for policy in $ATTACHED_POLICIES; do
                echo "Detaching policy $policy from certificate $CERT_ID"
                aws iot detach-policy --policy-name $policy --target $CERT_ARN || true
            done
        fi

        # Sleep enough time so policies get detached
        sleep 2

        # Delete the certificates
        if [ -n "$CERT_ID" ]; then
            echo "Deleting certificate $CERT_ID"
            aws iot update-certificate --certificate-id $CERT_ID --new-status INACTIVE || true
            aws iot delete-certificate --certificate-id $CERT_ID || true
        fi

        # Delete the Thing
        echo "Deleting Thing $THING_NAME"
        aws iot delete-thing --thing-name $THING_NAME || true

        # Remove the certificates directory
        rm -rf ../containers/certs/$THING_NAME
    done
done

# Detach the policy from any remaining principals
echo "Detaching policy $IOT_POLICY_NAME from any remaining principals"
PRINCIPALS=$(aws iot list-policy-principals --policy-name $IOT_POLICY_NAME --query "principals[*]" --output text || echo "")
for principal in $PRINCIPALS; do
    echo "Detaching policy $IOT_POLICY_NAME from principal $principal"
    aws iot detach-policy --policy-name $IOT_POLICY_NAME --target $principal || true
done

# Check if the policy exists before attempting to delete versions
if aws iot list-policies --query "policies[?policyName=='$IOT_POLICY_NAME']" --output text | grep -q $IOT_POLICY_NAME; then
    # Delete non-default versions of the policy
    echo "Deleting non-default versions of policy $IOT_POLICY_NAME"
    POLICY_VERSIONS=$(aws iot list-policy-versions --policy-name $IOT_POLICY_NAME --query "policyVersions[?isDefaultVersion==\`false\`].versionId" --output text)
    for version in $POLICY_VERSIONS; do
        echo "Deleting policy version $version"
        aws iot delete-policy-version --policy-name $IOT_POLICY_NAME --policy-version-id $version || true
    done

    # Delete the policy
    echo "Deleting IoT policy $IOT_POLICY_NAME"
    aws iot delete-policy --policy-name $IOT_POLICY_NAME || true
else
    echo "Policy $IOT_POLICY_NAME does not exist, skipping policy deletion"
fi