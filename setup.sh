#!/bin/bash
# Script de configuración inicial para jfc-cash-to-pay-audit
# Este script ayuda a configurar el proyecto en Google Cloud

set -e

PROJECT_ID="check-in-sf"
FUNCTION_NAME="jfc-cash-to-pay-audit"
REGION="us-central1"
SERVICE_ACCOUNT_NAME="github-actions"

echo "🚀 Configurando proyecto Google Cloud: $PROJECT_ID"
echo "================================================"

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado"
    echo "Instala desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configurar proyecto
echo "📋 Configurando proyecto..."
gcloud config set project $PROJECT_ID

# Habilitar APIs necesarias
echo "🔌 Habilitando APIs necesarias..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  --project=$PROJECT_ID

# Crear repositorio en Artifact Registry
echo "📦 Creando repositorio en Artifact Registry..."
gcloud artifacts repositories create cloud-functions \
  --repository-format=docker \
  --location=$REGION \
  --description="Repositorio para Cloud Functions" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠️  El repositorio ya existe, continuando..."

# Crear cuenta de servicio
echo "👤 Creando cuenta de servicio..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="GitHub Actions Service Account" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠️  La cuenta de servicio ya existe, continuando..."

SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Asignar roles
echo "🔐 Asignando roles a la cuenta de servicio..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/cloudfunctions.developer" \
  --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/artifactregistry.writer" \
  --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin" \
  --condition=None 2>/dev/null || true

# Crear clave JSON
echo "🔑 Creando clave JSON para GitHub Actions..."
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=$SERVICE_ACCOUNT_EMAIL \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠️  La clave ya existe, se sobrescribirá..."

echo ""
echo "✅ Configuración completada!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Agrega el contenido de 'github-actions-key.json' como secreto GCP_SA_KEY en GitHub"
echo "2. Agrega '$SERVICE_ACCOUNT_EMAIL' como secreto GCP_SA_EMAIL en GitHub"
echo "3. Haz commit y push de tu código a GitHub"
echo "4. El despliegue se ejecutará automáticamente"
echo ""
echo "⚠️  IMPORTANTE: No subas 'github-actions-key.json' a Git!"
echo "   Está incluido en .gitignore por seguridad"

