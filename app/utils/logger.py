import sys
import collections
from datetime import datetime, timezone

# Buffer para almacenar logs en memoria
# Usamos una variable global aquí que será importada por la app
server_logs = collections.deque(maxlen=2000)

class DualLogger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log_buffer = server_logs
        self._partial = ""
        self._sequence = 0
        
    def write(self, message):
        # Escribir en terminal original
        self.terminal.write(message)

        # Acumular fragmentos hasta tener líneas completas
        message = self._partial + message
        lines = message.split('\n')
        self._partial = lines[-1] if message and not message.endswith('\n') else ""
        complete_lines = lines[:-1] if self._partial else lines

        if complete_lines:
            timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            for line in complete_lines:
                if line.strip():
                    self._sequence += 1
                    self.log_buffer.append({
                        "time": timestamp,
                        "msg": line.strip(),
                        "seq": self._sequence,
                    })

    def flush(self):
        self.terminal.flush()
        if self._partial.strip():
            timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            self._sequence += 1
            self.log_buffer.append({
                "time": timestamp,
                "msg": self._partial.strip(),
                "seq": self._sequence,
            })
            self._partial = ""

def setup_logging():
    """Configura el logger dual para capturar stdout"""
    if not isinstance(sys.stdout, DualLogger):
        sys.stdout = DualLogger()

