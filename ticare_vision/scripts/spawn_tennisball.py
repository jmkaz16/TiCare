#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
import time

class TennisBallSpawner(Node):
    """
    Utility script to spawn a simulated tennis ball in Gazebo.
    Uses dynamic naming to avoid Gazebo spawn collisions.
    """

    def __init__(self):
        super().__init__("tennis_ball_spawner")
        self.client = self.create_client(SpawnEntity, "/spawn_entity")
        
        while not self.client.wait_for_service(timeout_sec=2.0):
            self.get_logger().info("Esperando al servicio de Gazebo /spawn_entity...")

        self.request = SpawnEntity.Request()

    def spawn(self, x: float, y: float, z: float):
        # SDF para una pelota de tenis (Esfera de 3.3 cm de radio, color verde claro)
        sdf_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
          <model name="tennisball">
            <static>false</static>
            <link name="link">
              
              <!-- Física y colisiones -->
              <collision name="collision">
                <geometry>
                  <sphere><radius>0.033</radius></sphere>
                </geometry>
                <!-- Opcional: hacer que rebote un poco -->
                <surface>
                  <bounce>
                    <restitution_coefficient>0.7</restitution_coefficient>
                    <threshold>0.01</threshold>
                  </bounce>
                  <contact>
                    <ode><max_vel>10</max_vel></ode>
                  </contact>
                </surface>
              </collision>
              
              <!-- Apariencia visual -->
              <visual name="visual">
                <geometry>
                  <sphere><radius>0.033</radius></sphere>
                </geometry>
                <material>
                  <!-- Valores RGBA: Red, Green, Blue, Alpha (Transparencia) -->
                  <!-- Verde claro / Amarillo verdoso típico de las pelotas de tenis -->
                  <ambient>0.7 1.0 0.1 1.0</ambient>
                  <diffuse>0.7 1.0 0.1 1.0</diffuse>
                </material>
              </visual>
              
            </link>
          </model>
        </sdf>
        """
        
        # Generamos un nombre único basado en la hora actual
        unique_name = f"tennisball_{int(time.time())}"
        
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
                self.get_logger().info("¡Pelota de tenis insertada con éxito!")
            else:
                self.get_logger().error(f"Gazebo rechazó la petición: {future.result().status_message}")
        else:
            self.get_logger().error("El servicio de Gazebo falló por completo.")

def main(args=None):
    rclpy.init(args=args)
    spawner = TennisBallSpawner()
    
    # Coordenadas por defecto (a 1 metro delante del robot, ligeramente elevada para que caiga)
    spawner.spawn(x=2.5, y=0.0, z=1.0)
    
    spawner.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()