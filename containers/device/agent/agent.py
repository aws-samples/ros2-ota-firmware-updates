# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from job_handler import JobHandler
from discover_gg_connection import get_mqtt_connection
import time
import os
import docker


registry = "registry:5000"
device_name = os.environ.get("DEVICE_NAME")
agent_thing_name = f"{device_name}-agent"
firmware_thing_name = f"{device_name}-firmware"
firmware_cert_mount_path = f"/certs/{firmware_thing_name}"
network = "host"

key = f"/certs/{agent_thing_name}/private.pem.key"
cert = f"/certs/{agent_thing_name}/device.pem.crt"
root_ca = f"/certs/AmazonRootCA1.pem"
region = "us-east-1"


def start_container(version, fallback_container):
    image = "firmware"
    docker_client = docker.from_env()

    container_name = f"{device_name}-firmware-{version}"
    labels = {"device": device_name}
    volumes = {}
    volumes[firmware_cert_mount_path] = {"bind": "/certs", "mode": "ro"}

    environment = {
        "THING_NAME": firmware_thing_name,
        "TOPIC": f"clients/{firmware_thing_name}/hello/world",
        "TIMER_PERIOD": "5",
    }

    print("Environment", environment)
    print("Labels", labels)
    print("Volumes", volumes)
    print("Network", network)

    try:
        container = docker_client.containers.get(container_name)
        print(f"Container {container_name} already exists, restarting")
        container.restart()
        return True

    except docker.errors.NotFound:
        print(f"Contain {container_name} does not exist. Creating.")

    print(f"Starting {container_name}...")
    try:
        print(f"Pulling image {registry}/{image}:{version}")
        docker_client.images.pull(f"{registry}/{image}:{version}")
        print(f"Starting container with image {registry}/{image}:{version}")

        container = docker_client.containers.run(
            f"{registry}/{image}:{version}",
            detach=True,
            name=container_name,
            labels=labels,
            volumes=volumes,
            environment=environment,
            network=network,
        )
        print(f"Container {container_name} started with id {container.id}")
        return True
    except docker.errors.APIError:
        print(f"Image {image}:{version} not found")
        if fallback_container:
            print(f"Falling back to {fallback_container.name}")
            fallback_container.restart()
        else:
            print(f"Image {image}:{version} not found and no fallback container available")
        return False
    except Exception as e:
        print(f"Error starting container: {e}")
        return False


def stop_container():
    docker_client = docker.from_env()
    containers = docker_client.containers.list(filters={"label": [f"device={device_name}"]})
    if not containers:
        print("No containers found for this device")
        return None
    # Really we should only have one container running per device. If ever we have more than one,
    # stop all of them and (arbitrarily) pick the first one as the fallback.
    for container in containers:
        print(f"Stopping {container.name}")
        container.stop()
    return containers[0]


def job_handler_callback_start_firmware_update(job_id, job_document):
    print("job_handler_callback_start_firmware_update job_id: " + str(job_id))
    print("job_handler_callback_start_firmware_update job_document: " + str(job_document))
    success_status = False
    if "version" in job_document:
        version = job_document["version"]
        fallback_container = stop_container()
        success_status = start_container(version, fallback_container)
    else:
        print("job_handler_callback_start_firmware_update missing version")
    print(f"job_handler_callback_start_firmware_update complete with status {success_status}")
    return success_status


def job_handler_callback(job_id, job_document):
    print("job_handler_callback job_id: " + str(job_id))
    print("job_handler_callback job_document: " + str(job_document))
    success_status = False
    if "operation" in job_document:
        operation = job_document["operation"]
        if operation == "Deploy-ROS-Firmware":
            success_status = job_handler_callback_start_firmware_update(job_id, job_document)
        else:
            print("job_handler_callback unknown operation: " + operation)

    print(f"job_handler_callback complete with status {success_status}")
    return success_status


def get_mqtt_connection_with_retry(thing_name, key, cert, region):
    while True:
        try:
            return get_mqtt_connection(thing_name, key, cert, region)
        except Exception as e:
            print(f"Connection failed with exception {e}. Retrying in 10 seconds...")
            time.sleep(10)


if __name__ == "__main__":
    if not device_name:
        print("DEVICE_NAME environment variable not set")
        exit(1)

    print(f"DEVICE_NAME {device_name}")
    print(f"thing_name {agent_thing_name}")

    mqtt_connection = get_mqtt_connection_with_retry(agent_thing_name, key, cert, region)

    job_handler = JobHandler(agent_thing_name, mqtt_connection, job_handler_callback)
    job_handler.run()
