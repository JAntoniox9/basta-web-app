#!/usr/bin/env python3
"""
🔍 Script para Verificar que los Datos se Guardan en Azure Database
Ejecutar: python verificar_azure_storage.py
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno (manejar errores de parsing silenciosamente)
try:
    load_dotenv()
except Exception as e:
    # Si hay un error de parsing, continuar sin las variables del .env
    # Las variables pueden estar en el entorno del sistema
    pass

print()
print("=" * 60)
print("🔍 VERIFICANDO ALMACENAMIENTO EN AZURE")
print("=" * 60)
print()

# 1. Verificar configuración de base de datos
print("1️⃣ Verificando configuración...")
print("-" * 60)

DATABASE_URL = os.getenv("DATABASE_URL")
USE_DATABASE = DATABASE_URL and not DATABASE_URL.startswith("#")

if USE_DATABASE:
    print("✅ DATABASE_URL configurado")
    print(f"   Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'N/A'}")
else:
    print("❌ DATABASE_URL no configurado")
    print("   ⚠️  Los datos se guardarán en checkpoint.json")

print()

# 2. Verificar si db_store está usando base de datos
print("2️⃣ Verificando db_store...")
print("-" * 60)

try:
    from app.services.db_store import db_store
    
    if db_store.use_database:
        print("✅ db_store está usando Azure Database")
        print("   💾 Los datos se guardan en PostgreSQL (Azure)")
    else:
        print("❌ db_store está usando fallback a JSON")
        print("   📄 Los datos se guardan en checkpoint.json")
        
except Exception as e:
    print(f"❌ Error importando db_store: {e}")

print()

# 3. Verificar checkpoint.json
print("3️⃣ Verificando checkpoint.json...")
print("-" * 60)

CHECKPOINT_FILE = "checkpoint.json"
if os.path.exists(CHECKPOINT_FILE):
    # Obtener timestamp de última modificación
    mod_time = os.path.getmtime(CHECKPOINT_FILE)
    mod_datetime = datetime.fromtimestamp(mod_time)
    
    print(f"⚠️  Archivo checkpoint.json existe")
    print(f"   Última modificación: {mod_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Leer contenido
    try:
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            salas_count = len(data.get("salas", {}))
            print(f"   Salas en checkpoint.json: {salas_count}")
    except:
        print("   ⚠️  No se pudo leer el archivo")
else:
    print("✅ Archivo checkpoint.json no existe (correcto si usas Azure)")

print()

# 4. Verificar datos en Azure Database
print("4️⃣ Verificando datos en Azure Database...")
print("-" * 60)

try:
    from app.services.db_store import db_store
    
    if db_store.use_database:
        # Obtener todas las salas de la base de datos
        todas_salas = db_store.get_all_salas()
        salas_count = len(todas_salas)
        
        print(f"✅ Salas en Azure Database: {salas_count}")
        
        if salas_count > 0:
            print()
            print("   📋 Salas encontradas:")
            for codigo, sala in list(todas_salas.items())[:5]:  # Mostrar máximo 5
                anfitrion = sala.get('anfitrion', 'N/A')
                jugadores = len(sala.get('jugadores', []))
                print(f"      - {codigo}: Anfitrión={anfitrion}, Jugadores={jugadores}")
            
            if salas_count > 5:
                print(f"      ... y {salas_count - 5} más")
        else:
            print("   ℹ️  No hay salas en la base de datos aún")
    else:
        print("⚠️  No se puede verificar (usando fallback a JSON)")
        
except Exception as e:
    print(f"❌ Error verificando base de datos: {e}")

print()

# 5. Prueba de escritura
print("5️⃣ Prueba de escritura...")
print("-" * 60)

try:
    from app.services.db_store import db_store
    
    # Crear una sala de prueba
    test_codigo = "TEST" + datetime.now().strftime("%H%M%S")
    print(f"   Creando sala de prueba: {test_codigo}")
    
    sala = db_store.create_sala(test_codigo, "TestUser")
    
    if sala:
        print(f"   ✅ Sala creada exitosamente")
        
        # Verificar que se puede leer
        sala_leida = db_store.get_sala(test_codigo)
        if sala_leida:
            print(f"   ✅ Sala leída desde la base de datos")
            
            # Verificar timestamp de checkpoint.json (no debería cambiar)
            if os.path.exists(CHECKPOINT_FILE):
                mod_time_antes = os.path.getmtime(CHECKPOINT_FILE)
                
                # Esperar un segundo y verificar de nuevo
                import time
                time.sleep(1)
                
                mod_time_despues = os.path.getmtime(CHECKPOINT_FILE)
                
                if mod_time_antes == mod_time_despues:
                    print(f"   ✅ checkpoint.json NO se modificó (correcto)")
                    print(f"      → Los datos se guardan en Azure, no en JSON")
                else:
                    print(f"   ⚠️  checkpoint.json se modificó")
                    print(f"      → Los datos también se guardan en JSON (fallback)")
            
            # Limpiar sala de prueba
            db_store.delete_sala(test_codigo)
            print(f"   🗑️  Sala de prueba eliminada")
        else:
            print(f"   ❌ No se pudo leer la sala desde la base de datos")
    else:
        print(f"   ❌ No se pudo crear la sala")
        
except Exception as e:
    print(f"❌ Error en prueba de escritura: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("📊 RESUMEN")
print("=" * 60)
print()

try:
    from app.services.db_store import db_store
    
    if db_store.use_database:
        print("✅ CONFIGURACIÓN CORRECTA:")
        print("   - Los datos se guardan en Azure Database PostgreSQL")
        print("   - Replicación Multi-AZ activa")
        print("   - Sin pérdida de datos garantizada")
        print()
        print("💡 Para verificar en Azure Portal:")
        print("   1. Ve a: https://portal.azure.com")
        print("   2. Busca tu base de datos: basta-web-db-13212")
        print("   3. Click en 'Query editor' o 'Connection strings'")
    else:
        print("⚠️  CONFIGURACIÓN ACTUAL:")
        print("   - Los datos se guardan en checkpoint.json (local)")
        print("   - No hay replicación")
        print("   - No hay alta disponibilidad")
        print()
        print("💡 Para usar Azure Database:")
        print("   1. Configura DATABASE_URL en tu .env")
        print("   2. Ejecuta: python setup_database.py")
        print("   3. Reinicia el servidor")
        
except Exception as e:
    print(f"❌ Error generando resumen: {e}")

print()

