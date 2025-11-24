import os
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    flask_app = Flask(__name__, template_folder='../templates', static_folder='../static')
    flask_app.secret_key = os.getenv("SECRET_KEY", "basta_secret_2025")
    
    # Configuración de SocketIO
    # En producción con Gunicorn, usar eventlet es más eficiente
    # En desarrollo, threading funciona bien
    async_mode = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")
    socketio.init_app(
        flask_app, 
        cors_allowed_origins="*", 
        async_mode=async_mode,
        logger=True,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=1e6
    )
    
    # Registrar blueprints
    from app.routes.admin import admin_bp
    from app.routes.game import game_bp
    
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(game_bp)
    
    # Registrar eventos de SocketIO
    # Nota: Importamos los módulos para que se registren los decoradores @socketio.on
    # pero no necesitamos hacer nada más con ellos
    import app.events.game
    import app.events.chat
    
    return flask_app
