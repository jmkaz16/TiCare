import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class BittleStateMachine(Node):
    def __init__(self):
        super().__init__('bittle_state_machine')
        
        # 1. Suscriptor: Escucha las órdenes ya procesadas por el sistema de voz
        self.subscription = self.create_subscription(
            String,
            'bittle_cmd',
            self.command_callback,
            10)
        
        # 2. Publicador: Envía las órdenes validadas al nodo de actuación de Bittle
        self.publisher_ = self.create_publisher(String, 'bittle_final_cmd', 10)
        
        # 3. Estado Inicial: Asumimos que Bittle se enciende de pie ("up")
        self.current_state = "up" 
        
        # 4. Clasificación de comandos para facilitar la lógica
        self.postures = [
            "sit", "up", "rest", "dropped", "pd", 
            "tbl", "zz", "buttUp", "lifted", "str", "calib"
        ]
        self.movements_and_actions = [
            "bk", "bkL", "bkR", "jpF", "phF", "phL", "phR", 
            "trF", "trL", "trR", "wkF", "wkL", "wkR", "mw", "jmp", # Movimientos
            "bx", "chr", "dg", "fiv", "hds", "hg", "hi", "hu",     # Acciones
            "kc", "pee", "pu", "scrh", "snf", "wh", "angry"
        ]

        self.get_logger().info("Bittle State Machine iniciada correctamente.")
        self.get_logger().info(f"Estado inicial de Bittle: {self.current_state}")

    def command_callback(self, msg):
        requested_action = msg.data.strip()
        
        if not requested_action:
            return

        self.get_logger().info(f"==> Orden recibida: '{requested_action}' | Estado actual: '{self.current_state}'")

        # Regla 1: Si piden una postura en la que YA estamos, lo ignoramos para ahorrar batería/tiempo
        if requested_action in self.postures and requested_action == self.current_state:
            self.get_logger().info("Bittle ya está en esa postura. Ignorando orden.")
            return

        # Regla 2: RESOLUCIÓN DE CONFLICTOS
        # Si piden un movimiento o acción, Bittle DEBE estar de pie ("up")
        if requested_action in self.movements_and_actions:
            if self.current_state != "up":
                self.get_logger().warn(f"Conflicto: Bittle está '{self.current_state}'. Levantando primero...")
                self.send_command("up")
                
                # Pausa para dar tiempo físico a que los motores levanten al perro
                # (Ajusta este tiempo según lo que tarde Bittle en la vida real)
                time.sleep(1.5) 
                
                self.current_state = "up"
                self.get_logger().info("Bittle ya está de pie. Procediendo con la orden...")

        # Regla 3: Si estaba durmiendo ("zz") o "muerto" ("pd") y le piden sentarse, 
        # a veces físicamente necesitan pasar por "up" primero (opcional, actívalo si es el caso)
        if requested_action == "sit" and self.current_state in ["zz", "pd", "tbl", "dropped"]:
             self.get_logger().warn("Postura compleja detectada. Levantando antes de sentar...")
             self.send_command("up")
             time.sleep(1.5)
             self.current_state = "up"

        # 5. Ejecutar la orden final solicitada
        self.send_command(requested_action)
        
        # 6. Actualizar el estado interno
        self.update_state(requested_action)

    def send_command(self, action):
        """Envia el comando al nodo actuador"""
        msg = String()
        msg.data = action
        self.publisher_.publish(msg)
        self.get_logger().info(f"Publicado en bittle_final_cmd: {action}")

    def update_state(self, action):
        """Actualiza la memoria del estado de Bittle"""
        if action in self.postures:
            # Si es una postura fija, el perro se queda así
            self.current_state = action
        else:
            # Si es un movimiento (caminar) o acción (saludar), 
            # al terminar el perro vuelve a su estado base de pie.
            self.current_state = "up"

def main(args=None):
    rclpy.init(args=args)
    node = BittleStateMachine()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()