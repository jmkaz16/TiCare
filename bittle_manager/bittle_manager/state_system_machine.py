import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class BittleStateMachine(Node):
    def __init__(self):
        super().__init__('bittle_state_machine')
        
        # Suscriptor: Escucha en 'bittle_raw'
        self.subscription = self.create_subscription(
            String,
            'bittle_raw',
            self.command_callback,
            10)
        
        # Publicador: Publica en 'bittle_cmd'
        self.publisher_ = self.create_publisher(String, 'bittle_cmd', 10)
        
        # Temporizador: Dicta el ritmo de ejecución de las órdenes compuestas
        timer_period = 2.0  # 2 segundos entre acción y acción
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        
        # Cola de comandos: Almacena la secuencia de acciones a realizar
        self.command_queue = []
        
        # Estado Inicial
        self.current_state = "rest" 
        
        # Clasificación de comandos
        self.postures = [
            "sit", "up", "rest", "dropped", "pd", 
            "tbl", "zz", "buttUp", "lifted", "str", "calib"
        ]
        self.movements_and_actions = [
            "bk", "bkL", "bkR", "jpF", "phF", "phL", "phR", 
            "trF", "trL", "trR", "wkF", "mw", "jmp",
            "bx", "chr", "dg", "fiv", "hds", "hg", "hi", "hu",
            "kc", "pee", "pu", "scrh", "snf", "wh", "angry"
        ]
        self.turns = ["wkL", "wkR"] 

        self.get_logger().info("Máquina de Estados iniciada. Lista para secuencias compuestas.")
        self.get_logger().info(f"Estado inicial: {self.current_state}")

    def command_callback(self, msg):
        # 1. DIVIDIR MENSAJE: Si llegan varias órdenes (ej: "up\nbx"), las separamos en una lista.
        incoming_commands = msg.data.strip().split('\n')
        
        if not incoming_commands or incoming_commands == ['']:
            return

        self.get_logger().info(f"Bloque de órdenes recibido: {incoming_commands}")

        # 2. PROCESAR CADA ORDEN INDIVIDUALMENTE
        for raw_action in incoming_commands:
            requested_action = raw_action.strip()
            if not requested_action:
                continue

            # Simulamos el estado futuro basándonos en lo que ya hay esperando en la cola
            simulated_state = self.current_state
            if self.command_queue:
                last_queued = self.command_queue[-1]
                if last_queued in self.postures:
                    simulated_state = last_queued
                else:
                    simulated_state = "up"

            # Regla 1: Ignorar posturas redundantes
            if requested_action in self.postures and requested_action == simulated_state:
                self.get_logger().info(f"Postura '{requested_action}' redundante. Ignorando en la secuencia.")
                continue

            # Regla 2: Resolver conflictos (Añadir transición "up")
            if requested_action in self.movements_and_actions or requested_action in self.turns:
                if simulated_state != "up":
                    self.get_logger().info(f"Añadiendo transición 'up' antes de '{requested_action}'...")
                    self.command_queue.append("up")
                    simulated_state = "up"

            # Añadir la orden validada a la cola
            self.command_queue.append(requested_action)
            self.get_logger().info(f"Orden '{requested_action}' encolada.")

            # Regla 3: Control de giros (Detener giro a los 90º)
            if requested_action in self.turns:
                self.get_logger().info(f"Giro detectado. Añadiendo 'up' a la cola para detenerlo.")
                self.command_queue.append("up")

    def timer_callback(self):
        # El temporizador saca de la cola una acción cada 2 segundos de forma secuencial
        if self.command_queue:
            action_to_publish = self.command_queue.pop(0)
            
            msg = String()
            msg.data = action_to_publish
            self.publisher_.publish(msg)
            
            # Actualizamos el estado real de la máquina
            if action_to_publish in self.postures:
                self.current_state = action_to_publish
            else:
                self.current_state = "up"
                
            self.get_logger().info(f'[{self.i}] Ejecutando secuencia: "{action_to_publish}" | Quedan en cola: {len(self.command_queue)}')
            self.i += 1

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