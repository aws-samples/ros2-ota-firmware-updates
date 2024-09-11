#!/usr/bin/env python3
#
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import json
import datetime
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from awscrt import mqtt
from service.connection_helper import ConnectionHelper

RETRY_WAIT_TIME_SECONDS = 5


class MqttPublisher(Node):
    def __init__(self):
        super().__init__("service")
        self.declare_parameter("path_for_config", "")
        self.declare_parameter("version", "1")
        self.declare_parameter("topic", "clients/device-thing-0/hello/world")
        self.declare_parameter("client_id", "device-thing-0")
        self.declare_parameter("timer_period", 10)

        discover_endpoints = True

        path_for_config = self.get_parameter("path_for_config").get_parameter_value().string_value
        self.version = self.get_parameter("version").get_parameter_value().string_value
        self.topic = self.get_parameter("topic").get_parameter_value().string_value
        self.timer_period = self.get_parameter("timer_period").get_parameter_value().integer_value
        self.client_id = self.get_parameter("client_id").get_parameter_value().string_value

        self.get_logger().info(
            f"Initializing firmware version {self.version}. Publishing to {self.topic} as client id {self.client_id} every {self.timer_period} seconds"
        )

        self.connection_helper = ConnectionHelper(
            self.get_logger(), path_for_config, self.client_id, discover_endpoints
        )

        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def timer_callback(self):
        message_json = json.dumps(
            {
                "version": self.version,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        )
        self.get_logger().info(
            "Received data on ROS2 {}\nPublishing to AWS IoT".format(message_json)
        )
        self.connection_helper.mqtt_conn.publish(
            topic=self.topic, payload=message_json, qos=mqtt.QoS.AT_LEAST_ONCE
        )


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MqttPublisher()

    rclpy.spin(minimal_subscriber)

    # Destroy the node
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
