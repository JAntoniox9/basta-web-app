from app import socketio
from flask import request
from app.services.state_store import state_store
from app.utils.helpers import get_client_ip
import time

# Mapeos en memoria (esto debería moverse a Redis también eventualmente)
sid_to_room = {}
sid_to_name = {}
sid_to_player_id = {}
player_id_to_sid = {}
iniciando_partida = set()

# Rate limiting (en memoria local por ahora)
last_request_times = {} 

def check_rate_limit(sid, action, cooldown=1.0):
    """Verifica si el cliente está enviando solicitudes demasiado rápido"""
    if sid not in last_request_times:
        last_request_times[sid] = {}
    
    last_time = last_request_times[sid].get(action, 0)
    current_time = time.time()
    
    if current_time - last_time < cooldown:
        return False
        
    last_request_times[sid][action] = current_time
    return True

@socketio.on("connect")
def on_connect():
    ip = get_client_ip()
    print(f"✅ Nuevo cliente conectado desde IP: {ip}")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    codigo = sid_to_room.pop(sid, None)
    jugador = sid_to_name.pop(sid, None)
    
    ip = get_client_ip()
    if not codigo:
        print(f"❌ Cliente desconectado (IP: {ip})")
        return

    sala = state_store.get_sala(codigo)
    if not sala:
        print(f"❌ Cliente desconectado de sala inexistente {codigo} (IP: {ip})")
        return
        
    print(f"❌ {jugador} desconectado de sala {codigo} (IP: {ip})")
    
    # Marcar como desconectado si estaba jugando
    if jugador in sala.get("jugadores", []):
        if "jugadores_desconectados" not in sala:
            sala["jugadores_desconectados"] = []
        if jugador not in sala["jugadores_desconectados"]:
            sala["jugadores_desconectados"].append(jugador)
            state_store.save()
            
        # Notificar desconexión
        socketio.emit("player_disconnected", {"jugador": jugador}, room=codigo)

@socketio.on("join_room_event")
def handle_join(data):
    ip = get_client_ip()
    if not check_rate_limit(request.sid, "join_room", 2.0):
        print(f"⚠️ Rate limit exceeded for join_room from {ip} ({request.sid})")
        return

    codigo = data.get("codigo")
    jugador = data.get("jugador", "Invitado")
    
    # Validar nombre
    if not jugador or jugador in ["null", "undefined", "none"] or not str(jugador).strip():
        print(f"⚠️ Intento de unirse con nombre inválido: {jugador} desde IP: {ip}")
        return

    sid_to_room[request.sid] = codigo
    sid_to_name[request.sid] = jugador
    socketio.server.enter_room(request.sid, codigo)

    sala = state_store.get_sala(codigo)

    if sala:
        if jugador not in sala["jugadores"]:
            sala["jugadores"].append(jugador)
            if jugador not in sala["puntuaciones"]:
                sala["puntuaciones"][jugador] = 0
            state_store.save()
        
        # Quitar de lista de desconectados si estaba
        if "jugadores_desconectados" in sala and jugador in sala["jugadores_desconectados"]:
            sala["jugadores_desconectados"].remove(jugador)
            
        iniciando_partida.discard(jugador)

        print(f"🟢 Jugador {jugador} unido a sala {codigo} (IP: {ip})")

        # Enviar estado actual de la sala
        socketio.emit(
            "player_joined",
            {
                "jugadores": sala["jugadores"],
                "puntuaciones": sala.get("puntuaciones", {}),
                "jugadores_listos": sala.get("jugadores_listos", []),
                "jugadores_desconectados": sala.get("jugadores_desconectados", []),
                "configuracion": {
                    "rondas": sala.get("rondas", 3),
                    "dificultad": sala.get("dificultad", "normal"),
                    "modo_juego": sala.get("modo_juego", "clasico"),
                    "chat_habilitado": sala.get("chat_habilitado", True),
                    "sonidos_habilitados": sala.get("sonidos_habilitados", True),
                    "powerups_habilitados": sala.get("powerups_habilitados", True),
                    "validacion_activa": sala.get("validacion_activa", True)
                }
            },
            room=codigo
        )

