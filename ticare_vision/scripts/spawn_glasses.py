#!/usr/bin/env python3

import argparse
import time

import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity


class GlassesSpawner(Node):
    """
    Spawns oversized glasses in Gazebo for YOLO vision testing.
    The glasses are static and placed facing the robot camera.
    """

    def __init__(self):
        super().__init__("glasses_spawner")
        self.client = self.create_client(SpawnEntity, "/spawn_entity")

        while not self.client.wait_for_service(timeout_sec=2.0):
            self.get_logger().info("Esperando al servicio de Gazebo /spawn_entity...")

    def spawn(self, x: float, y: float, z: float):
        sdf_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
          <model name="glasses">
            <static>true</static>

            <link name="glasses_link">

              <!-- LENTE IZQUIERDA AZUL -->
              <visual name="left_lens_visual">
                <pose>0 0.13 0 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.012 0.17 0.105</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.65 1.0 0.75</ambient>
                  <diffuse>0.0 0.65 1.0 0.75</diffuse>
                  <specular>0.4 0.8 1.0 1.0</specular>
                </material>
              </visual>

              <!-- LENTE DERECHA AZUL -->
              <visual name="right_lens_visual">
                <pose>0 -0.13 0 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.012 0.17 0.105</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.65 1.0 0.75</ambient>
                  <diffuse>0.0 0.65 1.0 0.75</diffuse>
                  <specular>0.4 0.8 1.0 1.0</specular>
                </material>
              </visual>

              <!-- MARCO SUPERIOR IZQUIERDO -->
              <visual name="left_top_frame_visual">
                <pose>0 0.13 0.065 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.20 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- MARCO INFERIOR IZQUIERDO -->
              <visual name="left_bottom_frame_visual">
                <pose>0 0.13 -0.065 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.20 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- MARCO SUPERIOR DERECHO -->
              <visual name="right_top_frame_visual">
                <pose>0 -0.13 0.065 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.20 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- MARCO INFERIOR DERECHO -->
              <visual name="right_bottom_frame_visual">
                <pose>0 -0.13 -0.065 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.20 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- MARCO LATERAL EXTERIOR IZQUIERDO -->
              <visual name="left_outer_frame_visual">
                <pose>0 0.225 0 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.025 0.15</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- MARCO LATERAL EXTERIOR DERECHO -->
              <visual name="right_outer_frame_visual">
                <pose>0 -0.225 0 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.025 0.025 0.15</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- PUENTE CENTRAL -->
              <visual name="bridge_visual">
                <pose>0 0 0.025 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.03 0.085 0.03</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- PATILLA IZQUIERDA -->
              <visual name="left_temple_visual">
                <pose>-0.16 0.255 0.025 0 0.35 0</pose>
                <geometry>
                  <box>
                    <size>0.32 0.025 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- PATILLA DERECHA -->
              <visual name="right_temple_visual">
                <pose>-0.16 -0.255 0.025 0 0.35 0</pose>
                <geometry>
                  <box>
                    <size>0.32 0.025 0.025</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.0 0.0 1.0</ambient>
                  <diffuse>0.0 0.0 0.0 1.0</diffuse>
                </material>
              </visual>

              <!-- COLISIÓN SIMPLE GLOBAL -->
              <collision name="glasses_collision">
                <pose>0 0 0 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.35 0.52 0.18</size>
                  </box>
                </geometry>
              </collision>

            </link>
          </model>
        </sdf>
        """

        request = SpawnEntity.Request()
        request.name = f"glasses_{int(time.time())}"
        request.xml = sdf_xml
        request.initial_pose.position.x = x
        request.initial_pose.position.y = y
        request.initial_pose.position.z = z

        self.get_logger().info(
            f"Spawneando gafas en Gazebo: x={x}, y={y}, z={z}"
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is None:
            self.get_logger().error("El servicio /spawn_entity no respondió.")
            return

        if future.result().success:
            self.get_logger().info("Gafas insertadas correctamente.")
        else:
            self.get_logger().error(
                f"Gazebo rechazó la petición: {future.result().status_message}"
            )


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=float, default=1.5)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--z", type=float, default=1.0)

    parsed_args = parser.parse_args()

    rclpy.init(args=args)
    node = GlassesSpawner()

    node.spawn(
        x=parsed_args.x,
        y=parsed_args.y,
        z=parsed_args.z
    )

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

