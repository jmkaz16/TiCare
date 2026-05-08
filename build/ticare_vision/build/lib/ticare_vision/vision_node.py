
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


        # # Configuration Parameters
        default_model_path = os.path.join(
    	get_package_share_directory("ticare_vision"),
    	"data",
    	"weights.pt"
	)

        self.declare_parameter("model_path", default_model_path)

        self.declare_parameter("confidence_threshold", 0.6)
        
        model_path = self.get_parameter("model_path").value
        self.conf_thresh = self.get_parameter("confidence_threshold").value

        # Internal State
        self.target_object = ""
        self.bridge = CvBridge()
        self.window_name = "TIAGo Vision - YOLO v11"
        
        # State Machine Initialization
        self.current_state = VisionState.ESPERANDO_ORDEN
        self.get_logger().info(f"--- [STATE] Initialized in state: {self.current_state.name} ---")
        
        # Load YOLO Model (Commented out for mock testing)
        self.get_logger().info(f"--- [INIT] Loading YOLO v11 model: {model_path} ---")
        self.model = YOLO(model_path)

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=5
        )
        # --- SUBSCRIBERS ---
        self.sub_com2vis = self.create_subscription(String, "/com2vis", self.com2vis_callback, qos_profile)
        self.sub_nav2vis = self.create_subscription(String, "/nav2vis", self.nav2vis_callback, qos_profile)
        self.sub_camera = self.create_subscription(Image, "/head_front_camera/rgb/image_raw", self.camera_callback, qos_profile) ## en la realidad la documentación pone como /head_front_camer/color/image_raw/*

        # --- PUBLISHERS ---
        self.pub_vis2com = self.create_publisher(String, "/vis2com", qos_profile)
        self.pub_vis2nav = self.create_publisher(String, "/vis2nav", qos_profile)

        # --- ACTION CLIENT FOR TIAGo HEAD ---
        # Este es el canal de comunicación hacia el controlador de Gazebo
        self.head_action_client = ActionClient(
            self, FollowJointTrajectory, "/head_controller/follow_joint_trajectory"
        )

        
        self.get_logger().info("--- [STATUS] Vision Node is READY and listening ---")

    def change_state(self, new_state: VisionState) -> None:

        
    # Lógica de transición HACIA Busqueda Activa (Encender cámara)
        if new_state == VisionState.BUSQUEDA_ACTIVA and self.current_state != VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info("--- [WEBCAM] Inicializando cámara local... ---")
            self.cap = cv2.VideoCapture(0) # 0 es la cámara por defecto del PC
            if not self.cap.isOpened():
                self.get_logger().error("!!! No se pudo acceder a la webcam !!!")

        # Lógica de transición SALIENDO de Busqueda Activa (Apagar cámara)
        if self.current_state == VisionState.BUSQUEDA_ACTIVA and new_state != VisionState.BUSQUEDA_ACTIVA:
            self.get_logger().info("--- [CLEANUP] Cerrando ventana y liberando webcam ---")
            if self.cap is not None:
                self.cap.release() # Apaga la luz de la webcam
            cv2.destroyAllWindows()

        # if self.current_state == VisionState.BUSQUEDA_ACTIVA and new_state != VisionState.BUSQUEDA_ACTIVA:
        #     self.get_logger().info("--- [CLEANUP] Closing vision window ---")
        #     cv2.destroyAllWindows()

        self.get_logger().info(f"--- [STATE TRANSITION] {self.current_state.name} -> {new_state.name} ---")
        self.current_state = new_state

    def check_emergency(self, cmd: str) -> bool:
        if cmd == "PE":
            self.get_logger().error("!!! [EMERGENCY] Parada de Emergencia Triggered !!!")
            self.change_state(VisionState.EMERGENCIA)
            return True
        return False

    def com2vis_callback(self, msg: String) -> None:
        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from COM (/com2vis): '{cmd}' ---")

        if self.check_emergency(cmd):
            return

        # State Machine Logic for Communication Commands       
        if self.current_state == VisionState.ESPERANDO_ORDEN:
            if cmd == "head_up":
                self.move_head(0.0)  # <--- DESCOMENTADO
                self.change_state(VisionState.PREPARANDO_VISION)

        elif self.current_state == VisionState.PREPARANDO_VISION:
            if cmd.startswith("object_"):
                self.target_object = cmd.replace("object_", "")
                self.get_logger().info(f"--- [CONFIG] New target saved: {self.target_object} ---")
                self.change_state(VisionState.ESPERANDO_OBJETO)

        elif self.current_state == VisionState.VISION_DETENIDA:
            if cmd == "head_down":
                self.move_head(-0.5)   # <--- DESCOMENTADO
                self.change_state(VisionState.ESPERANDO_ORDEN)

    def nav2vis_callback(self, msg: String) -> None:
        cmd = msg.data
        self.get_logger().info(f"--- [IN] Received from NAV (/nav2vis): '{cmd}' ---")

        if self.check_emergency(cmd):
            return

        if self.current_state == VisionState.ESPERANDO_OBJETO:
            if cmd == "start_vis":
                self.change_state(VisionState.BUSQUEDA_ACTIVA)
                self.move_head(-0.2)
                #self.trigger_mock_detection()

        elif self.current_state == VisionState.BUSQUEDA_ACTIVA:
            if cmd == "stop_vis":
                self.change_state(VisionState.VISION_DETENIDA)
                self.move_head(0.0)


    def camera_callback(self, msg: Image) -> None:

        if self.current_state != VisionState.BUSQUEDA_ACTIVA:
            return

#1. Convertir el mensaje de ROS a una imagen de OpenCV
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Error convirtiendo la imagen: {e}")
            return

        # 2. Mostrar la imagen en una ventana
        cv2.imshow("Lo que ve TIAGo", cv_image)
        cv2.waitKey(1) # Necesario para que OpenCV actualice la ventana


# 3. Run YOLO v11 Inference
        results = self.model.predict(cv_image, conf=self.conf_thresh, verbose=False)

        # 4. Visualization: Plot results and show window
        # .plot() returns a BGR numpy array with boxes and labels drawn
        annotated_frame = results[0].plot()
        cv2.imshow(self.window_name, annotated_frame)
        cv2.waitKey(1)

        # 5. Logic to detect target object in the results
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]

                if class_name == self.target_object:
                    self.get_logger().info(f"*** [DETECTION] Found: {class_name}! ***")
                    
                    # Notify other modules
                    out_msg = String()
                    out_msg.data = "object_detected"
                    self.pub_vis2com.publish(out_msg)
                    self.pub_vis2nav.publish(out_msg)
                    
                    self.get_logger().info("--- [OUT] Publishing 'object_detected' to COM/NAV ---")
                    
                    # Trigger state change (this will also close the window)
                    self.change_state(VisionState.VISION_DETENIDA)
                    return


    # def process_webcam(self) -> None:
    #     """Reads from local webcam, runs YOLO, and displays results if active."""
    #     # 1. Comprobaciones de seguridad
    #     if self.current_state != VisionState.BUSQUEDA_ACTIVA:
    #         return
    #     if self.cap is None or not self.cap.isOpened():
    #         return

    #     # 2. Leer el frame directamente del hardware (webcam)
    #     ret, cv_image = self.cap.read()
    #     if not ret:
    #         self.get_logger().warning("Fallo al leer frame de la webcam. Reintentando...")
    #         return

    #     # 3. Inferencia de YOLO (No necesitamos CvBridge porque OpenCV ya lee en BGR)
    #     results = self.model.predict(cv_image, conf=self.conf_thresh, verbose=False)

    #     # 4. Visualización
    #     annotated_frame = results[0].plot()
    #     cv2.imshow(self.window_name, annotated_frame)
    #     cv2.waitKey(1)

    #     # 5. Lógica de detección
    #     for result in results:
    #         for box in result.boxes:
    #             class_id = int(box.cls[0])
    #             class_name = self.model.names[class_id]

    #             if class_name == self.target_object:
    #                 self.get_logger().info(f"*** [DETECTION] Found: {class_name}! ***")
                    
    #                 out_msg = String()
    #                 out_msg.data = "object_detected"
    #                 self.pub_vis2com.publish(out_msg)
    #                 self.pub_vis2nav.publish(out_msg)
                    
    #                 self.get_logger().info("--- [OUT] Publishing 'object_detected' to COM/NAV ---")
                    
    #                 self.change_state(VisionState.VISION_DETENIDA)
    #                 return


    def move_head(self, tilt: float) -> None:
        """Sends a movement command to TIAGo's head via Action Server."""
        # 1. Esperamos a que Gazebo esté listo para recibir comandos
        if not self.head_action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warn("--- [WARN] Head controller (Gazebo) not found! ---")
            return

        # 2. Preparamos el mensaje de Meta (Goal)
        goal = FollowJointTrajectory.Goal()
        
        # 3. Definimos qué motores vamos a mover
        goal.trajectory.joint_names = ["head_1_joint", "head_2_joint"]
        
        # 4. Definimos a qué posición (en radianes) van a ir
        point = JointTrajectoryPoint()
        point.positions = [0.0, tilt] # 0.0 pan (centro), 'tilt' up/down
        
        # 5. Definimos el tiempo que debe tardar el movimiento (NUEVA IMPLEMENTACIÓN)
        point.time_from_start = Duration(sec=2, nanosec=0) 
        
        # Añadimos el punto a la trayectoria
        goal.trajectory.points = [point]

        # 6. Enviamos el comando de forma asíncrona
        self.get_logger().info(f"--- [ACTION] Sending head movement goal: {tilt} rad to Gazebo ---")
        self.head_action_client.send_goal_async(goal)

def main(args=None):
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