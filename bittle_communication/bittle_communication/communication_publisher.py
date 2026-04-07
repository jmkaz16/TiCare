#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory


import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class CommunicationPublisher(Node):

    def __init__(self):
        super().__init__('communication_publisher')
        self.publisher_ = self.create_publisher(String, 'bittle_cmd', 10)
        timer_period = 10  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

        # Obtain the base path to the installed package
        package_share_path = get_package_share_directory('bittle_communication')
        # Save the path of the 'data' folder as a variable to avoid recalculating it eveery time a position is saved
        self.data_dir = os.path.join(package_share_path, 'data')
        self.file_path = os.path.join(self.data_dir, 'order.txt')

    def timer_callback(self):
        msg = String()
        msg.data = self.read_from_file()
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1

    def read_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return f.read().strip()
        else:
            self.get_logger().warn(f"File {self.file_path} does not exist.")


def main(args=None):
    rclpy.init()

    communication_publisher = CommunicationPublisher()

    try:
        # rclpy.spin(communication_publisher)
        communication_publisher.timer_callback()  # Call the timer callback once
    
    except KeyboardInterrupt:
        pass
    
    finally:
        communication_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()