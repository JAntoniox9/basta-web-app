#!/bin/bash

# ============================================
# 🚀 Setup Completo - Basta Web en Azure
# ============================================
# Este script configura TODA la infraestructura de Azure
# para el sistema distribuido Basta Web
#
# Uso: bash setup_azure_complete.sh
# ============================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo ""
echo "============================================"
echo "🚀 Setup Basta Web - Azure Student"
echo "============================================"
echo ""

# Variables de configuración
RG="basta-web-rg"
LOCATION="mexicocentral"
DB_NAME="basta-web-db-$RANDOM"  # Nombre único
DB_USER="bastaadmin"
DB_PASS="BastaPassword2025!"
APP_NAME="basta-web-app-$RANDOM"  # Nombre único
PLAN_NAME="basta-web-plan"
INSIGHTS_NAME="basta-web-insights"
AUTOSCALE_NAME="basta-autoscale"

print_info "Configuración:"
echo "  Resource Group: $RG"
echo "  Ubicación: $LOCATION"
echo "  Base de datos: $DB_NAME"
echo "  App Service: $APP_NAME"
echo ""

# Verificar que Azure CLI está instalado
print_info "Verificando Azure CLI..."
if ! command -v az &> /dev/null; then
    print_error "Azure CLI no está instalado"
    echo "Instálalo desde: https://aka.ms/installazurecliwindows"
    exit 1
fi
print_success "Azure CLI instalado"

# Verificar login
print_info "Verificando login en Azure..."
if ! az account show &> /dev/null; then
    print_warning "No has iniciado sesión en Azure"
    echo "Ejecutando: az login"
    az login
fi
print_success "Sesión activa en Azure"

# Mostrar cuenta actual
ACCOUNT=$(az account show --query "name" -o tsv)
print_info "Cuenta actual: $ACCOUNT"
echo ""

# Preguntar confirmación
read -p "¿Continuar con el setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Setup cancelado"
    exit 0
fi

echo ""
echo "============================================"
echo "📦 PASO 1: Grupo de Recursos"
echo "============================================"
echo ""

print_info "Creando grupo de recursos: $RG"
az group create --name "$RG" --location "$LOCATION" > /dev/null
print_success "Grupo de recursos creado"

echo ""
echo "============================================"
echo "🗄️  PASO 2: Base de Datos PostgreSQL"
echo "============================================"
echo ""

print_info "Creando Azure Database for PostgreSQL (Burstable tier)..."
print_warning "Esto puede tomar 5-10 minutos. Por favor espera..."

az postgres flexible-server create \
  --resource-group "$RG" \
  --name "$DB_NAME" \
  --location "$LOCATION" \
  --admin-user "$DB_USER" \
  --admin-password "$DB_PASS" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0-255.255.255.255 \
  --yes > /dev/null

print_success "Base de datos creada (Burstable - optimizado para Azure Student)"

print_info "Creando base de datos: basta_db"
az postgres flexible-server db create \
  --resource-group "$RG" \
  --server-name "$DB_NAME" \
  --database-name basta_db > /dev/null

print_success "Base de datos basta_db creada"

# Obtener FQDN de la base de datos
DB_HOST=$(az postgres flexible-server show \
  --resource-group "$RG" \
  --name "$DB_NAME" \
  --query "fullyQualifiedDomainName" \
  --output tsv)

print_success "Endpoint de base de datos: $DB_HOST"

echo ""
echo "============================================"
echo "🌐 PASO 3: App Service"
echo "============================================"
echo ""

print_info "Creando App Service Plan: $PLAN_NAME"
az appservice plan create \
  --name "$PLAN_NAME" \
  --resource-group "$RG" \
  --sku B1 \
  --is-linux > /dev/null

print_success "App Service Plan creado"

print_info "Creando Web App: $APP_NAME"
az webapp create \
  --resource-group "$RG" \
  --plan "$PLAN_NAME" \
  --name "$APP_NAME" \
  --runtime "PYTHON:3.11" > /dev/null

print_success "Web App creada"

# Obtener URL de la app
APP_URL=$(az webapp show \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --query "defaultHostName" \
  --output tsv)

print_success "URL de la aplicación: https://$APP_URL"

echo ""
echo "============================================"
echo "⚙️  PASO 4: Configuración"
echo "============================================"
echo ""

print_info "Configurando variables de entorno..."

DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:5432/basta_db?sslmode=require"

az webapp config appsettings set \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --settings \
    DATABASE_URL="$DATABASE_URL" \
    ADMIN_PASSWORD="CambiarEstoEnProduccion" \
    SECRET_KEY="basta_secret_key_super_seguro_2025" \
    FLASK_ENV="production" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" > /dev/null

print_success "Variables de entorno configuradas"

print_info "Configurando startup command..."
az webapp config set \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --workers=2 run:flask_application" > /dev/null

print_success "Startup command configurado"

echo ""
echo "============================================"
echo "📈 PASO 5: Auto-Scaling"
echo "============================================"
echo ""

print_info "Configurando auto-scaling (2-5 instancias)..."

az monitor autoscale create \
  --resource-group "$RG" \
  --resource "$PLAN_NAME" \
  --resource-type Microsoft.Web/serverfarms \
  --name "$AUTOSCALE_NAME" \
  --min-count 2 \
  --max-count 5 \
  --count 2 > /dev/null

print_success "Auto-scaling configurado"

print_info "Agregando regla: Scale out si CPU > 75%"
az monitor autoscale rule create \
  --resource-group "$RG" \
  --autoscale-name "$AUTOSCALE_NAME" \
  --condition "CpuPercentage > 75 avg 5m" \
  --scale out 1 > /dev/null

print_info "Agregando regla: Scale in si CPU < 25%"
az monitor autoscale rule create \
  --resource-group "$RG" \
  --autoscale-name "$AUTOSCALE_NAME" \
  --condition "CpuPercentage < 25 avg 5m" \
  --scale in 1 > /dev/null

print_success "Reglas de auto-scaling configuradas"

echo ""
echo "============================================"
echo "📊 PASO 6: Application Insights"
echo "============================================"
echo ""

# Verificar si Application Insights ya existe
if az monitor app-insights component show --app "$INSIGHTS_NAME" --resource-group "$RG" &> /dev/null; then
    print_warning "Application Insights '$INSIGHTS_NAME' ya existe"
    read -p "¿Deseas recrearlo? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Eliminando Application Insights existente..."
        az monitor app-insights component delete --app "$INSIGHTS_NAME" --resource-group "$RG" --yes > /dev/null 2>&1 || true
        print_success "Application Insights eliminado"
    else
        print_info "Usando Application Insights existente"
        print_success "Application Insights ya está configurado"
        # Verificar si está conectado con Web App
        if az webapp config appsettings list --resource-group "$RG" --name "$APP_NAME" --query "[?name=='APPINSIGHTS_INSTRUMENTATIONKEY']" -o tsv | grep -q .; then
            print_success "Application Insights ya está conectado con Web App"
        else
            print_info "Conectando Application Insights con Web App..."
            INSTRUMENTATION_KEY=$(az monitor app-insights component show \
              --app "$INSIGHTS_NAME" \
              --resource-group "$RG" \
              --query "instrumentationKey" \
              --output tsv)
            az webapp config appsettings set \
              --resource-group "$RG" \
              --name "$APP_NAME" \
              --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY" > /dev/null
            print_success "Application Insights conectado"
        fi
        # Saltar al final
        echo ""
        echo "============================================"
        echo "✅ SETUP COMPLETO"
        echo "============================================"
        echo ""
        print_success "Infraestructura verificada exitosamente!"
        echo ""
        echo "📋 RESUMEN:"
        echo "  Resource Group: $RG"
        DB_EXISTING=$(az postgres flexible-server list --resource-group "$RG" --query "[0].name" -o tsv 2>/dev/null || echo "")
        if [ ! -z "$DB_EXISTING" ]; then
            echo "  Base de datos: $DB_EXISTING"
        fi
        echo "  Web App: $APP_NAME"
        APP_URL=$(az webapp show --resource-group "$RG" --name "$APP_NAME" --query "defaultHostName" -o tsv 2>/dev/null || echo "")
        if [ ! -z "$APP_URL" ]; then
            echo ""
            echo "🌐 URL de tu aplicación:"
            echo "  https://$APP_URL"
        fi
        echo ""
        exit 0
    fi
fi

# Verificar estado de proveedores antes de registrar
print_info "Verificando proveedores de recursos..."
OPINSIGHTS_STATE=$(az provider show --namespace "microsoft.operationalinsights" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")
INSIGHTS_STATE=$(az provider show --namespace "microsoft.insights" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")

if [ "$OPINSIGHTS_STATE" != "Registered" ] || [ "$INSIGHTS_STATE" != "Registered" ]; then
    print_info "Registrando proveedores de recursos necesarios..."
    print_warning "Esto puede tomar 1-2 minutos. Por favor espera..."
    
    if [ "$OPINSIGHTS_STATE" != "Registered" ]; then
        az provider register --namespace "microsoft.operationalinsights" --wait > /dev/null 2>&1 || true
    fi
    
    if [ "$INSIGHTS_STATE" != "Registered" ]; then
        az provider register --namespace "microsoft.insights" --wait > /dev/null 2>&1 || true
    fi
    
    print_success "Proveedores de recursos registrados"
else
    print_success "Proveedores de recursos ya están registrados"
fi

print_info "Creando Application Insights..."
az monitor app-insights component create \
  --app "$INSIGHTS_NAME" \
  --location "$LOCATION" \
  --resource-group "$RG" \
  --application-type web > /dev/null

print_success "Application Insights creado"

print_info "Conectando con Web App..."
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app "$INSIGHTS_NAME" \
  --resource-group "$RG" \
  --query "instrumentationKey" \
  --output tsv)

az webapp config appsettings set \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY" > /dev/null

print_success "Application Insights conectado"

echo ""
echo "============================================"
echo "✅ SETUP COMPLETO"
echo "============================================"
echo ""

print_success "Infraestructura creada exitosamente!"
echo ""
echo "📋 RESUMEN:"
echo "  Resource Group: $RG"
echo "  Base de datos: $DB_NAME"
echo "  Web App: $APP_NAME"
echo ""
echo "🌐 URL de tu aplicación:"
echo "  https://$APP_URL"
echo ""
echo "🗄️  CONNECTION STRING:"
echo "  $DATABASE_URL"
echo ""
echo "📝 SIGUIENTE PASO:"
echo "  1. Actualiza ADMIN_PASSWORD en Azure Portal o con:"
echo "     az webapp config appsettings set --name $APP_NAME --resource-group $RG --settings ADMIN_PASSWORD='TuPassword'"
echo ""
echo "  2. Despliega tu código:"
echo "     az webapp deployment source config-zip --name $APP_NAME --resource-group $RG --src basta-web.zip"
echo ""
echo "💰 COSTO ESTIMADO: ~\$25-30/mes (optimizado para Azure Student)"
echo ""

# Guardar información en archivo
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

print_success "Configuración guardada en: $CONFIG_FILE"
echo ""

