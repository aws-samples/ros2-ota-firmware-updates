#!/bin/bash

export AWS_PAGER=""
# Set the desired AWS region (e.g., us-east-1, us-west-2, etc.)
REGION="us-east-1"

# Get the AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

# Get the Greengrass service role ARN
GREENGRASS_SERVICE_ROLE_ARN=$(aws iam list-roles --query "Roles[?AssumeRolePolicyDocument.Statement[?Principal.Service=='greengrass.amazonaws.com']].Arn" --region "$REGION" --output text)

if [ -n "$GREENGRASS_SERVICE_ROLE_ARN" ]; then
    echo "The AWS IoT Greengrass service role '$GREENGRASS_SERVICE_ROLE_ARN' exists in the '$REGION' region."

    # Extract the role name from the ARN
    ROLE_NAME=$(echo "$GREENGRASS_SERVICE_ROLE_ARN" | awk -F'/' '{print $NF}')

    # Check if the trust policy allows the Greengrass service to assume the role from the specified account and region
    TRUST_POLICY=$(aws iam get-role --role-name "$ROLE_NAME" --query "Role.AssumeRolePolicyDocument" --region "$REGION" --output text 2>/dev/null)
    if echo "$TRUST_POLICY" | grep -q "$ACCOUNT_ID"; then
        echo "The trust policy for the '$ROLE_NAME' role allows the Greengrass service to assume the role from the '$REGION' region and account '$ACCOUNT_ID'."
    else
        echo "The trust policy for the '$ROLE_NAME' role does not allow the Greengrass service to assume the role from the '$REGION' region and account '$ACCOUNT_ID'."
    fi
else
    echo "No AWS IoT Greengrass service role found in the '$REGION' region. Creating a new role..."

    # Create the Greengrass service role
    ROLE_NAME="AWSGreengrassServiceRole"
    TRUST_POLICY=$(cat << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "greengrass.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$ACCOUNT_ID"
        }
      }
    }
  ]
}
EOF
)
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_POLICY" --region "$REGION"
    echo "Created the AWS IoT Greengrass service role '$ROLE_NAME'."

    # Attach required policies to the Greengrass service role
    REQUIRED_POLICIES=(
        "arn:aws:iam::aws:policy/service-role/AWSGreengrassResourceAccessRolePolicy"
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    )

    for policy in "${REQUIRED_POLICIES[@]}"; do
        aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "$policy" --region "$REGION"
        echo "Attached policy '$policy' to the '$ROLE_NAME' role."
    done

    ROLE_ARN=$(aws iam get-role --role-name AWSGreengrassServiceRole --query Role.Arn --output text)
    echo "Associating the role with ARN '$ROLE_NAME' with GreenGrassV2 in the '$REGION' region..."
    aws greengrassv2 associate-service-role-to-account --role-arn $ROLE_ARN --region "$REGION" 

    echo "The AWS IoT Greengrass service role '$ROLE_NAME' is now configured for the '$REGION' region and account '$ACCOUNT_ID'."
fi