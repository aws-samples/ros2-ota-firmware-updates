# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from pydantic import BaseModel, PositiveInt
from pprint import pprint
import json

iot_data_client = boto3.client("iot-data")
iot_client = boto3.client("iot")


class JobExecution(BaseModel):
    eventType: str
    eventId: str
    timestamp: PositiveInt
    operation: str
    jobId: str
    thingArn: str
    status: str


def get_job_version(jobId):
    # Use describe_job_execution to get the job document
    response = iot_client.get_job_document(jobId=jobId)
    # Pretty print response
    operation = json.loads(response["document"]).get("operation")
    if operation != "Deploy-ROS-Firmware":
        print(f"Operation: {operation} not recognized")
        return None
    version = json.loads(response["document"]).get("version")
    print(f"Firmware version: {version}")
    return version


def update_thing_shadow(thingName, version):
    payload = json.dumps({"state": {"reported": {"firmwareVersion": version}}})
    shadowName = "firmware"
    response = iot_data_client.update_thing_shadow(
        thingName=thingName, shadowName=shadowName, payload=payload
    )
    print(f"Updated shadow {shadowName} to firmware version {version}")
    return response


def update_thing_attribute(thingName, version):
    attributePayload = {"attributes": {"firmwareVersion": version}}

    response = iot_client.update_thing(
        thingName=thingName,
        attributePayload=attributePayload,
    )
    print(response)


def handler(event, context):
    print(event)
    print(context)
    parsedEvent = JobExecution(**event)
    print(parsedEvent)
    print(f"JobId: {parsedEvent.jobId}")
    print(f"Status: {parsedEvent.status}")
    print(f"ThingArn: {parsedEvent.thingArn}")
    version = get_job_version(parsedEvent.jobId)
    if version:
        thingName = parsedEvent.thingArn.split("/")[-1]
        update_thing_shadow(thingName, version)
        update_thing_attribute(thingName, version)
