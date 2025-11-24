#!/usr/bin/env python3
"""
🔍 Script de prueba para verificar conexión a RDS
Ejecutar: python test_rds_connection.py
"""

import os
import sys
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_rds_connection():
    """Prueba la conexión a RDS PostgreSQL"""
    
    print("=" * 60)
    print("🔍 PROBANDO CONEXIÓN A AWS RDS")
    print("=" * 60)
    print()
    
    # 1. Verificar que DATABASE_URL está configurado
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado en .env")
        print()
        print("Por favor agrega esta línea a tu archivo .env:")
        print("DATABASE_URL=postgresql://usuario:password@endpoint:5432/basta_db")
        return False
    
    if database_url.startswith("#") or "endpoint" in database_url:
        print("❌ ERROR: DATABASE_URL está comentado o tiene valores de ejemplo")
        print()
        print("Tu DATABASE_URL actual:")
        print(f"  {database_url}")
        print()
        print("Debe ser algo como:")
        print("  postgresql://bastaadmin:password@basta-web-db.xxxxx.rds.amazonaws.com:5432/basta_db")
        return False
    
    print("✅ DATABASE_URL configurado")
    print(f"   {database_url[:50]}...")
    print()
    
    # 2. Verificar que psycopg2 está instalado
    try:
        import psycopg2
        print("✅ psycopg2 instalado")
    except ImportError:
        print("❌ ERROR: psycopg2 no está instalado")
        print()
        print("Instálalo con:")
        print("  pip install psycopg2-binary")
        return False
    
    # 3. Verificar que SQLAlchemy está instalado
    try:
        import sqlalchemy
        print("✅ SQLAlchemy instalado")
    except ImportError:
        print("❌ ERROR: SQLAlchemy no está instalado")
        print()
        print("Instálalo con:")
        print("  pip install SQLAlchemy")
        return False
    
    print()
    print("-" * 60)
    print("🔌 Intentando conectar a RDS...")
    print("-" * 60)
    
    # 4. Intentar conexión con SQLAlchemy
    try:
        from sqlalchemy import create_engine, text
        
        # Crear engine con configuración de prueba
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verifica conexión antes de usar
            connect_args={
                "connect_timeout": 10,  # Timeout de 10 segundos
            }
        )
        
        # Medir latencia
        start_time = time.time()
        
        # Ejecutar query simple
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row[0] == 1:
                latency = (time.time() - start_time) * 1000  # en ms
                
                print()
                print("✅ CONEXIÓN EXITOSA A RDS")
                print(f"✅ Latencia: {latency:.0f}ms")
                print()
                
                # Obtener información de la base de datos
                result = connection.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"📊 Versión PostgreSQL:")
                print(f"   {version}")
                print()
                
                # Verificar Multi-AZ (si está disponible)
                print("🔄 Verificando replicación...")
                result = connection.execute(text("""
                    SELECT pg_is_in_recovery() as is_standby
                """))
                is_standby = result.fetchone()[0]
                
                if is_standby:
                    print("   ℹ️ Esta es una réplica Standby")
                else:
                    print("   ℹ️ Esta es la instancia Primary")
                print()
                
                print("=" * 60)
                print("✅ TODO CORRECTO - RDS funcionando perfectamente")
                print("=" * 60)
                return True
                
    except Exception as e:
        print()
        print("❌ ERROR DE CONEXIÓN")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        
        # Diagnóstico según el tipo de error
        error_msg = str(e).lower()
        
        if "timeout" in error_msg or "timed out" in error_msg:
            print("🔍 DIAGNÓSTICO:")
            print("   - El timeout indica que no se puede alcanzar el servidor RDS")
            print()
            print("✅ SOLUCIONES:")
            print("   1. Verifica que el Security Group permite conexiones:")
            print("      - Ve a RDS → basta-web-db → Connectivity & Security")
            print("      - Click en el Security Group")
            print("      - Inbound rules debe tener:")
            print("        Type: PostgreSQL, Port: 5432, Source: 0.0.0.0/0")
            print()
            print("   2. Verifica que 'Public accessibility' está en YES")
            print()
            
        elif "password" in error_msg or "authentication" in error_msg:
            print("🔍 DIAGNÓSTICO:")
            print("   - Usuario o contraseña incorrectos")
            print()
            print("✅ SOLUCIONES:")
            print("   1. Verifica el username y password en .env")
            print("   2. Verifica que usaste los mismos al crear RDS")
            print()
            
        elif "could not translate host name" in error_msg or "name or service not known" in error_msg:
            print("🔍 DIAGNÓSTICO:")
            print("   - El endpoint de RDS es incorrecto")
            print()
            print("✅ SOLUCIONES:")
            print("   1. Ve a RDS Console → Databases → basta-web-db")
            print("   2. Copia el Endpoint exacto")
            print("   3. Actualiza DATABASE_URL en .env")
            print()
            
        else:
            print("🔍 DIAGNÓSTICO:")
            print("   - Error desconocido")
            print()
            print("✅ SOLUCIONES:")
            print("   1. Verifica que RDS está en estado 'Available'")
            print("   2. Verifica todas las credenciales en .env")
            print("   3. Verifica el Security Group")
            print()
        
        return False
    
    return False

if __name__ == "__main__":
    print()
    success = test_rds_connection()
    print()
    
    if success:
        print("🎉 ¡Puedes continuar con el siguiente paso!")
        print("   Ejecuta: python setup_database.py")
        sys.exit(0)
    else:
        print("⚠️  Soluciona los errores antes de continuar")
        sys.exit(1)

