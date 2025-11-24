# 📁 Carpeta Azure - Scripts y Documentación

Esta carpeta contiene todos los archivos relacionados con la configuración y despliegue en Azure.

## 📋 Contenido

### 📘 Documentación
- **`GUIA_COMPLETA_AZURE.md`** - Guía completa paso a paso para configurar Azure (lee este primero)

### 🔧 Scripts de Setup (.sh)
- **`setup_azure_complete.sh`** - Script principal que crea toda la infraestructura automáticamente
- **`setup_application_insights.sh`** - Script para crear solo Application Insights
- **`registrar_proveedores.sh`** - Script para registrar proveedores de recursos necesarios
- **`obtener_config_azure.sh`** - Script para obtener configuración y crear `azure_config.txt`

### 🧪 Scripts de Prueba (.py)
- **`test_rds_connection.py`** - Probar conexión a Azure Database
- **`setup_database.py`** - Crear tablas en Azure Database
- **`test_migration.py`** - Probar migración de datos
- **`verificar_azure_storage.py`** - Verificar que los datos se guardan en Azure

### ⚙️ Configuración
- **`azure_config.txt`** - Archivo generado automáticamente con la configuración de tus recursos Azure

## 🚀 Uso Rápido

### Setup Completo (Recomendado)
```bash
# Desde la raíz del proyecto
bash azure/setup_azure_complete.sh
```

### Probar Conexión
```bash
# Desde la raíz del proyecto
python azure/test_rds_connection.py
```

### Crear Tablas
```bash
# Desde la raíz del proyecto
python azure/setup_database.py
```

## 📖 Documentación Completa

Para instrucciones detalladas, consulta: **`azure/GUIA_COMPLETA_AZURE.md`**

---

**Nota:** Todos los scripts deben ejecutarse desde la raíz del proyecto (no desde dentro de la carpeta `azure/`).

