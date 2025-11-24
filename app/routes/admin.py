from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from app.utils.helpers import (
    require_admin_auth, get_client_ip, check_ip_blocked, 
    record_failed_attempt, reset_attempts, hash_password, 
    ADMIN_PASSWORD_HASH, generate_admin_token, ADMIN_SESSION_DURATION, 
    BLOCK_DURATION_MINUTES, verify_admin_token, VALID_ADMIN_TOKENS
)
from app.services.state_store import state_store
from app.utils.logger import server_logs
import hmac
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin")
def admin_panel():
    """Panel de administración - requiere autenticación"""
    token = request.cookies.get("admin_token")
    if not token or not verify_admin_token(token):
        # Si no hay token o no es válido, redirigir a la página de login
        return redirect(url_for('admin.admin_login_page'))
    return render_template("admin_dashboard.html")

@admin_bp.route("/admin/login")
def admin_login_page():
    return render_template("admin_login.html")

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """Autenticar como administrador con seguridad mejorada"""
    client_ip = get_client_ip()
    
    # Verificar si la IP está bloqueada
    if check_ip_blocked(client_ip):
        # Calcular tiempo restante de manera segura
        # Nota: Esto requeriría acceso al diccionario admin_login_attempts de helpers.py
        # Por simplicidad en este paso devolvemos mensaje genérico o importamos el dict
        return jsonify({
            "ok": False, 
            "error": f"IP bloqueada. Intenta de nuevo más tarde."
        }), 403
    
    data = request.get_json() if request.is_json else request.form.to_dict()
    password = data.get("password", "")
    
    # Validar entrada
    if not password or len(password) < 3:
        record_failed_attempt(client_ip)
        return jsonify({"ok": False, "error": "Contraseña incorrecta"}), 403
    
    # Verificar contraseña usando hash
    password_hash = hash_password(password)
    
    if hmac.compare_digest(password_hash, ADMIN_PASSWORD_HASH):
        # Login exitoso
        reset_attempts(client_ip)
        token = generate_admin_token()
        response = jsonify({"ok": True, "message": "Autenticación exitosa"})
        response.set_cookie(
            "admin_token", 
            token, 
            max_age=ADMIN_SESSION_DURATION,
            httponly=True,  # Prevenir acceso desde JavaScript
            secure=False,  # Cambiar a True en producción con HTTPS
            samesite='Lax'  # Protección CSRF
        )
        print(f"✅ [ADMIN] Login exitoso desde IP: {client_ip}")
        return response
    else:
        # Login fallido
        record_failed_attempt(client_ip)
        print(f"⚠️ [ADMIN] Intento de login fallido desde IP: {client_ip}")
        
        return jsonify({
            "ok": False, 
            "error": "Contraseña incorrecta"
        }), 403

@admin_bp.route("/admin/logout")
def admin_logout():
    """Cerrar sesión de administrador"""
    # Invalidar el token
    token = request.cookies.get("admin_token")
    if token and token in VALID_ADMIN_TOKENS:
        VALID_ADMIN_TOKENS.discard(token)
        print(f"🔓 [ADMIN] Sesión cerrada, token invalidado")
    
    response = redirect("/")
    response.set_cookie("admin_token", "", max_age=0, httponly=True)
    return response

# API Endpoints para el Dashboard
@admin_bp.route("/api/admin/salas", methods=["GET"])
@require_admin_auth
def get_all_salas():
    """Obtener todas las salas activas (solo admin)"""
    salas = state_store.get_all_salas()
    salas_info = []
    
    for codigo, sala in salas.items():
        # Filtrar jugadores desconectados de la lista
        jugadores_activos = [
            j for j in sala.get("jugadores", []) 
            if j not in sala.get("jugadores_desconectados", [])
        ]
        
        salas_info.append({
            "codigo": codigo,
            "anfitrion": sala.get("anfitrion"),
            "jugadores": jugadores_activos,
            "estado": sala.get("estado", "espera"),
            "ronda_actual": sala.get("ronda_actual", 1),
            "total_rondas": sala.get("rondas", 1),
            "modo_juego": sala.get("modo_juego", "clasico"),
            "en_curso": sala.get("en_curso", False),
            "pausada": sala.get("pausada", False),
            "num_mensajes": len(sala.get("mensajes_chat", []))
        })
    
    return jsonify({
        "ok": True,
        "salas": salas_info,
        "total_salas": len(salas_info)
    })

@admin_bp.route("/api/admin/logs", methods=["GET"])
@require_admin_auth
def admin_get_logs():
    """Obtener logs del servidor en tiempo real"""
    return jsonify({
        "ok": True,
        "logs": list(server_logs)
    })

@admin_bp.route("/api/admin/estadisticas", methods=["GET"])
@require_admin_auth
def get_estadisticas():
    """Obtener estadísticas del sistema"""
    salas = state_store.get_all_salas()
    
    # Calcular estadísticas
    salas_activas = sum(1 for sala in salas.values() if sala.get("en_curso", False))
    total_mensajes = sum(len(sala.get("mensajes_chat", [])) for sala in salas.values())
    
    # Contar jugadores únicos (aproximado, mejor lógica requerida si usamos Redis)
    total_jugadores = sum(len(sala.get("jugadores", [])) for sala in salas.values())
    
    return jsonify({
        "ok": True,
        "estadisticas": {
            "total_salas": len(salas),
            "salas_activas": salas_activas,
            "salas_en_espera": len(salas) - salas_activas,
            "total_jugadores": total_jugadores,
            "total_mensajes": total_mensajes
        }
    })

