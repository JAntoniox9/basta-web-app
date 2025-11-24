import sys
import os

# ⚙️ Cargar variables de entorno desde .env ANTES de importar otros módulos
from dotenv import load_dotenv
load_dotenv()  # Esto carga el archivo .env

# Importar módulos necesarios
from app import create_app, socketio
from app.utils.logger import setup_logging

# Configurar logging primero
setup_logging()

# Crear la aplicación
flask_application = create_app()

if __name__ == "__main__":
    print("🚀 Servidor Flask-SocketIO modularizado ejecutándose...")
    socketio.run(flask_application, host="0.0.0.0", port=8081, use_reloader=False, allow_unsafe_werkzeug=True)

