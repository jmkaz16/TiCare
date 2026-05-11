
import os
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import String
from sensor_msgs.msg import Image
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration  
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from enum import Enum

class VisionState(Enum):
    """
    Manages object detection and TIAGo head control using a State Machine.
    """
    ESPERANDO_ORDEN = 1
    PREPARANDO_VISION = 2
    ESPERANDO_OBJETO = 3
    BUSQUEDA_ACTIVA = 4
    VISION_DETENIDA = 5
    EMERGENCIA = 6

class VisionNode(Node):
    """
        Constructor method. Initializes the ROS 2 node, declares and retrieves parameters 
        (like model path, confidence threshold, and camera ID), loads the YOLO model, 
        and sets up all publishers, subscribers, action clients, and a timer for the webcam.
    """
    def __init__(self):
        super().__init__("vision_node")
        default_model_path = os.path.join(
    	get_package_share_directory("ticare_vision"),
    	"data",
    	"weights.pt")

        self.declare_parameter("model_path", default_model_path)

        self.declare_parameter("confidence_threshold", 0.6)
        
        model_path = self.get_parameter("model_path").value
        self.conf_thresh = self.get_parameter("confidence_threshold").value
        self.declare_parameter("camera_id", 0)
        # Internal State
        self.target_object = ""
        self.bridge = CvBridge()
        self.window_name = "TIAGo Vision - YOLO v11"
        
        self.cap = None
        self.camera_id = self.get_parameter("camera_id").value
        # State Machine Initialization
        self.current_state = VisionState.ESPERANDO_ORDEN
        self.get_logger().info(f"--- [STATE] Initialized in state: {self.current_state.name} ---")
        
        # Load YOLO Model (Commented out for mock testing)
        self.get_logger().info(f"--- [INIT] Loading YOLO v11 model: {model_path} ---")
        self.model = YOLO(model_path)

        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=5
        )


        self.sub_com2vis = self.create_subscription(String, "/com2vis", self.com2vis_callback, qos_profile)
        self.sub_nav2vis = self.create_subscription(String, "/nav2vis", self.nav2vis_callback, qos_profile)
       
        # --- PUBLISHERS ---
        self.pub_vis2com = self.create_publisher(String, "/vis2com", qos_profile)
        self.pub_vis2nav = self.create_publisher(String, "/vis2nav", qos_profile)

        self.head_action_client = ActionClient(
            self, FollowJointTrajectory, "/head_controller/follow_joint_trajectory"
        )

        self.timer = self.create_timer(0.05, self.process_webcam)
        
        self.get_logger().info("--- [STATUS] Vision Node is READY and listening ---")

    def change_state(self, new_state: VisionState) -> None:
        """
        Handles state transitions and manages the local webcam resources.
        It initializes the camera with specific parameters (V4L2, MJPG, 640x480) when 
        entering the active search state, and releases it when leaving the state.
        """
        if new_state == VisionState.BUSQUEDA_ACTIVA and self.current_state != VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info("--- [WEBCAM] Inicializando cámara local... ---")

            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_V4L2) 
            
            if self.cap.isOpened():

                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
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
        Checks if the incoming command is an emergency stop ("PE").
        Transitions the state machine to the EMERGENCY state if triggered.
        Returns True if an emergency was detected, False otherwise.
        """
        if cmd == "PE":
            self.get_logger().error("!!! [EMERGENCY] Parada de Emergencia Triggered !!!")
            self.change_state(VisionState.EMERGENCIA)
            return True
        return False
    
    def com2vis_callback(self, msg: String) -> None:

        """
        Callback for commands received from the Communication (COM) node.
        Handles actions like setting the target object and adjusting the 
        robot's head position based on the current state.
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
                self.move_head(-0.5)   
                self.change_state(VisionState.ESPERANDO_ORDEN)


    def nav2vis_callback(self, msg: String) -> None:
        """
        Callback for commands received from the Navigation (NAV) node.
        Used primarily to start or stop the active visual search routine.
        """
        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from NAV (/nav2vis): '{cmd}' ---")
        if self.check_emergency(cmd):
            return
        if self.current_state == VisionState.ESPERANDO_OBJETO:
            if cmd == "start_vis":
                self.change_state(VisionState.BUSQUEDA_ACTIVA)
                self.move_head(-0.2)
        elif self.current_state == VisionState.BUSQUEDA_ACTIVA:
            if cmd == "stop_vis":
                self.change_state(VisionState.VISION_DETENIDA)
                self.move_head(0.0)


    def process_webcam(self) -> None:
        """
        Timer callback triggered every 0.05 seconds. 
        Reads the current frame from the local webcam, runs the YOLO prediction, 
        displays the frame with bounding boxes, and checks if the target object was found.
        """
        if self.current_state != VisionState.BUSQUEDA_ACTIVA:
            return
        if self.cap is None or not self.cap.isOpened():
            return
        ret, cv_image = self.cap.read()
        if not ret:
            self.get_logger().warning("Fallo al leer frame de la webcam. Reintentando...")
            return
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
        Sends an action goal to Gazebo (or the real robot) to tilt TIAGo's head.
        Requires a tilt value in radians.
        """
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
    Main entry point for the node. Initializes ROS 2, spins the VisionNode 
    to process callbacks, and ensures safe resource cleanup (releasing webcam, 
    closing windows) upon termination.
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