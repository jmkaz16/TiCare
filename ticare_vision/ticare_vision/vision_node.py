
import os
import rclpy
from glob import glob
from setuptools import setup
from rclpy.node import Node
from rclpy.action import ActionClient
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import String
from sensor_msgs.msg import Image
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration  
from cv_bridge import CvBridge
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from ultralytics import YOLO
import cv2
from enum import Enum

class VisionState(Enum):
    """Enumeration of all possible states for the Vision State Machine."""
    ESPERANDO_ORDEN = 1
    PREPARANDO_VISION = 2
    ESPERANDO_OBJETO = 3
    BUSQUEDA_ACTIVA = 4
    VISION_DETENIDA = 5
    EMERGENCIA = 6

class VisionNode(Node):
    """
    Manages object detection and TIAGo head control using a State Machine.
    """

    def __init__(self):
        super().__init__("vision_node")

        """
        Constructor method. Initializes the ROS 2 node, loads parameters (like the YOLO model path 
        and confidence threshold), sets up the YOLOv11 model, and establishes all the necessary 
        ROS publishers, subscribers, and action clients.
        """
        
        default_model_path = os.path.join(
    	get_package_share_directory("ticare_vision"),
    	"data",
    	"weights.pt")

        self.declare_parameter("model_path", default_model_path)
        self.declare_parameter("confidence_threshold", 0.6)
        model_path = self.get_parameter("model_path").value
        self.conf_thresh = self.get_parameter("confidence_threshold").value


        self.target_object = ""
        self.bridge = CvBridge()
        self.window_name = "TIAGo Vision - YOLO v11"

        self.current_state = VisionState.ESPERANDO_ORDEN
        self.get_logger().info(f"--- [STATE] Initialized in state: {self.current_state.name} ---")
        

        self.get_logger().info(f"--- [INIT] Loading YOLO v11 model: {model_path} ---")
        self.model = YOLO(model_path)

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=5
        )

        self.sub_com2vis = self.create_subscription(String, "/com2vis", self.com2vis_callback, qos_profile)
        self.sub_nav2vis = self.create_subscription(String, "/nav2vis", self.nav2vis_callback, qos_profile)
        self.sub_camera = self.create_subscription(Image, "/head_front_camera/rgb/image_raw", self.camera_callback, qos_profile) ## en la realidad la documentación pone como /head_front_camer/color/image_raw/*


        self.pub_vis2com = self.create_publisher(String, "/vis2com", qos_profile)
        self.pub_vis2nav = self.create_publisher(String, "/vis2nav", qos_profile)

        self.head_action_client = ActionClient(
            self, FollowJointTrajectory, "/head_controller/follow_joint_trajectory"
        )

        
        self.get_logger().info("--- [STATUS] Vision Node is READY and listening ---")



    def change_state(self, new_state: VisionState) -> None:
        """
        Handles state transitions for the vision state machine. 
        It also manages hardware resources: it opens the local webcam when entering 
        the active search state (BUSQUEDA_ACTIVA) and releases the camera and closes 
        windows when exiting that state.
        """

        if new_state == VisionState.BUSQUEDA_ACTIVA and self.current_state != VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info("--- [WEBCAM] Inicializando cámara local... ---")
            self.cap = cv2.VideoCapture(0) # 0 es la cámara por defecto del PC
            if not self.cap.isOpened():
                self.get_logger().error("!!! No se pudo acceder a la webcam !!!")

        if self.current_state == VisionState.BUSQUEDA_ACTIVA and new_state != VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info("--- [CLEANUP] Cerrando ventana y liberando webcam ---")
            if self.cap is not None:
                self.cap.release() 
            cv2.destroyAllWindows()
        self.get_logger().info(f"--- [STATE TRANSITION] {self.current_state.name} -> {new_state.name} ---")
        self.current_state = new_state

    def check_emergency(self, cmd: str) -> bool:
        """
        Checks if an emergency stop command ("PE") has been received.
        If it is an emergency, it transitions the system to the EMERGENCIA state.
        Returns True if it's an emergency, False otherwise.
        """

        if cmd == "PE":
            self.get_logger().error("!!! [EMERGENCY] Parada de Emergencia Triggered !!!")
            self.change_state(VisionState.EMERGENCIA)
            return True
        return False

    def com2vis_callback(self, msg: String) -> None:
        """
        Callback triggered when a message is received on the '/com2vis' topic.
        It handles commands from the communication node, such as moving the robot's head 
        or receiving the target object to search for, depending on the current state.
        """

        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from COM (/com2vis): '{cmd}' ---")
        if self.check_emergency(cmd):
            return
        if self.current_state == VisionState.ESPERANDO_ORDEN:
            if cmd == "head_up":
                self.move_head(0.0) 
                self.change_state(VisionState.PREPARANDO_VISION)
        elif self.current_state == VisionState.PREPARANDO_VISION:
            if cmd.startswith("object_"):
                self.target_object = cmd.replace("object_", "")
                self.get_logger().info(f"--- [CONFIG] New target saved: {self.target_object} ---")
                self.change_state(VisionState.ESPERANDO_OBJETO)
        elif self.current_state == VisionState.VISION_DETENIDA:
            if cmd == "head_down":
                self.move_head(-0.75)
                self.change_state(VisionState.ESPERANDO_ORDEN)

    def nav2vis_callback(self, msg: String) -> None:
        """
        Callback triggered when a message is received on the '/nav2vis' topic.
        It handles commands from the navigation node, mainly to start or stop 
        the active visual search process.
        """

        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from NAV (/nav2vis): '{cmd}' ---")
        if self.check_emergency(cmd):
            return
        if self.current_state == VisionState.ESPERANDO_OBJETO:
            if cmd == "start_vis":
                self.change_state(VisionState.BUSQUEDA_ACTIVA)
                self.move_head(-0.5)
        elif self.current_state == VisionState.BUSQUEDA_ACTIVA:
            if cmd == "stop_vis":
                self.change_state(VisionState.VISION_DETENIDA)
                self.move_head(0.0)


    def camera_callback(self, msg: Image) -> None:
        """
        Callback triggered every time a new image frame is published on the robot's camera topic.
        It converts the ROS image to an OpenCV format, runs YOLO object detection, 
        displays the frame, and checks if the detected objects match the target object. 
        If a match is found, it alerts the other nodes.
        """
        if self.current_state != VisionState.BUSQUEDA_ACTIVA:
            return
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Error convirtiendo la imagen: {e}")
            return
        cv2.imshow("Lo que ve TIAGo", cv_image)
        cv2.waitKey(1)
        results = self.model.predict(cv_image, conf=self.conf_thresh, verbose=False)
        annotated_frame = results[0].plot()
        cv2.imshow(self.window_name, annotated_frame)
        cv2.waitKey(1)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                if class_name == self.target_object:
                    self.get_logger().info(f"*** [DETECTION] Found: {class_name}! ***")
                    out_msg = String()
                    out_msg.data = "object_detected"
                    self.pub_vis2com.publish(out_msg)
                    self.pub_vis2nav.publish(out_msg)
                    self.get_logger().info("--- [OUT] Publishing 'object_detected' to COM/NAV ---")
                    self.change_state(VisionState.VISION_DETENIDA)
                    return

    def move_head(self, tilt: float) -> None:
        """
        Sends an asynchronous action goal to the robot's head controller to tilt the head.
        Takes a 'tilt' value (in radians) to adjust the up/down angle of TIAGo's head.
        """
        """Sends a movement command to TIAGo's head via Action Server."""
        if not self.head_action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warn("--- [WARN] Head controller (Gazebo) not found! ---")
            return
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ["head_1_joint", "head_2_joint"]
        point = JointTrajectoryPoint()
        point.positions = [0.0, tilt] 
        point.time_from_start = Duration(sec=2, nanosec=0) 
        goal.trajectory.points = [point]
        self.get_logger().info(f"--- [ACTION] Sending head movement goal: {tilt} rad to Gazebo ---")
        self.head_action_client.send_goal_async(goal)

def main(args=None):
    """
    Main entry point for the ROS 2 node. Initializes the rclpy library, 
    spins up the VisionNode, and ensures proper cleanup (releasing the camera, 
    destroying windows, and shutting down ROS) upon exiting.
    """
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.cap is not None:
            node.cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()