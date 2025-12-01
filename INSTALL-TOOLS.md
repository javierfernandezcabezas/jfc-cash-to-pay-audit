# Guía de Instalación de Herramientas

Para conectar Cursor, GitHub y Google Cloud, necesitas instalar algunas herramientas.

## 🔧 Herramientas Requeridas

### 1. Git

**Opción A: Usando Winget (Recomendado)**
```powershell
winget install Git.Git
```

**Opción B: Descarga Manual**
1. Ve a: https://git-scm.com/download/win
2. Descarga e instala Git para Windows
3. Reinicia PowerShell después de la instalación

**Verificar instalación:**
```powershell
git --version
```

### 2. Google Cloud SDK

**Opción A: Usando Winget**
```powershell
winget install Google.CloudSDK
```

**Opción B: Descarga Manual**
1. Ve a: https://cloud.google.com/sdk/docs/install
2. Descarga e instala Google Cloud SDK
3. Ejecuta `gcloud init` para configurar

**Verificar instalación:**
```powershell
gcloud --version
```

### 3. GitHub CLI (Opcional pero recomendado)

**Opción A: Usando Winget**
```powershell
winget install GitHub.cli
```

**Opción B: Descarga Manual**
1. Ve a: https://cli.github.com/
2. Descarga e instala GitHub CLI

**Verificar instalación:**
```powershell
gh --version
```

## 🚀 Instalación Rápida (Todo en uno)

Ejecuta este comando en PowerShell como Administrador:

```powershell
winget install Git.Git Google.CloudSDK GitHub.cli
```

Luego reinicia PowerShell y verifica:

```powershell
git --version
gcloud --version
gh --version
```

## 📝 Configuración Inicial

### Configurar Git
```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@example.com"
```

### Autenticar con Google Cloud
```powershell
gcloud auth login
gcloud config set project check-in-sf
```

### Autenticar con GitHub (si instalaste GitHub CLI)
```powershell
gh auth login
```

## ✅ Verificación Completa

Ejecuta este script para verificar que todo está instalado:

```powershell
Write-Host "Verificando herramientas..." -ForegroundColor Cyan
Write-Host "Git: " -NoNewline; git --version 2>&1
Write-Host "GCloud: " -NoNewline; gcloud --version 2>&1 | Select-Object -First 1
Write-Host "GitHub CLI: " -NoNewline; gh --version 2>&1 | Select-Object -First 1
```

