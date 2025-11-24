import sys
import collections
from datetime import datetime

# Buffer para almacenar logs en memoria
# Usamos una variable global aquí que será importada por la app
server_logs = collections.deque(maxlen=500)

class DualLogger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log_buffer = server_logs
        
    def write(self, message):
        # Escribir en terminal original
        self.terminal.write(message)
        
        # Guardar en buffer si no es solo salto de línea
        if message.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Si el mensaje tiene varias líneas, procesarlas individualmente
            for line in message.split('\n'):
                if line.strip():
                    self.log_buffer.append({
                        "time": timestamp, 
                        "msg": line.strip()
                    })
                
    def flush(self):
        self.terminal.flush()

def setup_logging():
    """Configura el logger dual para capturar stdout"""
    if not isinstance(sys.stdout, DualLogger):
        sys.stdout = DualLogger()

