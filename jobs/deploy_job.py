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
    job_document = {"operation": "Deploy-ROS-Firmware", "version": version}
    response = client.create_job(
        jobId=str(job_id),
        targets=[target],
        description=f"Deployment to version {version}",
        targetSelection="SNAPSHOT",
        document=json.dumps(job_document),
    )
    print(response)


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
    create_deployment_job(version, thing_name, job_id, account_id, region)
