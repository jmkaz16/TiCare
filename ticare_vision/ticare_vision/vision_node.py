import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from sensor_msgs.msg import Image
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from cv_bridge import CvBridge
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

    This node subscribes to communication and navigation topics to coordinate 
    vision tasks and head movements following a strict state flow.
    """

    def __init__(self):
        """Initialize the node, parameters, state machine, and ROS 2 interfaces."""
        super().__init__("vision_node")

        # Configuration Parameters
        self.declare_parameter("model_path", "/home/luisgfgetino/ticare_ws/src/ticare_vision/data/weights.pt")
        self.declare_parameter("confidence_threshold", 0.6)
        
        model_path = self.get_parameter("model_path").value
        self.conf_thresh = self.get_parameter("confidence_threshold").value

        # Internal State
        self.target_object = ""
        self.bridge = CvBridge()
        
        # State Machine Initialization
        self.current_state = VisionState.ESPERANDO_ORDEN
        self.get_logger().info(f"--- [STATE] Initialized in state: {self.current_state.name} ---")
        
        # Load YOLO Model (Architecture YOLO v11) - Commented out for mock testing
        self.get_logger().info(f"--- [INIT] Loading YOLO v11 model: {model_path} ---")
        self.model = YOLO(model_path)

        # --- SUBSCRIBERS ---
        self.sub_com2vis = self.create_subscription(
            String, "/com2vis", self.com2vis_callback, 10
        )
        self.sub_nav2vis = self.create_subscription(
            String, "/nav2vis", self.nav2vis_callback, 10
        )
        self.sub_camera = self.create_subscription(
            Image, "/xtion/rgb/image_rect_color", self.camera_callback, 10
        )

        # --- PUBLISHERS ---
        self.pub_vis2com = self.create_publisher(String, "/vis2com", 10)
        self.pub_vis2nav = self.create_publisher(String, "/vis2nav", 10)

        # Action Client for TIAGo Head
        self.head_action_client = ActionClient(
            self, FollowJointTrajectory, "/head_controller/follow_joint_trajectory"
        )
        
        self.get_logger().info("--- [STATUS] Vision Node is READY and listening ---")

    def change_state(self, new_state: VisionState) -> None:
        """
        Handles state transitions safely and logs them.
        
        Args:
            new_state (VisionState): The target state to transition to.
        """
        self.get_logger().info(
            f"--- [STATE TRANSITION] {self.current_state.name} -> {new_state.name} ---"
        )
        self.current_state = new_state

    def check_emergency(self, cmd: str) -> bool:
        """
        Checks for emergency commands to trigger an immediate state change.
        
        Args:
            cmd (str): The received command string.
            
        Returns:
            bool: True if an emergency was triggered, False otherwise.
        """
        if cmd == "PE":
            self.get_logger().error("!!! [EMERGENCY] Parada de Emergencia Triggered !!!")
            self.change_state(VisionState.EMERGENCIA)
            return True
        return False

    def com2vis_callback(self, msg: String) -> None:
        """
        Handles messages from the Communication module acting as state triggers. 
        
        Args:
            msg (String): Message received (head_up, head_down, object_X, PE, rearme manual).
        """
        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from COM (/com2vis): '{cmd}' ---")

        if self.check_emergency(cmd):
            return

        # State Machine Logic for Communication Commands       
        if self.current_state == VisionState.ESPERANDO_ORDEN:
            if cmd == "head_up":
                #self.move_head(-0.5)
                self.change_state(VisionState.PREPARANDO_VISION)

        elif self.current_state == VisionState.PREPARANDO_VISION:
            if cmd.startswith("object_"):
                self.target_object = cmd.replace("object_", "")
                self.get_logger().info(f"--- [CONFIG] New target saved: {self.target_object} ---")
                self.change_state(VisionState.ESPERANDO_OBJETO)

        elif self.current_state == VisionState.VISION_DETENIDA:
            if cmd == "head_down":
                #self.move_head(0.5)
                self.change_state(VisionState.ESPERANDO_ORDEN)

    def nav2vis_callback(self, msg: String) -> None:
        """
        Handles messages from the Navigation module acting as state triggers. 
        
        Args:
            msg (String): Message received (start_vis, stop_vis, PE).
        """
        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from NAV (/nav2vis): '{cmd}' ---")

        if self.check_emergency(cmd):
            return

        # State Machine Logic for Navigation Commands
        if self.current_state == VisionState.ESPERANDO_OBJETO:
            if cmd == "start_vis":
                self.change_state(VisionState.BUSQUEDA_ACTIVA)
                self.trigger_mock_detection() # Descomentar para test manual sin cámara

        elif self.current_state == VisionState.BUSQUEDA_ACTIVA:
            if cmd == "stop_vis":
                self.change_state(VisionState.VISION_DETENIDA)

    def trigger_mock_detection(self) -> None:
        """Simulates finding the object immediately after activating vision."""
        if self.current_state == VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info(f"*** [MOCK] Simulando deteccion de: {self.target_object} ***")
            
            out_msg = String()
            out_msg.data = "object_detected"
            self.pub_vis2com.publish(out_msg)
            self.pub_vis2nav.publish(out_msg)
            
            self.get_logger().info("--- [OUT] Publicado 'object_detected' a COM y NAV ---")
            self.change_state(VisionState.VISION_DETENIDA)

    def camera_callback(self, msg: Image) -> None:
        """
        Processes frames. Only executes inference if in BUSQUEDA_ACTIVA state.
        """
        # Protegemos el callback: solo evalúa imágenes si está en el estado correcto
        if self.current_state != VisionState.BUSQUEDA_ACTIVA:
            return

        # # --- MOCK LOGIC (from your code) ---
        # self.get_logger().info(f"*** [MOCK DETECTION] Simulando que he encontrado: {self.target_object}! ***")
        
        # out_msg = String()
        # out_msg.data = "object_detected"
        # self.pub_vis2com.publish(out_msg)
        # self.pub_vis2nav.publish(out_msg)
        
        # # Actualizamos la máquina de estados
        # self.change_state(VisionState.VISION_DETENIDA)
        # return 

        # --- REAL YOLO LOGIC (Commented out) ---
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        results = self.model(cv_image, conf=self.conf_thresh, verbose=False)
        
        for result in results:
            for box in result.boxes:
                class_name = self.model.names[int(box.cls[0])]
                if class_name == self.target_object:
                    self.get_logger().info(f"*** [DETECTION] Found: {class_name}! ***")
                    out_msg = String()
                    out_msg.data = "object_detected"
                    self.pub_vis2com.publish(out_msg)
                    self.pub_vis2nav.publish(out_msg)
                    self.get_logger().info("--- [OUT] Publishing 'object_detected' to COM and NAV ---")
                    self.change_state(VisionState.VISION_DETENIDA)
                    return

    def move_head(self, tilt: float) -> None:
        """Sends a movement command to TIAGo's head via Action Server."""
        if not self.head_action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn("--- [WARN] Head controller not found! ---")
            return

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ["head_1_joint", "head_2_joint"]
        point = JointTrajectoryPoint()
        point.positions = [0.0, tilt]
        point.time_from_start.sec = 2
        goal.trajectory.points = [point]

        self.get_logger().info(f"--- [ACTION] Sending head movement goal: {tilt} rad ---")
        self.head_action_client.send_goal_async(goal)

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()