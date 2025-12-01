# Script para crear el repositorio en GitHub usando la API
# Requiere un token de acceso personal de GitHub

$GITHUB_USER = "javierfernandezcabezas"
$REPO_NAME = "jfc-cash-to-pay-audit"

Write-Host "🔧 Creando repositorio en GitHub" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar token de GitHub
Write-Host "🔑 Necesitas un token de acceso personal de GitHub" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para crear un token:" -ForegroundColor Cyan
Write-Host "1. Ve a: https://github.com/settings/tokens" -ForegroundColor White
Write-Host "2. Click en 'Generate new token (classic)'" -ForegroundColor White
Write-Host "3. Dale un nombre (ej: 'jfc-cash-to-pay-audit')" -ForegroundColor White
Write-Host "4. Selecciona el scope: 'repo' (todos los permisos)" -ForegroundColor White
Write-Host "5. Click en 'Generate token'" -ForegroundColor White
Write-Host "6. COPIA el token (solo se muestra una vez)" -ForegroundColor White
Write-Host ""

$token = Read-Host "Ingresa tu token de GitHub" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
$GITHUB_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

if ([string]::IsNullOrWhiteSpace($GITHUB_TOKEN)) {
    Write-Host "❌ Token no puede estar vacío" -ForegroundColor Red
    exit 1
}

# Headers para la API de GitHub
$headers = @{
    "Authorization" = "token $GITHUB_TOKEN"
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "PowerShell-Script"
}

# Crear repositorio
Write-Host "`n📦 Creando repositorio en GitHub..." -ForegroundColor Green

$body = @{
    name = $REPO_NAME
    description = "Google Cloud Function para auditorías cash-to-pay con CI/CD"
    private = $false
    auto_init = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" `
        -Method Post `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "✅ Repositorio creado exitosamente!" -ForegroundColor Green
    Write-Host "   URL: $($response.html_url)" -ForegroundColor Cyan
    Write-Host "   Clone URL: $($response.clone_url)" -ForegroundColor Cyan
    
    # Configurar remote
    Write-Host "`n🔗 Configurando conexión local..." -ForegroundColor Green
    
    $remoteUrl = $response.clone_url
    $remoteUrlWithToken = $remoteUrl -replace "https://", "https://$GITHUB_TOKEN@"
    
    # Verificar si ya existe el remote
    $existingRemote = git remote get-url origin 2>&1
    if ($LASTEXITCODE -eq 0) {
        git remote set-url origin $remoteUrlWithToken
        Write-Host "✅ Remote 'origin' actualizado" -ForegroundColor Green
    } else {
        git remote add origin $remoteUrlWithToken
        Write-Host "✅ Remote 'origin' agregado" -ForegroundColor Green
    }
    
    # Cambiar a rama main
    git branch -M main
    
    # Hacer commit si hay cambios
    $status = git status --porcelain
    if ($status) {
        Write-Host "`n💾 Creando commit inicial..." -ForegroundColor Green
        git add .
        git commit -m "Initial commit: Cloud Function setup with CI/CD"
        Write-Host "✅ Commit creado" -ForegroundColor Green
    }
    
    # Push a GitHub
    Write-Host "`n🚀 Subiendo código a GitHub..." -ForegroundColor Green
    git push -u origin main
    
    Write-Host "`n✅ ¡Repositorio creado y código subido exitosamente!" -ForegroundColor Green
    Write-Host "`n📋 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "1. Ejecuta .\setup.ps1 para configurar Google Cloud" -ForegroundColor White
    Write-Host "2. Ve a tu repositorio: $($response.html_url)" -ForegroundColor White
    Write-Host "3. Ve a Settings → Secrets and variables → Actions" -ForegroundColor White
    Write-Host "4. Agrega GCP_SA_KEY (contenido de github-actions-key.json)" -ForegroundColor White
    Write-Host "5. Agrega GCP_SA_EMAIL (github-actions@check-in-sf.iam.gserviceaccount.com)" -ForegroundColor White
    Write-Host "`n💡 El siguiente push a main desplegará automáticamente" -ForegroundColor Cyan
    
} catch {
    $errorDetails = $_.ErrorDetails.Message
    try {
        $errorJson = $errorDetails | ConvertFrom-Json
        if ($errorJson.message -like "*already exists*") {
            Write-Host "⚠️  El repositorio ya existe en GitHub" -ForegroundColor Yellow
            Write-Host "   Conectando con el repositorio existente..." -ForegroundColor Cyan
            
            $repoUrl = "https://github.com/$GITHUB_USER/$REPO_NAME.git"
            $repoUrlWithToken = $repoUrl -replace "https://", "https://$GITHUB_TOKEN@"
            
            $existingRemote = git remote get-url origin 2>&1
            if ($LASTEXITCODE -eq 0) {
                git remote set-url origin $repoUrlWithToken
            } else {
                git remote add origin $repoUrlWithToken
            }
            
            git branch -M main
            git add .
            git commit -m "Initial commit: Cloud Function setup with CI/CD" 2>&1 | Out-Null
            git push -u origin main
            
            Write-Host "✅ Código subido al repositorio existente" -ForegroundColor Green
        } else {
            Write-Host "❌ Error: $($errorJson.message)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error creando repositorio: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Detalles: $errorDetails" -ForegroundColor Red
    }
}

