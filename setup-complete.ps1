# Script maestro para configurar todo el entorno
# Instala herramientas, configura GitHub y Google Cloud

$ErrorActionPreference = "Stop"

Write-Host "🚀 Configuración Completa: Cursor → GitHub → Google Cloud" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si estamos ejecutando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Paso 1: Verificar/Instalar Git
Write-Host "📦 Paso 1: Verificando Git..." -ForegroundColor Green
try {
    $gitVersion = git --version 2>&1
    Write-Host "   ✅ Git ya está instalado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Git no está instalado" -ForegroundColor Yellow
    if ($isAdmin) {
        Write-Host "   📥 Instalando Git..." -ForegroundColor Cyan
        try {
            winget install --id Git.Git -e --silent
            Write-Host "   ✅ Git instalado. Por favor reinicia PowerShell y ejecuta este script nuevamente." -ForegroundColor Green
            exit 0
        } catch {
            Write-Host "   ❌ Error instalando Git. Por favor instálalo manualmente desde: https://git-scm.com/download/win" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   ❌ Git no está instalado y no tienes permisos de administrador." -ForegroundColor Red
        Write-Host "   Por favor ejecuta PowerShell como Administrador o instala Git manualmente." -ForegroundColor Yellow
        Write-Host "   Descarga desde: https://git-scm.com/download/win" -ForegroundColor Yellow
        exit 1
    }
}

# Paso 2: Verificar/Instalar Google Cloud SDK
Write-Host "`n📦 Paso 2: Verificando Google Cloud SDK..." -ForegroundColor Green
try {
    $gcloudVersion = gcloud --version 2>&1 | Select-Object -First 1
    Write-Host "   ✅ Google Cloud SDK ya está instalado" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Google Cloud SDK no está instalado" -ForegroundColor Yellow
    if ($isAdmin) {
        Write-Host "   📥 Instalando Google Cloud SDK..." -ForegroundColor Cyan
        try {
            winget install --id Google.CloudSDK -e --silent
            Write-Host "   ✅ Google Cloud SDK instalado. Por favor reinicia PowerShell y ejecuta este script nuevamente." -ForegroundColor Green
            exit 0
        } catch {
            Write-Host "   ❌ Error instalando Google Cloud SDK. Por favor instálalo manualmente." -ForegroundColor Red
            Write-Host "   Descarga desde: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Google Cloud SDK no está instalado." -ForegroundColor Yellow
        Write-Host "   Puedes instalarlo después desde: https://cloud.google.com/sdk/docs/install" -ForegroundColor Cyan
    }
}

# Paso 3: Configurar GitHub
Write-Host "`n📦 Paso 3: Configurando GitHub..." -ForegroundColor Green
if (Test-Path "setup-github.ps1") {
    Write-Host "   Ejecutando script de configuración de GitHub..." -ForegroundColor Cyan
    & .\setup-github.ps1
} else {
    Write-Host "   ⚠️  Script setup-github.ps1 no encontrado" -ForegroundColor Yellow
}

# Paso 4: Configurar Google Cloud
Write-Host "`n📦 Paso 4: Configurando Google Cloud..." -ForegroundColor Green
if (Test-Path "setup.ps1") {
    Write-Host "   Ejecutando script de configuración de Google Cloud..." -ForegroundColor Cyan
    & .\setup.ps1
} else {
    Write-Host "   ⚠️  Script setup.ps1 no encontrado" -ForegroundColor Yellow
}

Write-Host "`n✅ Configuración completada!" -ForegroundColor Green
Write-Host "`n📋 Resumen de próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Ve a tu repositorio en GitHub: https://github.com/javierfernandezcabezas/jfc-cash-to-pay-audit" -ForegroundColor White
Write-Host "2. Settings → Secrets and variables → Actions" -ForegroundColor White
Write-Host "3. Agrega GCP_SA_KEY (contenido de github-actions-key.json)" -ForegroundColor White
Write-Host "4. Agrega GCP_SA_EMAIL (github-actions@check-in-sf.iam.gserviceaccount.com)" -ForegroundColor White
Write-Host "5. El siguiente push a main/master desplegará automáticamente" -ForegroundColor White

