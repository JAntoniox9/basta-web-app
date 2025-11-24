import json
import threading
import time
import os

# Archivo de persistencia local (fallback si no hay Redis)
STATE_FILE = "checkpoint.json"

class StateStore:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateStore, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa el estado en memoria"""
        self.state = {
            "salas": {}
        }
        self.state_dirty = False
        self.save_lock = threading.Lock()
        
        # Cargar estado previo si existe
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    loaded_state = json.load(f)
                    self.state = loaded_state
                    print("📂 Estado previo cargado correctamente.")
            except Exception as e:
                print(f"⚠️ Error cargando estado previo: {e}")
                
        # Iniciar guardado en segundo plano
        threading.Thread(target=self._background_saver, daemon=True).start()

    def _background_saver(self):
        """Guarda el estado en disco periódicamente si ha cambiado"""
        while True:
            time.sleep(5)
            if self.state_dirty:
                with self.save_lock:
                    try:
                        with open(STATE_FILE, "w") as f:
                            json.dump(self.state, f, indent=4)
                        self.state_dirty = False
                    except Exception as e:
                        print(f"❌ Error saving state: {e}")

    def get_sala(self, codigo):
        return self.state["salas"].get(codigo)
    
    def set_sala(self, codigo, data):
        self.state["salas"][codigo] = data
        self.state_dirty = True
        
    def get_all_salas(self):
        return self.state["salas"]
    
    def create_sala(self, codigo, anfitrion):
        self.state["salas"][codigo] = {
            "anfitrion": anfitrion,
            "jugadores": [anfitrion],
            "jugadores_ids": {},  # Se llenará después
            "ids_jugadores": {},  # Se llenará después
            "en_curso": False,
            "ronda_actual": 1,
            "puntuaciones": {anfitrion: 0},
            "mensajes_chat": [],
            "configuracion": {}
        }
        self.state_dirty = True
        return self.state["salas"][codigo]
        
    def save(self):
        """Fuerza el guardado (marca como sucio)"""
        self.state_dirty = True

# Singleton global
state_store = StateStore()

