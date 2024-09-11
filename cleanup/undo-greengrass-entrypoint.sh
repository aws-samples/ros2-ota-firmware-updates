#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

# Get the AWS Region from the environment variable
AWS_REGION=$(echo "$AWS_REGION" | tr '[:upper:]' '[:lower:]')

# Get the Greengrass Core Thing Name
THING_NAME="RosProvisioningGreengrassCore"

# Retrieve the Greengrass Core Thing ARN
THING_ARN=$(aws iot describe-thing --thing-name "$THING_NAME" --query "thingArn" --output text || echo "")

if [ -z "$THING_ARN" ]; then
    echo "Greengrass Core Thing '$THING_NAME' not found. Skipping cleanup."
    exit 0
fi

# Get the Thing Group Name & Arn
THING_GROUP_NAME=$(aws iot list-thing-groups --query "thingGroups[?groupName=='RosProvisioningGreengrassCoreGroup'].groupName" --output text)
THING_GROUP_ARN=$(aws iot list-thing-groups --query "thingGroups[?groupName=='RosProvisioningGreengrassCoreGroup'].groupArn" --output text)

# Get the policy name
POLICY_NAME=$(aws iot list-policies --query "policies[?policyName=='GreengrassV2IoTThingPolicy'].policyName" --output text)

# Get the certificate ARN
CERT_ARN=$(aws iot list-thing-principals --thing-name "$THING_NAME" --query "principals[0]" --output text)

# Extract the certificate ID from the ARN
CERT_ID=$(echo "$CERT_ARN" | awk -F'/' '{print $NF}')

# Get the TES role alias name
TES_ROLE_ALIAS_NAME=$(aws iot list-role-aliases --query "roleAliases[*]" --output text | grep "GreengrassCoreTokenExchangeRoleAlias")

# Get the TES certificate policy name
TES_CERT_POLICY_NAME=$(aws iot list-policies --query "policies[?policyName=='GreengrassTESCertificatePolicyGreengrassCoreTokenExchangeRoleAlias'].policyName" --output text)

# Detach the policy from the certificate
if [ -n "$CERT_ARN" ] && [ -n "$POLICY_NAME" ] && [ "$CERT_ARN" != "None" ]; then
    echo "Detaching policy '$POLICY_NAME' from certificate '$CERT_ARN'"
    aws iot detach-policy --policy-name "$POLICY_NAME" --target "$CERT_ARN"
fi

# Detach all policies from the certificate
if [ -n "$CERT_ARN" ] && [ "$CERT_ARN" != "None" ]; then
    ATTACHED_POLICIES=$(aws iot list-attached-policies --target "$CERT_ARN" --query "policies[*].policyName" --output text)
    for policy in $ATTACHED_POLICIES; do
        echo "Detaching policy '$policy' from certificate '$CERT_ARN'"
        aws iot detach-policy --policy-name "$policy" --target "$CERT_ARN"
    done
fi

# Detach the certificate from the Greengrass Core Thing
if [ -n "$CERT_ARN" ] && [ -n "$THING_NAME" ] && [ "$CERT_ARN" != "None" ]; then
    echo "Detaching certificate '$CERT_ARN' from Greengrass Core Thing '$THING_NAME'"
    aws iot detach-thing-principal --thing-name "$THING_NAME" --principal "$CERT_ARN"
fi

# Delete the certificate
if [ -n "$CERT_ID" ] && [ "$CERT_ARN" != "None" ]; then
    echo "Deleting certificate '$CERT_ID'"
    aws iot update-certificate --certificate-id "$CERT_ID" --new-status INACTIVE
    aws iot delete-certificate --certificate-id "$CERT_ID"
fi

# Remove the Greengrass Core Thing from the Thing Group
if [ -n "$THING_NAME" ] && [ -n "$THING_GROUP_NAME" ]; then
    echo "Removing Greengrass Core Thing '$THING_NAME' from Thing Group '$THING_GROUP_NAME'"
    aws iot remove-thing-from-thing-group --thing-name "$THING_NAME" --thing-group-name "$THING_GROUP_NAME"
fi

# Delete the Greengrass Core Thing
if [ -n "$THING_NAME" ]; then
    echo "Deleting Greengrass Core Thing '$THING_NAME'"
    aws iot delete-thing --thing-name "$THING_NAME"
fi

# Delete the core device
echo "Deleting Greengrass Core Device"
aws greengrassv2 delete-core-device --core-device-thing-name "$THING_NAME"

# Delete the policy
if [ -n "$POLICY_NAME" ]; then
    echo "Deleting policy '$POLICY_NAME'"
    aws iot delete-policy --policy-name "$POLICY_NAME"
fi

# Detach and delete the TES certificate policy
if [ -n "$TES_CERT_POLICY_NAME" ]; then
    TES_CERT_POLICY_ARN=$(aws iot list-policy-principals --policy-name "$TES_CERT_POLICY_NAME" --query "principals[*]" --output text)
    for principal in $TES_CERT_POLICY_ARN; do
        echo "Detaching TES certificate policy '$TES_CERT_POLICY_NAME' from principal '$principal'"
        aws iot detach-policy --policy-name "$TES_CERT_POLICY_NAME" --target "$principal"
    done
    echo "Deleting TES certificate policy '$TES_CERT_POLICY_NAME'"
    aws iot delete-policy --policy-name "$TES_CERT_POLICY_NAME"
fi

# Delete the TES role alias
if [ -n "$TES_ROLE_ALIAS_NAME" ]; then
    echo "Deleting TES role alias '$TES_ROLE_ALIAS_NAME'"
    aws iot delete-role-alias --role-alias "$TES_ROLE_ALIAS_NAME"
fi

# Delete the Thing Group
if [ -n "$THING_GROUP_NAME" ] && [ -n "$THING_GROUP_ARN" ]; then
    echo "Deleting Thing Group '$THING_GROUP_NAME' ($THING_GROUP_ARN)"
    aws iot delete-thing-group --thing-group-name "$THING_GROUP_NAME"
fi

echo "Cleanup completed."