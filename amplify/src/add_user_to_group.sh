#!/bin/bash

# Ensure the script exits on error
set -e

# Hardcoded group name
GROUP_NAME="ROS-OTA-AuthorizedUsers"

# Function to display usage
usage() {
    echo "Usage: $0 -u <username> -p <user_pool_id>"
    exit 1
}

# Parse arguments
while getopts ":u:p:" opt; do
    case ${opt} in
        u) USERNAME=$OPTARG ;;
        p) USER_POOL_ID=$OPTARG ;;
        *) usage ;;
    esac
done

# Check if username and user_pool_id are provided
if [[ -z "$USERNAME" || -z "$USER_POOL_ID" ]]; then
    usage
fi

# Add the user to the group
echo "Adding user '$USERNAME' to group '$GROUP_NAME' in user pool '$USER_POOL_ID'..."
aws cognito-idp admin-add-user-to-group \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --group-name "$GROUP_NAME"

if [[ $? -eq 0 ]]; then
    echo "User '$USERNAME' successfully added to group '$GROUP_NAME'."
else
    echo "Failed to add user '$USERNAME' to group '$GROUP_NAME'."
fi