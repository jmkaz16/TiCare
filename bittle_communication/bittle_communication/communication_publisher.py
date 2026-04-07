#!/usr/bin/env python3

import os
import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class CommunicationPublisher(Node):

    def __init__(self):
        super().__init__('communication_publisher')
        self.publisher_ = self.create_publisher(String, 'bittle_raw', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = self.read_from_file()
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1

    def read_from_file(self, file="order.txt"):
        if os.path.exists(file):
            with open(file, "r") as f:
                return f.read().strip()
        else:
            self.get_logger().warn(f"File {file} does not exist.")


def main(args=None):
    rclpy.init()

    communication_publisher = CommunicationPublisher()

    try:
        rclpy.spin(communication_publisher)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        communication_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()