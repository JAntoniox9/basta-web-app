#!/bin/bash

# ============================================
# 🔧 Script para Registrar Proveedores de Recursos
# ============================================
# Este script registra los proveedores necesarios
# para crear Application Insights en Azure
#
# Uso: bash registrar_proveedores.sh
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
echo "🔧 Registro de Proveedores de Recursos"
echo "============================================"
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

# Registrar proveedores
echo "============================================"
echo "📋 Registrando Proveedores"
echo "============================================"
echo ""

print_info "Registrando microsoft.operationalinsights..."
print_warning "Esto puede tomar 1-2 minutos. Por favor espera..."
az provider register --namespace "microsoft.operationalinsights" --wait
print_success "microsoft.operationalinsights registrado"

echo ""

print_info "Registrando microsoft.insights..."
print_warning "Esto puede tomar 1-2 minutos. Por favor espera..."
az provider register --namespace "microsoft.insights" --wait
print_success "microsoft.insights registrado"

echo ""
echo "============================================"
echo "🔍 Verificación"
echo "============================================"
echo ""

print_info "Verificando estado de los proveedores..."

OPINSIGHTS_STATE=$(az provider show --namespace "microsoft.operationalinsights" --query "registrationState" -o tsv)
INSIGHTS_STATE=$(az provider show --namespace "microsoft.insights" --query "registrationState" -o tsv)

echo ""
echo "Estado de microsoft.operationalinsights: $OPINSIGHTS_STATE"
echo "Estado de microsoft.insights: $INSIGHTS_STATE"
echo ""

if [ "$OPINSIGHTS_STATE" == "Registered" ] && [ "$INSIGHTS_STATE" == "Registered" ]; then
    print_success "¡Todos los proveedores están registrados correctamente!"
    echo ""
    echo "Ahora puedes crear Application Insights ejecutando:"
    echo "  az monitor app-insights component create \\"
    echo "    --app basta-web-insights \\"
    echo "    --location mexicocentral \\"
    echo "    --resource-group basta-web-rg \\"
    echo "    --application-type web"
else
    print_warning "Algunos proveedores aún no están registrados."
    print_info "Espera unos minutos y verifica de nuevo con:"
    echo "  az provider show --namespace microsoft.operationalinsights"
    echo "  az provider show --namespace microsoft.insights"
fi

echo ""

