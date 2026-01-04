# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import argparse
import json
import uuid


def create_deployment_job(version, thing_name, job_id, account_id, region):
    print(f"Creating iot job to deploy version {version}")
    if not job_id:
        # create a unique job id
        job_id = uuid.uuid4()
    if not account_id:
        # get the account id
        account_id = boto3.client("sts", region_name=region).get_caller_identity().get("Account")
    print("job_id", job_id)
    print("account_id", account_id)
    print("thing_name", thing_name)
    print("region", region)
    client = boto3.client("iot", region_name=region)
    target = f"arn:aws:iot:{region}:{account_id}:thing/{thing_name}"
    job_document = f'''{{
        "operation": "Deploy-ROS-Firmware",
        "jobDocument": {{
            "thingName": "{thing_name}",
            "attributeUpdate": {{
                "attributes": {{
                    "firmwareVersion": "{version}"
                }}
            }}
        }},
        "version": "{version}"
    }}'''
    response = client.create_job(
        jobId=str(job_id),
        targets=[target],
        description=f"Deployment to version {version}",
        targetSelection="SNAPSHOT",
        document=job_document,
    )
    print(response)
    return response

def update_thing_attributes(thing_name, version, region):
    client = boto3.client("iot", region_name=region)
    # Get current version
    current_version = (client.describe_thing(thingName=thing_name)).get('version')
    print(f"Current version of {thing_name} is: {current_version}")
    try: 
        response = client.update_thing(
            thingName=thing_name,
            attributePayload={
                'attributes': {
                    'firmwareVersion': version,
                    'OTA_Support': 'True'
                },
                'merge': True  # Merge with existing attributes
            },
            expectedVersion=current_version
        )
        print(f"Updated firmwareVersion attribute for {thing_name}: {response}")
    except client.exceptions.VersionConflictException as e:
        print(f"Version conflict: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an iot job")
    parser.add_argument("version", help="version to deploy")
    parser.add_argument("--thing_name", help="thing name", default="device-thing-1-agent")
    parser.add_argument("--job_id", help="job id")
    parser.add_argument("--account_id", help="AWS account id")
    parser.add_argument("--region", help="AWS region", default="us-east-1")
    args = parser.parse_args()
    version = args.version
    job_id = args.job_id
    account_id = args.account_id
    thing_name = args.thing_name
    region = args.region
    response = create_deployment_job(version, thing_name, job_id, account_id, region)

    # Check if the job creation was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Job creation successful, proceeding to update thing attributes.")
        # Update thing attribute directly
        update_thing_attributes(thing_name, version, region)
    else:
        print("Job creation failed, skipping attribute update.")
