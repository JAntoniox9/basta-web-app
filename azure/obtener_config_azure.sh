#!/bin/bash

# ============================================
# 🔍 Script para Obtener Configuración de Azure
# ============================================
# Este script obtiene toda la información de tus recursos Azure
# y crea el archivo azure_config.txt
#
# Uso: bash obtener_config_azure.sh
# ============================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "============================================"
echo "🔍 Obteniendo Configuración de Azure"
echo "============================================"
echo ""

RG="basta-web-rg"

# Verificar login
if ! az account show &> /dev/null; then
    echo "❌ No has iniciado sesión en Azure"
    echo "Ejecuta: az login"
    exit 1
fi

echo "📋 Obteniendo información de recursos..."
echo ""

# Obtener nombre de la base de datos
echo "1️⃣ Buscando base de datos..."
DB_NAME=$(az postgres flexible-server list --resource-group "$RG" --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -z "$DB_NAME" ]; then
    echo "⚠️  No se encontró base de datos en $RG"
    DB_NAME="NO_ENCONTRADA"
    DB_HOST="NO_ENCONTRADA"
    DATABASE_URL="NO_ENCONTRADA"
else
    echo "✅ Base de datos encontrada: $DB_NAME"
    
    # Obtener FQDN
    DB_HOST=$(az postgres flexible-server show \
      --resource-group "$RG" \
      --name "$DB_NAME" \
      --query "fullyQualifiedDomainName" \
      -o tsv 2>/dev/null || echo "NO_ENCONTRADA")
    
    echo "✅ Host: $DB_HOST"
    
    # Construir DATABASE_URL
    DATABASE_URL="postgresql://bastaadmin:BastaPassword2025!@$DB_HOST:5432/basta_db?sslmode=require"
fi

echo ""

# Obtener nombre de la Web App
echo "2️⃣ Buscando Web App..."
APP_NAME=$(az webapp list --resource-group "$RG" --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -z "$APP_NAME" ]; then
    echo "⚠️  No se encontró Web App en $RG"
    APP_NAME="NO_ENCONTRADA"
    APP_URL="NO_ENCONTRADA"
else
    echo "✅ Web App encontrada: $APP_NAME"
    
    # Obtener URL
    APP_URL=$(az webapp show \
      --resource-group "$RG" \
      --name "$APP_NAME" \
      --query "defaultHostName" \
      -o tsv 2>/dev/null || echo "NO_ENCONTRADA")
    
    echo "✅ URL: https://$APP_URL"
fi

echo ""

# Obtener ubicación
LOCATION=$(az group show --name "$RG" --query "location" -o tsv 2>/dev/null || echo "mexicocentral")

echo "3️⃣ Creando archivo azure_config.txt..."
echo ""

# Crear archivo de configuración
CONFIG_FILE="azure_config.txt"
cat > "$CONFIG_FILE" << EOF
# Configuración de Azure - Basta Web
# Creado: $(date)

Resource Group: $RG
Ubicación: $LOCATION
Base de datos: $DB_NAME
Web App: $APP_NAME
URL: https://$APP_URL

DATABASE_URL=$DATABASE_URL

Comandos útiles:

# Ver logs
az webapp log tail --resource-group $RG --name $APP_NAME

# Reiniciar app
az webapp restart --resource-group $RG --name $APP_NAME

# Ver costos
az consumption usage list --output table

# Eliminar todo
az group delete --name $RG --yes
EOF

echo -e "${GREEN}✅ Archivo creado: $CONFIG_FILE${NC}"
echo ""
echo "📋 Contenido del archivo:"
echo "============================================"
cat "$CONFIG_FILE"
echo "============================================"
echo ""
echo -e "${BLUE}💡 Ahora puedes usar el DATABASE_URL en tu archivo .env${NC}"
echo ""

