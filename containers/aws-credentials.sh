#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Check if the $HOME/.aws/credentials file exists
if [ -f "$HOME/.aws/credentials" ]; then
    # Read the values from the credentials file
    AWS_ACCESS_KEY_ID=$(grep -oP 'aws_access_key_id\s*=\s*\K\w+' "$HOME/.aws/credentials")
    AWS_SECRET_ACCESS_KEY=$(grep -oP '^aws_secret_access_key\s*=\s*\K.*' "$HOME/.aws/credentials" | tr -d '\r')

    # Export the values as environment variables
    export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
    cat "$HOME/.aws/credentials" > ./credentials
    echo "Echoed the $HOME/.aws/credentials file into the env."
else
    echo "The $HOME/.aws/credentials file does not exist."
fi