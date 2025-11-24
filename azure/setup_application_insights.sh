#!/bin/bash

# ============================================
# 📊 Setup Application Insights - Paso 6
# ============================================
# Este script solo crea Application Insights
# y lo conecta con la Web App existente
#
# Uso: bash setup_application_insights.sh
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
echo "📊 Setup Application Insights - Paso 6"
echo "============================================"
echo ""

# Variables de configuración
RG="basta-web-rg"
LOCATION="mexicocentral"
INSIGHTS_NAME="basta-web-insights"

# Verificar que Azure CLI está instalado
print_info "Verificando Azure CLI..."
if ! command -v az &> /dev/null; then
    print_error "Azure CLI no está instalado"
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

# Verificar que el grupo de recursos existe
print_info "Verificando grupo de recursos: $RG"
if ! az group show --name "$RG" &> /dev/null; then
    print_error "El grupo de recursos $RG no existe"
    echo "Ejecuta primero: bash setup_azure_complete.sh"
    exit 1
fi
print_success "Grupo de recursos encontrado"

# Obtener nombre de la Web App
print_info "Buscando Web App en el grupo de recursos..."
APP_NAME=$(az webapp list --resource-group "$RG" --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -z "$APP_NAME" ]; then
    print_error "No se encontró ninguna Web App en $RG"
    echo "Ejecuta primero los pasos 1-5 del setup completo"
    exit 1
fi

print_success "Web App encontrada: $APP_NAME"
echo ""

# Verificar si Application Insights ya existe
print_info "Verificando si Application Insights ya existe..."
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
    fi
fi

echo ""
echo "============================================"
echo "📊 PASO 6: Application Insights"
echo "============================================"
echo ""

# Verificar y registrar proveedores
print_info "Verificando proveedores de recursos..."

OPINSIGHTS_STATE=$(az provider show --namespace "microsoft.operationalinsights" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")
INSIGHTS_STATE=$(az provider show --namespace "microsoft.insights" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")

if [ "$OPINSIGHTS_STATE" != "Registered" ] || [ "$INSIGHTS_STATE" != "Registered" ]; then
    print_warning "Algunos proveedores no están registrados"
    print_info "Registrando proveedores de recursos necesarios..."
    print_warning "Esto puede tomar 1-2 minutos. Por favor espera..."
    
    if [ "$OPINSIGHTS_STATE" != "Registered" ]; then
        print_info "Registrando microsoft.operationalinsights..."
        az provider register --namespace "microsoft.operationalinsights" --wait > /dev/null 2>&1 || true
        print_success "microsoft.operationalinsights registrado"
    fi
    
    if [ "$INSIGHTS_STATE" != "Registered" ]; then
        print_info "Registrando microsoft.insights..."
        az provider register --namespace "microsoft.insights" --wait > /dev/null 2>&1 || true
        print_success "microsoft.insights registrado"
    fi
else
    print_success "Proveedores de recursos ya están registrados"
fi

echo ""

# Crear Application Insights
print_info "Creando Application Insights: $INSIGHTS_NAME"
az monitor app-insights component create \
  --app "$INSIGHTS_NAME" \
  --location "$LOCATION" \
  --resource-group "$RG" \
  --application-type web > /dev/null

print_success "Application Insights creado"

# Conectar con Web App
print_info "Conectando Application Insights con Web App: $APP_NAME"
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app "$INSIGHTS_NAME" \
  --resource-group "$RG" \
  --query "instrumentationKey" \
  --output tsv)

az webapp config appsettings set \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY" > /dev/null

print_success "Application Insights conectado con Web App"

echo ""
echo "============================================"
echo "✅ APPLICATION INSIGHTS CONFIGURADO"
echo "============================================"
echo ""

print_success "¡Application Insights está listo!"
echo ""
echo "📋 RESUMEN:"
echo "  Application Insights: $INSIGHTS_NAME"
echo "  Conectado con: $APP_NAME"
echo "  Instrumentation Key: $INSTRUMENTATION_KEY"
echo ""
echo "🔍 Para ver métricas:"
echo "  1. Ve a: https://portal.azure.com"
echo "  2. Busca: $INSIGHTS_NAME"
echo "  3. Click en 'Application Insights'"
echo ""

