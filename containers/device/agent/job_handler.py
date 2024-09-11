# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import time
import json
import sys
import traceback
import threading
from awscrt import io, http, mqtt
from awscrt.mqtt import QoS
from awsiot.greengrass_discovery import DiscoveryClient
from awsiot import iotjobs, mqtt_connection_builder
from concurrent.futures import Future


class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.disconnect_called = False
        self.is_working_on_job = False
        self.is_next_job_waiting = False
        self.got_job_response = False


class JobHandler:
    def __init__(self, thing_name, mqtt_connection, job_handler_callback):
        self.thing_name = thing_name
        self.job_handler_callback = job_handler_callback
        self.mqtt_connection = mqtt_connection
        self.jobs_client = iotjobs.IotJobsClient(self.mqtt_connection)
        self.available_jobs = []
        self.locked_data = LockedData()
        self.is_sample_done = threading.Event()

    def on_get_pending_job_executions_accepted_closure(self):
        def on_get_pending_job_executions_accepted(response):
            # type: (iotjobs.GetPendingJobExecutionsResponse) -> None
            with self.locked_data.lock:
                if len(response.queued_jobs) > 0 or len(response.in_progress_jobs) > 0:
                    print("Pending Jobs:")
                    for job in response.in_progress_jobs:
                        self.available_jobs.append(job)
                        print(f"  In Progress: {job.job_id} @ {job.last_updated_at}")
                    for job in response.queued_jobs:
                        self.available_jobs.append(job)
                        print(f"  {job.job_id} @ {job.last_updated_at}")
                else:
                    print("No pending or queued jobs found!")
                self.locked_data.got_job_response = True

        return on_get_pending_job_executions_accepted

    def on_get_pending_job_executions_rejected_closure(self):
        def on_get_pending_job_executions_rejected(error):
            # type: (iotjobs.RejectedError) -> None
            print(f"Request rejected: {error.code}: {error.message}")
            self.exit("Get pending jobs request rejected!")

        return on_get_pending_job_executions_rejected

    def on_next_job_execution_changed_closure(self):
        def on_next_job_execution_changed(event):
            # type: (iotjobs.NextJobExecutionChangedEvent) -> None
            try:
                execution = event.execution
                if execution:
                    print(
                        "Received Next Job Execution Changed event. job_id:{} job_document:{}".format(
                            execution.job_id, execution.job_document
                        )
                    )

                    # Start job now, or remember to start it when current job is done
                    start_job_now = False
                    with self.locked_data.lock:
                        if self.locked_data.is_working_on_job:
                            self.locked_data.is_next_job_waiting = True
                        else:
                            start_job_now = True

                    if start_job_now:
                        self.try_start_next_job()

                else:
                    print(
                        "Received Next Job Execution Changed event: None. Waiting for further jobs..."
                    )

            except Exception as e:
                self.exit(e)

        return on_next_job_execution_changed

    def on_start_next_pending_job_execution_accepted_closure(self):
        def on_start_next_pending_job_execution_accepted(response):
            # type: (iotjobs.StartNextJobExecutionResponse) -> None
            try:
                if response.execution:
                    execution = response.execution
                    print(
                        "Request to start next job was accepted. job_id:{} job_document:{}".format(
                            execution.job_id, execution.job_document
                        )
                    )

                    # To emulate working on a job, spawn a thread that sleeps for a few seconds
                    job_thread = threading.Thread(
                        target=lambda: self.job_thread_fn(execution.job_id, execution.job_document),
                        name="job_thread",
                    )
                    job_thread.start()
                else:
                    print(
                        "Request to start next job was accepted, but there are no jobs to be done. Waiting for further jobs..."
                    )
                    self.done_working_on_job()

            except Exception as e:
                self.exit(e)

        return on_start_next_pending_job_execution_accepted

    def on_start_next_pending_job_execution_rejected_closure(self):
        def on_start_next_pending_job_execution_rejected(rejected):
            # type: (iotjobs.RejectedError) -> None
            self.exit(
                "Request to start next pending job rejected with code:'{}' message:'{}'".format(
                    rejected.code, rejected.message
                )
            )

        return on_start_next_pending_job_execution_rejected

    def on_update_job_execution_accepted_closure(self):
        def on_update_job_execution_accepted(response):
            # type: (iotjobs.UpdateJobExecutionResponse) -> None
            try:
                print("Request to update job was accepted.")
                self.done_working_on_job()
            except Exception as e:
                self.exit(e)

        return on_update_job_execution_accepted

    def on_update_job_execution_rejected_closure(self):
        def on_update_job_execution_rejected(rejected):
            # type: (iotjobs.RejectedError) -> None
            self.exit(
                "Request to update job status was rejected. code:'{}' message:'{}'.".format(
                    rejected.code, rejected.message
                )
            )

        return on_update_job_execution_rejected

    def on_publish_start_next_pending_job_execution_closure(self):
        def on_publish_start_next_pending_job_execution(future):
            try:
                future.result()  # raises exception if publish failed

                print("Published request to start the next job.")

            except Exception as e:
                self.exit(e)

        return on_publish_start_next_pending_job_execution

    def on_publish_update_job_execution_closure(self):
        def on_publish_update_job_execution(future):
            # type: (Future) -> None
            try:
                future.result()  # raises exception if publish failed
                print("Published request to update job.")

            except Exception as e:
                self.exit(e)

        return on_publish_update_job_execution

    # Function for gracefully quitting this sample
    def exit(self, msg_or_exception):
        if isinstance(msg_or_exception, Exception):
            print("Exiting Sample due to exception.")
            traceback.print_exception(
                msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2]
            )
        else:
            print("Exiting Sample:", msg_or_exception)

        with self.locked_data.lock:
            if not self.locked_data.disconnect_called:
                print("Disconnecting...")
                self.locked_data.disconnect_called = True
                future = self.mqtt_connection.disconnect()
                future.add_done_callback(self.on_disconnected_closure())

    def try_start_next_job(self):
        print("Trying to start the next job...")
        with self.locked_data.lock:
            if self.locked_data.is_working_on_job:
                print("Nevermind, already working on a job.")
                return

            if self.locked_data.disconnect_called:
                print("Nevermind, sample is disconnecting.")
                return

            self.locked_data.is_working_on_job = True
            self.locked_data.is_next_job_waiting = False

        print("Publishing request to start next job...")
        request = iotjobs.StartNextPendingJobExecutionRequest(thing_name=self.thing_name)
        publish_future = self.jobs_client.publish_start_next_pending_job_execution(
            request, mqtt.QoS.AT_LEAST_ONCE
        )
        publish_future.add_done_callback(self.on_publish_start_next_pending_job_execution_closure())

    def done_working_on_job(self):
        with self.locked_data.lock:
            self.locked_data.is_working_on_job = False
            try_again = self.locked_data.is_next_job_waiting

        if try_again:
            self.try_start_next_job()

    def job_thread_fn(self, job_id, job_document):
        try:
            print("Starting local work on job...")
            # time.sleep(self.input_job_time)
            success_status = self.job_handler_callback(job_id, job_document)
            print("Done working on job.")

            status = iotjobs.JobStatus.FAILED
            if success_status:
                status = iotjobs.JobStatus.SUCCEEDED
            print(f"Publishing request to update job status to {status}")
            request = iotjobs.UpdateJobExecutionRequest(
                thing_name=self.thing_name, job_id=job_id, status=status
            )
            publish_future = self.jobs_client.publish_update_job_execution(
                request, mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.add_done_callback(self.on_publish_update_job_execution_closure())

        except Exception as e:
            exit(e)

    def on_disconnected_closure(self):
        def on_disconnected(disconnect_future):
            # type: (Future) -> None
            print("Disconnected.")

            # Signal that sample is finished
            self.is_sample_done.set()

        return on_disconnected

    def run(self):
        try:
            # List the jobs queued and pending
            print("Subscribing to GetPendingJobExecutions responses...")
            get_jobs_request = iotjobs.GetPendingJobExecutionsRequest(thing_name=self.thing_name)
            jobs_request_future_accepted, _ = (
                self.jobs_client.subscribe_to_get_pending_job_executions_accepted(
                    request=get_jobs_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_get_pending_job_executions_accepted_closure(),
                )
            )
            # Wait for the subscription to succeed
            jobs_request_future_accepted.result()

            jobs_request_future_rejected, _ = (
                self.jobs_client.subscribe_to_get_pending_job_executions_rejected(
                    request=get_jobs_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_get_pending_job_executions_rejected_closure(),
                )
            )
            # Wait for the subscription to succeed
            jobs_request_future_rejected.result()

            # Get a list of all the jobs
            get_jobs_request_future = self.jobs_client.publish_get_pending_job_executions(
                request=get_jobs_request, qos=mqtt.QoS.AT_LEAST_ONCE
            )
            # Wait for the publish to succeed
            get_jobs_request_future.result()
        except Exception as e:
            self.exit(e)

        try:
            # Subscribe to necessary topics.
            # Note that is **is** important to wait for "accepted/rejected" subscriptions
            # to succeed before publishing the corresponding "request".
            print("Subscribing to Next Changed events...")
            changed_subscription_request = iotjobs.NextJobExecutionChangedSubscriptionRequest(
                thing_name=self.thing_name
            )

            subscribed_future, _ = self.jobs_client.subscribe_to_next_job_execution_changed_events(
                request=changed_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_next_job_execution_changed_closure(),
            )

            # Wait for subscription to succeed
            subscribed_future.result()

            print("Subscribing to Start responses...")
            start_subscription_request = iotjobs.StartNextPendingJobExecutionSubscriptionRequest(
                thing_name=self.thing_name
            )
            subscribed_accepted_future, _ = (
                self.jobs_client.subscribe_to_start_next_pending_job_execution_accepted(
                    request=start_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_start_next_pending_job_execution_accepted_closure(),
                )
            )

            subscribed_rejected_future, _ = (
                self.jobs_client.subscribe_to_start_next_pending_job_execution_rejected(
                    request=start_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_start_next_pending_job_execution_rejected_closure(),
                )
            )

            # Wait for subscriptions to succeed
            subscribed_accepted_future.result()
            subscribed_rejected_future.result()

            print("Subscribing to Update responses...")
            # Note that we subscribe to "+", the MQTT wildcard, to receive
            # responses about any job-ID.
            update_subscription_request = iotjobs.UpdateJobExecutionSubscriptionRequest(
                thing_name=self.thing_name, job_id="+"
            )

            subscribed_accepted_future, _ = (
                self.jobs_client.subscribe_to_update_job_execution_accepted(
                    request=update_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_update_job_execution_accepted_closure(),
                )
            )

            subscribed_rejected_future, _ = (
                self.jobs_client.subscribe_to_update_job_execution_rejected(
                    request=update_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.on_update_job_execution_rejected_closure(),
                )
            )

            # Wait for subscriptions to succeed
            subscribed_accepted_future.result()
            subscribed_rejected_future.result()

            # Make initial attempt to start next job. The service should reply with
            # an "accepted" response, even if no jobs are pending. The response
            # will contain data about the next job, if there is one.
            # (Will do nothing if we are in CI)
            self.try_start_next_job()

        except Exception as e:
            self.exit(e)

        # Wait for the sample to finish
        self.is_sample_done.wait()
