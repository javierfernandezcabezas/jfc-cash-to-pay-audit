# Script de configuración inicial para jfc-cash-to-pay-audit (PowerShell)
# Este script ayuda a configurar el proyecto en Google Cloud

$ErrorActionPreference = "Stop"

$PROJECT_ID = "check-in-sf"
$FUNCTION_NAME = "jfc-cash-to-pay-audit"
$REGION = "us-central1"
$SERVICE_ACCOUNT_NAME = "github-actions"

Write-Host "🚀 Configurando proyecto Google Cloud: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Verificar que gcloud está instalado
try {
    $null = gcloud --version 2>&1
} catch {
    Write-Host "❌ Error: gcloud CLI no está instalado" -ForegroundColor Red
    Write-Host "Instala desde: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Configurar proyecto
Write-Host "📋 Configurando proyecto..." -ForegroundColor Green
gcloud config set project $PROJECT_ID

# Habilitar APIs necesarias
Write-Host "🔌 Habilitando APIs necesarias..." -ForegroundColor Green
gcloud services enable `
  cloudfunctions.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  run.googleapis.com `
  --project=$PROJECT_ID

# Crear repositorio en Artifact Registry
Write-Host "📦 Creando repositorio en Artifact Registry..." -ForegroundColor Green
try {
    gcloud artifacts repositories create cloud-functions `
      --repository-format=docker `
      --location=$REGION `
      --description="Repositorio para Cloud Functions" `
      --project=$PROJECT_ID 2>&1 | Out-Null
} catch {
    Write-Host "⚠️  El repositorio ya existe, continuando..." -ForegroundColor Yellow
}

# Crear cuenta de servicio
Write-Host "👤 Creando cuenta de servicio..." -ForegroundColor Green
try {
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
      --display-name="GitHub Actions Service Account" `
      --project=$PROJECT_ID 2>&1 | Out-Null
} catch {
    Write-Host "⚠️  La cuenta de servicio ya existe, continuando..." -ForegroundColor Yellow
}

$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Asignar roles
Write-Host "🔐 Asignando roles a la cuenta de servicio..." -ForegroundColor Green
$roles = @(
    "roles/cloudfunctions.developer",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountUser",
    "roles/run.admin"
)

foreach ($role in $roles) {
    try {
        gcloud projects add-iam-policy-binding $PROJECT_ID `
          --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
          --role=$role `
          --condition=None 2>&1 | Out-Null
    } catch {
        # Ignorar errores si el binding ya existe
    }
}

# Crear clave JSON
Write-Host "🔑 Creando clave JSON para GitHub Actions..." -ForegroundColor Green
if (Test-Path "github-actions-key.json") {
    Write-Host "⚠️  La clave ya existe, se sobrescribirá..." -ForegroundColor Yellow
    Remove-Item "github-actions-key.json" -Force
}

gcloud iam service-accounts keys create github-actions-key.json `
  --iam-account=$SERVICE_ACCOUNT_EMAIL `
  --project=$PROJECT_ID

Write-Host ""
Write-Host "✅ Configuración completada!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Agrega el contenido de 'github-actions-key.json' como secreto GCP_SA_KEY en GitHub"
Write-Host "2. Agrega '$SERVICE_ACCOUNT_EMAIL' como secreto GCP_SA_EMAIL en GitHub"
Write-Host "3. Haz commit y push de tu código a GitHub"
Write-Host "4. El despliegue se ejecutará automáticamente"
Write-Host ""
Write-Host "⚠️  IMPORTANTE: No subas 'github-actions-key.json' a Git!" -ForegroundColor Red
Write-Host "   Está incluido en .gitignore por seguridad" -ForegroundColor Red

