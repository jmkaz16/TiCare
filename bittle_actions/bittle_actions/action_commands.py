#!/usr/bin/env python3

import rclpy 
from rclpy.node import Node

from std_msgs.msg import String

# import serial
import socket
# import time

'''BITTLE_COMMANDS = {
    "stand": "kup",
    "butt_up": "kbuttUp",
    "calibrate": "kcalib",
    "rest": "krest",
    "sit": "ksit",
    "stretch": "kstr",
    "backward": "kbk",
    "backward_left": "kbkL",
    "backward_right": "kbkR",
    "jump_forward": "kjpF",
    "push_forward": "kphF",
    "push_left": "kphL",
    "push_right": "kphR",
    "walk_forward": "kwkF",
    "walk_left": "kwkL",
    "walk_right": "kwkR",
    "trot_forward": "ktrF",
    "trot_lef": "ktrL",
    "trot_right": "ktrR",
    "boxing": "kbx",
    "cheers": "kchr",
    "dig": "kdg",
    "high_five": "kfiv",
    "handstand": "khds",
    "hug": "khg",
    "hi": "khi",
    "hands_up": "khu",
    "jump": "kjmp",
    "kick": "kkc",
    "moon_walk": "kmw",
    "play_dead": "kpd", # no me convence
    "pee": "kpee",
    "push_ups": "kpu",
    # "recover": "krc", para cuando esté boca arriba
    "scratch": "kscrh",
    "sniff": "ksnf",
    "be_table": "ktbl",
    "wave_head": "kwh",
    "sleep": "kzz",
    "frontflip": "kff",
    "backflip": "kbf"
}'''

class BittleAction(Node):

    def __init__(self):
        super().__init__('bittle_action')
        
        self.declare_parameter('MAC_ADDRESS', '00:00:00:00:00:AA') # declare a parameter with a default empty value
        self.MAC = self.get_parameter('MAC_ADDRESS').get_parameter_value().string_value
        self.get_logger().info(f'Configuring Bittle with MAC address: {self.MAC}')
        
        # self.ser = serial.Serial('/dev/rfcomm0', 115200, timeout=1)
        self.ser = None
        self.connect_serial()
        
        self.subscription = self.create_subscription(
            String,
            '/bittle_cmd',
            self.execute_command,
            10)
        self.subscription  # prevent unused variable warning

    def connect_serial(self, PORT=1):
        try:
            self.ser = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM
            )
            self.ser.connect((self.MAC, PORT))
            self.get_logger().info(f'Connected to Bittle {self.MAC}!')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to Bittle: {e}')

    def execute_command(self, msg):
        if self.ser is None:
            self.get_logger().error('Serial connection not established')
            return
        # cmd = BITTLE_COMMANDS.get(msg.data) con diccionario
        cmd = "k" + msg.data
        if cmd:
            self.ser.send(f'{cmd}\n'.encode())
            self.get_logger().info(f'Sent:{cmd}')
        else:
            self.get_logger().warn('Unknown command')

    def __del__(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()


def main(args=None):
    rclpy.init(args=args)

    bittle_action = BittleAction()

    try:
        rclpy.spin(bittle_action)
    except KeyboardInterrupt: # Ctrl+C
        pass
    finally:
        bittle_action.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()