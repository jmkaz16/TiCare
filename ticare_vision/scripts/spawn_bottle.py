#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
import time  # <--- IMPORTACIÓN AÑADIDA

class BottleSpawner(Node):
    """
    Utility script to spawn a simulated plastic bottle in Gazebo.
    Uses dynamic naming to avoid Gazebo spawn collisions.
    """

    def __init__(self):
        super().__init__("bottle_spawner")
        self.client = self.create_client(SpawnEntity, "/spawn_entity")
        
        while not self.client.wait_for_service(timeout_sec=2.0):
            self.get_logger().info("Esperando al servicio de Gazebo /spawn_entity...")

        self.request = SpawnEntity.Request()

    def spawn(self, x: float, y: float, z: float):
        sdf_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
          <model name="bottle">
            <static>false</static>
            <link name="link">
              <collision name="collision">
                <geometry>
                  <cylinder><radius>0.04</radius><length>0.25</length></cylinder>
                </geometry>
              </collision>
              <visual name="visual">
                <geometry>
                  <cylinder><radius>0.04</radius><length>0.25</length></cylinder>
                </geometry>
                <material>
                  <ambient>0.0 0.5 1.0 0.5</ambient>
                  <diffuse>0.0 0.5 1.0 0.5</diffuse>
                </material>
              </visual>
            </link>
          </model>
        </sdf>
        """
        
        # SOLUCIÓN: Generamos un nombre único basado en la hora actual
        unique_name = f"test_bottle_{int(time.time())}"
        
        self.request.name = unique_name
        self.request.xml = sdf_xml
        self.request.initial_pose.position.x = x
        self.request.initial_pose.position.y = y
        self.request.initial_pose.position.z = z

        self.get_logger().info(f"Haciendo spawn de '{unique_name}' en x={x}, y={y}, z={z}...")
        
        future = self.client.call_async(self.request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            if future.result().success:
                self.get_logger().info("¡Botella insertada con éxito!")
            else:
                self.get_logger().error(f"Gazebo rechazó la petición: {future.result().status_message}")
        else:
            self.get_logger().error("El servicio de Gazebo falló por completo.")

def main(args=None):
    rclpy.init(args=args)
    spawner = BottleSpawner()
    
    # MODIFICA ESTAS VARIABLES TRANQUILAMENTE AHORA
    # x=1.0 está a 1 metro frente al robot.
    spawner.spawn(x=2.3, y=0.0, z=0.0)
    
    spawner.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()