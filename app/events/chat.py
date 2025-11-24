from app import socketio
from flask import request
from app.services.state_store import state_store
from app.services.db_store import db_store
from app.utils.helpers import get_client_ip
import re
import time

# Simple rate limiting para chat
last_chat_times = {}

# Palabras ofensivas básicas (se puede ampliar o mover a config)
PALABRAS_PROHIBIDAS = {
    "puta", "mierda", "pendejo", "idiota", "estupido", "imbecil",
    "cabrón", "cabron", "culero", "chingada", "fuck", "bitch"
}


def _contiene_palabras_prohibidas(texto: str) -> bool:
    normalizado = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]", "", texto).lower()
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in normalizado:
            return True
    return False

def check_chat_rate_limit(sid):
    current_time = time.time()
    last_time = last_chat_times.get(sid, 0)
    if current_time - last_time < 0.5: # Max 2 mensajes por segundo
        return False
    last_chat_times[sid] = current_time
    return True

@socketio.on("enviar_mensaje_chat")
def handle_chat_message(data):
    if not check_chat_rate_limit(request.sid):
        return

    codigo = data.get("codigo")
    jugador = data.get("jugador")
    mensaje = data.get("mensaje", "").strip()
    
    if not jugador or not mensaje:
        return
    
    # Usar db_store como fuente principal para soportar despliegues con base de datos
    sala = db_store.get_sala(codigo) or state_store.get_sala(codigo)
    if not sala or not sala.get("chat_habilitado", True):
        return

    # Filtrar palabras prohibidas
    if _contiene_palabras_prohibidas(mensaje):
        socketio.emit(
            "mensaje_rechazado",
            {"razon": "Mensaje bloqueado por lenguaje inapropiado"},
            room=request.sid,
        )
        # Notificar en el chat como mensaje del sistema para dar contexto al resto
        socketio.emit(
            "nuevo_mensaje_chat",
            {
                "jugador": "Moderador",
                "mensaje": f"El mensaje de {jugador} fue bloqueado por lenguaje inapropiado",
                "timestamp": time.time() * 1000,
                "tipo": "sistema_moderacion",
            },
            room=codigo,
        )
        return

    # Validar que el mensaje comience con la letra actual de la ronda
    letra_ronda = (sala.get("letra") or "").strip().upper()
    if letra_ronda and mensaje:
        primera_letra = mensaje[0].upper()
        if primera_letra != letra_ronda:
            socketio.emit(
                "mensaje_rechazado",
                {"razon": f"El mensaje debe iniciar con la letra {letra_ronda}"},
                room=request.sid,
            )
            return
    
    timestamp = time.time() * 1000 # JS timestamp
    msg_obj = {
        "jugador": jugador,
        "mensaje": mensaje,
        "timestamp": timestamp
    }
    
    if "mensajes_chat" not in sala:
        sala["mensajes_chat"] = []

    sala["mensajes_chat"].append(msg_obj)
    
    # Mantener historial limitado
    if len(sala["mensajes_chat"]) > 50:
        sala["mensajes_chat"] = sala["mensajes_chat"][-50:]
        
    # Persistir tanto en la DB (si está habilitada) como en el fallback JSON
    try:
        db_store.set_sala(codigo, sala)
        # Mantener sincronizado el cache local para otros eventos en tiempo real
        state_store.set_sala(codigo, sala)
    except Exception:
        # Si falla el guardado en DB, al menos persistimos en disco
        state_store.set_sala(codigo, sala)
        state_store.save()
    
    socketio.emit("nuevo_mensaje_chat", msg_obj, room=codigo)
    
    # Log para admin
    print(f"💬 [CHAT] {jugador} en {codigo}: {mensaje}")

