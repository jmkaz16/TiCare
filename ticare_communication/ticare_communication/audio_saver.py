import os
import time
import wave

import rclpy
from rclpy.node import Node

from audio_common_msgs.msg import AudioData

from ament_index_python.packages import get_package_share_directory


class AudioRecorder(Node):
    def __init__(self):
        super().__init__("audio_recorder")
        self.audio_buffer = []

        self.sub = self.create_subscription(AudioData, "/audio", self.audio_callback, 5)

        self.get_logger().info("Grabando... Habla ahora")

        package_share_path = get_package_share_directory("ticare_communication")

        self.data_dir = os.path.join(package_share_path, "data")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def audio_callback(self, msg):
        self.audio_buffer.append(bytes(msg.data))

    def save_file(self):
        if not self.audio_buffer:
            self.get_logger().error("No se recibió audio. ¿Está corriendo el audio_capture_node?")
            return

        # Guarda mp3
        # file_path = os.path.expanduser("~/com_ws/src/ticare_audio_recorder/data/audio1.mp3")
        # with open(file_path, "wb") as f:
        #     f.write(b"".join(self.audio_buffer))
        # self.get_logger().info(f"Guardado como MP3 en: {file_path}")

        # ros2 run ticare_audio_recorder save_audio

        # por su lado se runea el comando: ros2 run audio_capture audio_capture_node

        # Guarda wav
        file_path = os.path.join(self.data_dir, "audio.wav")

        with wave.open(
            file_path, "wb"
        ) as wf:  # la info de a continuación hace referencia a lo que sale cuando haces ros2 topic echo /audio_info
            wf.setnchannels(1)  # channels: 1
            wf.setsampwidth(2)  # sample_format: S16LE, S16 significa 16 bits
            wf.setframerate(16000)  # sample_rate: 16000
            wf.writeframes(b"".join(self.audio_buffer))

        self.get_logger().info(f"Guardado como WAV en: {file_path}")

        # por su lado se runea el comando: ros2 run audio_capture audio_capture_node --ros-args -p format:="wave"


def main(args=None):
    rclpy.init(args=args)
    node = AudioRecorder()

    start_time = time.time()
    while rclpy.ok() and (time.time() - start_time) < 5.0:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.save_file()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
