import rclpy
from rclpy.node import Node

from ticare_interfaces.srv import SavePose

class PoseRecorder(Node):

    def __init__(self):
        super().__init__('pose_recorder')
        self.srv = self.create_service(SavePose, 'save_pose', self.save_pose_callback)

    def save_pose_callback(self, request, response):
        response.success = True
        response.message = f'Pose saved successfully: {request.label}'
        self.get_logger().info(f'Incoming request: {request.label}')

        return response

# ros2 service call /save_pose ticare_interfaces/srv/SavePose "{label: 'juan'}"

def main():
    rclpy.init()

    pose_recorder = PoseRecorder()

    rclpy.spin(pose_recorder)

    pose_recorder.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()