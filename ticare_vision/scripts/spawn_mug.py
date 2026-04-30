#!/usr/bin/env python3

import argparse
import time

import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity


class MugSpawner(Node):
    """
    Spawns a more recognizable blue mug in Gazebo.
    The mug is represented with:
    - a large blue cylindrical body
    - a dark top opening
    - a visible side handle
    """

    def __init__(self):
        super().__init__("mug_spawner")
        self.client = self.create_client(SpawnEntity, "/spawn_entity")

        while not self.client.wait_for_service(timeout_sec=2.0):
            self.get_logger().info("Esperando al servicio de Gazebo /spawn_entity...")

    def spawn(self, x: float, y: float, z: float):
        sdf_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
          <model name="Mug">
            <static>true</static>

            <link name="mug_link">

              <!-- CUERPO PRINCIPAL AZUL -->
              <visual name="blue_body_visual">
                <pose>0 0 0.09 0 0 0</pose>
                <geometry>
                  <cylinder>
                    <radius>0.085</radius>
                    <length>0.16</length>
                  </cylinder>
                </geometry>
                <material>
                  <ambient>0.0 0.05 1.0 1.0</ambient>
                  <diffuse>0.0 0.10 1.0 1.0</diffuse>
                  <specular>0.2 0.2 0.8 1.0</specular>
                </material>
              </visual>

              <collision name="body_collision">
                <pose>0 0 0.09 0 0 0</pose>
                <geometry>
                  <cylinder>
                    <radius>0.085</radius>
                    <length>0.16</length>
                  </cylinder>
                </geometry>
              </collision>

              <!-- APERTURA SUPERIOR OSCURA PARA QUE PAREZCA TAZA -->
              <visual name="dark_top_visual">
                <pose>0 0 0.172 0 0 0</pose>
                <geometry>
                  <cylinder>
                    <radius>0.072</radius>
                    <length>0.006</length>
                  </cylinder>
                </geometry>
                <material>
                  <ambient>0.02 0.02 0.02 1.0</ambient>
                  <diffuse>0.02 0.02 0.02 1.0</diffuse>
                </material>
              </visual>

              <!-- BORDE SUPERIOR CLARO -->
              <visual name="rim_visual">
                <pose>0 0 0.178 0 0 0</pose>
                <geometry>
                  <cylinder>
                    <radius>0.09</radius>
                    <length>0.008</length>
                  </cylinder>
                </geometry>
                <material>
                  <ambient>0.8 0.85 1.0 1.0</ambient>
                  <diffuse>0.8 0.85 1.0 1.0</diffuse>
                </material>
              </visual>

              <!-- ASA DERECHA: pieza vertical -->
              <visual name="handle_vertical_visual">
                <pose>0 -0.125 0.09 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.035 0.115</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.05 1.0 1.0</ambient>
                  <diffuse>0.0 0.10 1.0 1.0</diffuse>
                </material>
              </visual>

              <collision name="handle_vertical_collision">
                <pose>0 -0.125 0.09 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.035 0.115</size>
                  </box>
                </geometry>
              </collision>

              <!-- ASA DERECHA: unión superior -->
              <visual name="handle_top_visual">
                <pose>0 -0.095 0.14 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.075 0.03</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.05 1.0 1.0</ambient>
                  <diffuse>0.0 0.10 1.0 1.0</diffuse>
                </material>
              </visual>

              <collision name="handle_top_collision">
                <pose>0 -0.095 0.14 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.075 0.03</size>
                  </box>
                </geometry>
              </collision>

              <!-- ASA DERECHA: unión inferior -->
              <visual name="handle_bottom_visual">
                <pose>0 -0.095 0.04 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.075 0.03</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.0 0.05 1.0 1.0</ambient>
                  <diffuse>0.0 0.10 1.0 1.0</diffuse>
                </material>
              </visual>

              <collision name="handle_bottom_collision">
                <pose>0 -0.095 0.04 0 0 0</pose>
                <geometry>
                  <box>
                    <size>0.035 0.075 0.03</size>
                  </box>
                </geometry>
              </collision>

            </link>
          </model>
        </sdf>
        """

        request = SpawnEntity.Request()
        request.name = f"Mug_{int(time.time())}"
        request.xml = sdf_xml
        request.initial_pose.position.x = x
        request.initial_pose.position.y = y
        request.initial_pose.position.z = z

        self.get_logger().info(
            f"Spawneando taza azul en Gazebo: x={x}, y={y}, z={z}"
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is None:
            self.get_logger().error("El servicio /spawn_entity no respondió.")
            return

        if future.result().success:
            self.get_logger().info("Taza azul insertada correctamente.")
        else:
            self.get_logger().error(
                f"Gazebo rechazó la petición: {future.result().status_message}"
            )


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=float, default=1.5)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--z", type=float, default=0.0)

    parsed_args = parser.parse_args()

    rclpy.init(args=args)
    node = MugSpawner()

    node.spawn(
        x=parsed_args.x,
        y=parsed_args.y,
        z=parsed_args.z
    )

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
