from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.services.db_store import db_store
import random
import string

game_bp = Blueprint('game', __name__)

# Constantes (mover a config.py despues)
CATEGORIAS_DISPONIBLES = {
    "Nombre": {"icon": "👤", "examples": ["Ana", "Beto", "Carlos"]},
    "Apellido": {"icon": "family", "examples": ["Alvarez", "Benitez", "Castro"]},
    "Ciudad/País": {"icon": "🌍", "examples": ["Argentina", "Brasil", "Chile"]},
    "Animal": {"icon": "🐾", "examples": ["Ardilla", "Ballena", "Caballo"]},
    "Fruta/Verdura": {"icon": "🍎", "examples": ["Ananá", "Banana", "Cereza"]},
    "Color": {"icon": "🎨", "examples": ["Amarillo", "Blanco", "Celeste"]},
    "Cosa": {"icon": "📦", "examples": ["Almohada", "Botella", "Cama"]},
    "Marca": {"icon": "🏷️", "examples": ["Adidas", "Bic", "Canon"]},
    "Comida": {"icon": "🍔", "examples": ["Asado", "Bife", "Canelones"]},
    "Profesión": {"icon": "💼", "examples": ["Abogado", "Bombero", "Carpintero"]},
    "Famoso": {"icon": "⭐", "examples": ["Messi", "Shakira", "Brad Pitt"]},
    "Película/Serie": {"icon": "🎬", "examples": ["Avatar", "Batman", "Cars"]},
}

@game_bp.route("/")
def index():
    return render_template("index.html")

@game_bp.route("/crear_sala")
def crear_sala_page():
    return render_template("crear_sala.html")

@game_bp.route("/unirse_sala")
def unirse_sala_page():
    return render_template("unirse_sala.html")

@game_bp.route("/create", methods=["POST"])
def create_room():
    data = request.json
    # El frontend envía los datos directamente, no dentro de un objeto "config"
    nombre_anfitrion = data.get("nombre")
    
    if not nombre_anfitrion:
        return jsonify({"ok": False, "error": "Nombre requerido"}), 400

    # Generar código único
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not db_store.get_sala(codigo):
            break
    
    sala = db_store.create_sala(codigo, nombre_anfitrion)
    
    # Guardar configuración (los datos vienen directamente en data, no en data.config)
    sala["rondas"] = int(data.get("rondas", 5))
    sala["dificultad"] = data.get("dificultad", "normal")
    sala["modo_juego"] = data.get("modo_juego", "clasico")
    sala["categorias"] = data.get("categorias", list(CATEGORIAS_DISPONIBLES.keys())[:6])
    
    # Opciones adicionales
    sala["chat_habilitado"] = data.get("chat_habilitado", True)
    sala["sonidos_habilitados"] = data.get("sonidos_habilitados", True)
    sala["powerups_habilitados"] = data.get("powerups_habilitados", True)
    sala["validacion_activa"] = data.get("validacion_activa", True)
    
    # Guardar cambios en la base de datos
    db_store.set_sala(codigo, sala)
    
    print(f"✅ Sala creada: {codigo} por {nombre_anfitrion} (Modo: {sala['modo_juego']})")
    return jsonify({"ok": True, "codigo": codigo})

@game_bp.route("/join", methods=["POST"])
def join_room_http():
    data = request.json
    codigo = data.get("codigo")
    nombre = data.get("nombre")
    
    if not codigo or not nombre:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400
        
    sala = db_store.get_sala(codigo)
    if not sala:
        return jsonify({"ok": False, "error": "Sala no encontrada"}), 404
        
    if nombre in sala["jugadores"]:
        # Permitir reconexión (logica simplificada)
        return jsonify({"ok": True, "codigo": codigo})
        
    if sala.get("en_curso", False):
        return jsonify({"ok": False, "error": "Partida en curso"}), 400
        
    if len(sala["jugadores"]) >= 20:
         return jsonify({"ok": False, "error": "Sala llena"}), 400
         
    sala["jugadores"].append(nombre)
    sala["puntuaciones"][nombre] = 0
    db_store.set_sala(codigo, sala)
    
    print(f"👥 Jugador {nombre} se unió a sala {codigo}")
    return jsonify({"ok": True, "codigo": codigo})

@game_bp.route("/waiting/<codigo>")
def waiting_room(codigo):
    sala = db_store.get_sala(codigo)
    if not sala:
        return "❌ Sala no encontrada", 404
        
    if sala.get("finalizada", False):
        return render_template("partida_finalizada.html", codigo=codigo)
        
    return render_template(
        "waiting.html",
        jugadores=sala.get("jugadores", []),
        anfitrion=sala["anfitrion"],
        codigo=codigo,
        puntuaciones=sala.get("puntuaciones", {}),
        fin_del_juego=sala.get("ronda_actual", 1) > sala.get("rondas", 1),
        jugadores_listos=sala.get("jugadores_listos", []),
        jugadores_desconectados=sala.get("jugadores_desconectados", [])
    )

@game_bp.route("/game/<codigo>")
def game(codigo):
    sala = db_store.get_sala(codigo)
    if not sala:
        return "Sala no encontrada", 404
        
    # Lógica de recuperación de partida finalizada
    finalizada = sala.get("finalizada", False)
    last_results = sala.get("last_results", None)
    
    if finalizada and not last_results:
        return render_template("partida_finalizada.html", codigo=codigo)
        
    categorias = sala.get("categorias", list(CATEGORIAS_DISPONIBLES.keys())[:6])
    categorias_con_iconos = []
    for cat in categorias:
        icon = CATEGORIAS_DISPONIBLES.get(cat, {}).get("icon", "📝")
        categorias_con_iconos.append({"nombre": cat, "icon": icon})

    return render_template("game.html",
        jugador=sala["anfitrion"], # Esto es incorrecto, deberia ser sesion
        codigo=codigo,
        ronda=sala.get("ronda_actual", 1),
        total_rondas=sala.get("rondas", 1),
        letra=sala.get("letra", "?"),
        categorias=categorias_con_iconos,
        powerups_habilitados=sala.get("powerups_habilitados", True),
        chat_habilitado=sala.get("chat_habilitado", True),
        validacion_activa=sala.get("validacion_activa", False),
        finalizada=finalizada,
        last_results=last_results
    )

