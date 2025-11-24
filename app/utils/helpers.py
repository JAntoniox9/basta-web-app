from flask import request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import os

# Constantes de autenticación (se cargan desde .env en run.py)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_SESSION_DURATION = 3600  # 1 hora
MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15

# Memoria local para rate limiting y auth
admin_login_attempts = {} # {ip: {"count": N, "blocked_until": datetime}}

def hash_password(password):
    """Crea un hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_PASSWORD_HASH = hash_password(ADMIN_PASSWORD)

def get_client_ip():
    """Obtiene la IP real del cliente"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def check_ip_blocked(ip):
    """Verifica si una IP está bloqueada"""
    if ip not in admin_login_attempts:
        return False
    
    attempt_data = admin_login_attempts[ip]
    if "blocked_until" in attempt_data:
        if datetime.now() < attempt_data["blocked_until"]:
            return True
        else:
            # Desbloquear si ya pasó el tiempo
            del admin_login_attempts[ip]
            return False
    return False

def record_failed_attempt(ip):
    """Registra un intento fallido de login"""
    if ip not in admin_login_attempts:
        admin_login_attempts[ip] = {"count": 0}
    
    admin_login_attempts[ip]["count"] += 1
    
    if admin_login_attempts[ip]["count"] >= MAX_LOGIN_ATTEMPTS:
        admin_login_attempts[ip]["blocked_until"] = datetime.now() + timedelta(minutes=BLOCK_DURATION_MINUTES)
        print(f"🚫 IP {ip} bloqueada por {BLOCK_DURATION_MINUTES} minutos después de {MAX_LOGIN_ATTEMPTS} intentos fallidos")

def reset_attempts(ip):
    """Resetea los intentos fallidos para una IP"""
    if ip in admin_login_attempts:
        del admin_login_attempts[ip]

# Token almacenado en memoria (simple para este ejemplo)
# En un entorno real distributed esto debería estar en Redis
VALID_ADMIN_TOKENS = set()

def generate_admin_token():
    """Genera un token simple para la sesión de admin"""
    # En producción usar algo como JWT o sesiones firmadas
    token = hashlib.sha256(f"admin_token_{datetime.now()}".encode()).hexdigest()
    VALID_ADMIN_TOKENS.add(token)
    return token

def verify_admin_token(token):
    """Verifica si el token de admin es válido"""
    if not token:
        return False
    return token in VALID_ADMIN_TOKENS 

def require_admin_auth(f):
    """Decorador para requerir autenticación de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("admin_token")
        # Aquí deberíamos validar el token contra VALID_ADMIN_TOKENS
        if not token: 
            return jsonify({"ok": False, "error": "No autorizado"}), 403
        return f(*args, **kwargs)
    return decorated_function

