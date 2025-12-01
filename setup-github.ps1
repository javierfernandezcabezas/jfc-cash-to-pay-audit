# Script para configurar GitHub y conectar con el repositorio
# Requiere: Git instalado y token de GitHub

$ErrorActionPreference = "Stop"

$GITHUB_USER = "javierfernandezcabezas"
$REPO_NAME = "jfc-cash-to-pay-audit"
$GITHUB_TOKEN = $env:GITHUB_TOKEN

Write-Host "🔧 Configurando conexión con GitHub" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Verificar Git
Write-Host "`n📋 Verificando Git..." -ForegroundColor Green
try {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git no está instalado" -ForegroundColor Red
    Write-Host "`nPor favor instala Git desde: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "O ejecuta: winget install Git.Git" -ForegroundColor Yellow
    exit 1
}

# Solicitar token de GitHub si no está en variables de entorno
if (-not $GITHUB_TOKEN) {
    Write-Host "`n🔑 Necesitas un token de acceso personal de GitHub" -ForegroundColor Yellow
    Write-Host "1. Ve a: https://github.com/settings/tokens" -ForegroundColor Cyan
    Write-Host "2. Click en 'Generate new token (classic)'" -ForegroundColor Cyan
    Write-Host "3. Selecciona los scopes: repo (todos los permisos)" -ForegroundColor Cyan
    Write-Host "4. Copia el token generado" -ForegroundColor Cyan
    Write-Host ""
    $GITHUB_TOKEN = Read-Host "Ingresa tu token de GitHub" -AsSecureString
    $GITHUB_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($GITHUB_TOKEN)
    )
}

# Crear repositorio en GitHub usando API
Write-Host "`n📦 Creando repositorio en GitHub..." -ForegroundColor Green

$headers = @{
    "Authorization" = "token $GITHUB_TOKEN"
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "PowerShell"
}

$body = @{
    name = $REPO_NAME
    description = "Google Cloud Function para auditorías cash-to-pay"
    private = $false
    auto_init = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" `
        -Method Post `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "✅ Repositorio creado: $($response.html_url)" -ForegroundColor Green
} catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($errorDetails.message -like "*already exists*") {
        Write-Host "⚠️  El repositorio ya existe, continuando..." -ForegroundColor Yellow
    } else {
        Write-Host "❌ Error creando repositorio: $($_.Exception.Message)" -ForegroundColor Red
        if ($errorDetails) {
            Write-Host "   Detalles: $($errorDetails.message)" -ForegroundColor Red
        }
        exit 1
    }
}

# Inicializar git local si no está inicializado
Write-Host "`n📂 Inicializando repositorio local..." -ForegroundColor Green
if (-not (Test-Path ".git")) {
    git init
    Write-Host "✅ Repositorio Git inicializado" -ForegroundColor Green
} else {
    Write-Host "✅ Repositorio Git ya existe" -ForegroundColor Green
}

# Configurar usuario de Git si no está configurado
Write-Host "`n👤 Configurando usuario de Git..." -ForegroundColor Green
$currentUser = git config user.name 2>&1
if ($LASTEXITCODE -ne 0 -or -not $currentUser) {
    git config user.name $GITHUB_USER
    Write-Host "✅ Usuario configurado: $GITHUB_USER" -ForegroundColor Green
}

$currentEmail = git config user.email 2>&1
if ($LASTEXITCODE -ne 0 -or -not $currentEmail) {
    $email = Read-Host "Ingresa tu email de GitHub (o presiona Enter para usar $GITHUB_USER@users.noreply.github.com)"
    if ([string]::IsNullOrWhiteSpace($email)) {
        $email = "$GITHUB_USER@users.noreply.github.com"
    }
    git config user.email $email
    Write-Host "✅ Email configurado: $email" -ForegroundColor Green
}

# Agregar remote
Write-Host "`n🔗 Conectando con GitHub..." -ForegroundColor Green
$repoUrl = "https://github.com/$GITHUB_USER/$REPO_NAME.git"
$currentRemote = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    git remote add origin $repoUrl
    Write-Host "✅ Remote 'origin' agregado: $repoUrl" -ForegroundColor Green
} else {
    git remote set-url origin $repoUrl
    Write-Host "✅ Remote 'origin' actualizado: $repoUrl" -ForegroundColor Green
}

# Agregar todos los archivos
Write-Host "`n📝 Preparando archivos para commit..." -ForegroundColor Green
git add .

# Hacer commit inicial
Write-Host "`n💾 Creando commit inicial..." -ForegroundColor Green
$commitMessage = "Initial commit: Cloud Function setup with CI/CD"
try {
    git commit -m $commitMessage
    Write-Host "✅ Commit creado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  No hay cambios para commitear o ya existe un commit" -ForegroundColor Yellow
}

# Push a GitHub
Write-Host "`n🚀 Subiendo código a GitHub..." -ForegroundColor Green
Write-Host "   (Esto puede pedirte credenciales)" -ForegroundColor Yellow

# Configurar credenciales helper
git config credential.helper store

# Intentar push
try {
    git branch -M main
    git push -u origin main
    Write-Host "✅ Código subido exitosamente a GitHub!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error en push. Puede que necesites autenticarte manualmente." -ForegroundColor Yellow
    Write-Host "`nPara hacer push manualmente:" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host "`nO usa tu token como contraseña cuando se solicite" -ForegroundColor Yellow
}

Write-Host "`n✅ Configuración de GitHub completada!" -ForegroundColor Green
Write-Host "`n📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Ve a: https://github.com/$GITHUB_USER/$REPO_NAME" -ForegroundColor White
Write-Host "2. Ve a Settings → Secrets and variables → Actions" -ForegroundColor White
Write-Host "3. Agrega los secretos necesarios (ver README.md)" -ForegroundColor White
Write-Host "4. Ejecuta .\setup.ps1 para configurar Google Cloud" -ForegroundColor White

