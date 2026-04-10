#!/usr/bin/env python3

import os
from time import time
from ament_index_python.packages import get_package_share_directory


import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class CommunicationPublisher(Node):

    def __init__(self):
        super().__init__("communication_publisher")
        self.publisher_ = self.create_publisher(String, "bittle_cmd", 10)
        timer_period = 2  # segundos
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

        # Obtener la ruta del paquete y ruta de los archivos
        package_share_path = get_package_share_directory("bittle_communication")
        self.data_dir = os.path.abspath(
            os.path.join(
                package_share_path,
                "..",
                "..",
                "..",
                "..",
                "src",
                "bittle_communication",
                "bittle_communication",
                "state",
            )
        )
        self.file_path = os.path.join(self.data_dir, "order.txt")
        self.lock_path = os.path.join(self.data_dir, "order.lock")

    def timer_callback(self):
        msg = String()
        msg.data = self.read_from_file()
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1

    def read_from_file(self):
        # Comprobar si el archivo existe
        if not os.path.exists(self.file_path):
            return ""

        try:
            # Comprobar si el semáforo existe y esperar a que desaparezca
            while os.path.exists(self.lock_path):
                time.sleep(0.1)

            # Crear el semáforo
            open(self.lock_path, "w").close()

            # Leer el contenido del archivo
            with open(self.file_path, "r") as f:
                content = f.read().strip()

            # Elminar el archivo
            os.remove(self.file_path)

            return content

        except Exception as e:
            self.get_logger().error(f"Error processing {self.file_path}: {e}")
            return ""

        finally:
            # Eliminar el semáforo
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)


def main(args=None):
    rclpy.init()

    communication_publisher = CommunicationPublisher()

    try:
        rclpy.spin(communication_publisher)
        # communication_publisher.timer_callback() # Llamar manualmente a la función para publicar inmediatamente al iniciar

    except KeyboardInterrupt:
        pass

    finally:
        if rclpy.ok():
            communication_publisher.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
