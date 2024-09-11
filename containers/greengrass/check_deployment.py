# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import json


def check_deployment(deployment_name, client):
    try:
        # List all deployments
        response = client.list_deployments()
        deployments = response["deployments"]

        # Filter deployments by name
        for deployment in deployments:
            deployment_id = deployment["deploymentId"]
            deployment_details = client.get_deployment(deploymentId=deployment_id)
            if deployment_details.get("deploymentName") == deployment_name:
                return True

        return None
    except client.exceptions.BadRequestException:
        print(f"No deployment '{deployment_name}' found.")
        return False
    except Exception as e:
        print(f"Error checking deployment: {e}")
        return False


def get_account_info(client):
    try:
        response = client.get_service_role_for_account()
        return response["roleArn"].split(":")[4]  # Extract the account ID from the RoleArn
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None


def create_deployment(deployment_template_file, region, account_id):
    client = boto3.client("greengrassv2", region_name=region)

    try:
        with open(deployment_template_file, "r") as f:
            deployment_template = json.load(f)

        # Replace placeholders with actual values
        target_arn = (
            deployment_template["targetArn"]
            .replace("<REGION>", region)
            .replace("<ACCOUNT>", account_id)
        )
        print("Target ARN for deployment", target_arn)
        deployment_template["targetArn"] = target_arn

        # Extract components and policies
        components = deployment_template.get("components", {})
        deployment_policies = deployment_template.get("deploymentPolicies", {})

        # Create the deployment
        response = client.create_deployment(
            targetArn=target_arn,
            deploymentName=deployment_template["deploymentName"],
            components=components,
            deploymentPolicies=deployment_policies,
        )

        return response

    except Exception as e:
        print(f"Error creating deployment: {e}")
        return None


if __name__ == "__main__":
    specific_deployment_name = "Deployment for RosProvisioningGreengrassCore"
    region = "us-east-1"  # hardcoded for now
    deployment_template_file = "./deployment-template.json"

    client = boto3.client("greengrassv2", region_name=region)

    account_id = get_account_info(client)
    if not account_id:
        print(
            "Failed to retrieve account information. So unable to check deployment. Check IoT Policy."
        )
    else:
        deployment = check_deployment(specific_deployment_name, client)

        if deployment:
            # print(f"Found deployment: {specific_deployment_name}")
            print(deployment)
        else:
            print(
                f"Deployment with name '{specific_deployment_name}' not found. Creating deployment..."
            )
            response = create_deployment(deployment_template_file, region, account_id)
            if response:
                print(f"Deployment created successfully: {response['deploymentId']}")
            else:
                print("Failed to create deployment.")
