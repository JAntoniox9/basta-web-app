#!/usr/bin/env python3
"""
🗄️ Script para crear las tablas en RDS
Ejecutar: python setup_database.py
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def setup_database():
    """Crea las tablas necesarias en RDS"""
    
    print("=" * 60)
    print("🗄️  CONFIGURANDO BASE DE DATOS RDS")
    print("=" * 60)
    print()
    
    # Verificar DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url or database_url.startswith("#"):
        print("❌ ERROR: DATABASE_URL no configurado")
        print("   Ejecuta primero: python test_rds_connection.py")
        return False
    
    try:
        from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, Boolean, Text
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime
        
        print("✅ Librerías importadas")
        print()
        
        # Crear engine
        engine = create_engine(database_url, pool_pre_ping=True)
        Base = declarative_base()
        
        # Definir modelo de tabla
        class Sala(Base):
            __tablename__ = "salas"
            
            codigo = Column(String(10), primary_key=True, index=True)
            anfitrion = Column(String(100), nullable=False)
            jugadores = Column(JSON, default=list)
            jugadores_desconectados = Column(JSON, default=list)
            estado = Column(String(50), default="espera")
            
            # Configuración
            rondas = Column(Integer, default=1)
            ronda_actual = Column(Integer, default=1)
            dificultad = Column(String(20), default="normal")
            modo_juego = Column(String(50), default="clasico")
            categorias = Column(JSON, default=list)
            
            # Juego
            letra = Column(String(1), nullable=True)
            en_curso = Column(Boolean, default=False)
            pausada = Column(Boolean, default=False)
            finalizada = Column(Boolean, default=False)
            tiempo_restante = Column(Integer, default=180)
            basta = Column(Boolean, default=False)
            basta_activado = Column(Boolean, default=False)
            
            # Datos del juego
            puntuaciones = Column(JSON, default=dict)
            respuestas_ronda = Column(JSON, default=dict)
            jugadores_listos = Column(JSON, default=list)
            mensajes_chat = Column(JSON, default=list)
            
            # Power-ups y validación
            powerups_habilitados = Column(Boolean, default=True)
            powerups_jugadores = Column(JSON, default=dict)
            validacion_activa = Column(Boolean, default=True)
            validaciones_ia = Column(JSON, default=dict)
            apelaciones = Column(JSON, default=dict)
            respuestas_cuestionadas = Column(JSON, default=dict)
            votos_validacion = Column(JSON, default=dict)
            penalizaciones = Column(JSON, default=dict)
            
            # Configuración adicional
            chat_habilitado = Column(Boolean, default=True)
            sonidos_habilitados = Column(Boolean, default=True)
            equipos = Column(JSON, default=dict)
            puntuaciones_equipos = Column(JSON, default=dict)
            
            # IDs de jugadores para Socket.IO
            jugadores_ids = Column(JSON, default=dict)
            ids_jugadores = Column(JSON, default=dict)
            
            # Timestamps
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            inicio_ronda = Column(DateTime, nullable=True)
        
        print("📋 Modelo de tabla definido")
        print()
        print("-" * 60)
        print("🔨 Creando tablas en RDS...")
        print("-" * 60)
        print()
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tabla 'salas' creada exitosamente")
        print()
        
        # Verificar que la tabla existe
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("📊 Tablas en la base de datos:")
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"   ✅ {table} ({len(columns)} columnas)")
        
        print()
        print("=" * 60)
        print("✅ BASE DE DATOS CONFIGURADA CORRECTAMENTE")
        print("=" * 60)
        print()
        print("🎯 Siguiente paso:")
        print("   1. Ejecuta: python test_migration.py")
        print("   2. Luego inicia el servidor: python run.py")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("❌ ERROR AL CREAR TABLAS")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        
        if "psycopg2" in str(e):
            print("💡 Instala: pip install psycopg2-binary")
        elif "sqlalchemy" in str(e):
            print("💡 Instala: pip install SQLAlchemy")
        else:
            print("💡 Verifica que RDS está accesible:")
            print("   python test_rds_connection.py")
        
        print()
        return False

if __name__ == "__main__":
    print()
    success = setup_database()
    print()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

