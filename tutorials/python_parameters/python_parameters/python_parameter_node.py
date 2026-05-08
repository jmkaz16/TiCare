import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor

class MinimalParam(rclpy.node.Node):
    def __init__(self):
        super().__init__('minimal_param_node')

        descriptor = ParameterDescriptor(description='A string parameter')

        self.declare_parameter('my_parameter', 'world', descriptor) # (name, default_value, descriptor)

        self.timer = self.create_timer(1, self.timer_callback)

    def timer_callback(self):
        my_param = self.get_parameter('my_parameter').get_parameter_value().string_value

        self.get_logger().info(f'Hello {my_param}!')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalParam()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()