import rclpy 
from rclpy.node import Node

from std_msgs.msg import String

import serial
import time

BITTLE_COMMANDS = {
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
}

class BittleAction(Node):

    def __init__(self):
        super().__init__('bittle_action')
        self.ser = serial.Serial('/dev/rfcomm0', 115200, timeout=1)
        time.sleep(2)
        self.subscription = self.create_subscription(
            String,
            '/bittle_cmd',
            self.execute_command,
            10)
        self.subscription  # prevent unused variable warning

    def execute_command(self, msg):
        cmd = BITTLE_COMMANDS.get(msg.data)
        if cmd:
            self.ser.write(f'{cmd}\n'.encode())
            self.ser.flush() # forces transmisssion from OS serial write buffer to Bittle
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