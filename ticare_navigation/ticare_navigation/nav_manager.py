import rclpy
from rclpy.node import Node

from enum import Enum
from geometry_msgs.msg import PoseWithCovarianceStamped
from ticare_interfaces.srv import SavePose

class State(Enum):
    IDLE = 0
    WAITING_FOR_SEARCH = 1
    LOCALIZING = 2
    SAVING_START_POSE = 3
    NAVIGATING_TO_ZONE = 4
    EMERGENCY_STOP = 5

class NavManager(Node):
    def __init__(self):
        super().__init__('nav_manager')
        
        # 1. Parámetros 
        self.declare_parameter('covariance_threshold', 0.2)
        self.state = State.IDLE
        
        # 2. Suscriptores
        # Escucha la pose para monitorizar la localización 
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10)
            
        # 3. Clientes de Servicio
        self.save_pose_client = self.create_client(SavePose, 'save_pose')

    def pose_callback(self, msg):
        """Callback que monitoriza la precisión de la localización."""
        if self.state == State.LOCALIZING:
            # SR-4.004: Suma de covarianzas espaciales 
            cov_x = msg.pose.covariance[0]
            cov_y = msg.pose.covariance[7]
            
            if (cov_x + cov_y) < self.get_parameter('covariance_threshold').value:
                self.get_logger().info('Localización validada. Guardando punto de inicio...')
                self.state = State.SAVING_START_POSE
                self.call_save_pose_service()

    def call_save_pose_service(self):
        """Llamada asíncrona al servicio de registro (SR-4.005)."""
        while not self.save_pose_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando al servicio pose_recorder...')
            
        request = SavePose.Request()
        request.label = "punto_inicio"
        
        # Llamada asíncrona para no bloquear el nodo
        future = self.save_pose_client.call_async(request)
        future.add_done_callback(self.save_pose_callback)

    def save_pose_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info('Punto de inicio guardado con éxito.')
                self.state = State.NAVIGATING_TO_ZONE
                # Aquí llamarías a la acción de navegación UR-005 
        except Exception as e:
            self.get_logger().error(f'Error al llamar al servicio: {e}')

def main(args=None):
    rclpy.init(args=args)
    nav_manager = NavManager()
    rclpy.spin(nav_manager)
    nav_manager.destroy_node()
    rclpy.shutdown()