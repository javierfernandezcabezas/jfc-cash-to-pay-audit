# 🚀 Guía Rápida de Configuración

## Paso 1: Crear Token de GitHub

1. Ve a: **https://github.com/settings/tokens**
2. Click en **"Generate new token (classic)"**
3. Dale un nombre: `jfc-cash-to-pay-audit`
4. Selecciona el scope: **`repo`** (todos los permisos de repositorio)
5. Click en **"Generate token"**
6. **COPIA el token inmediatamente** (solo se muestra una vez)

## Paso 2: Crear Repositorio en GitHub

Ejecuta este comando en PowerShell:

```powershell
.\create-github-repo.ps1
```

Cuando te pida el token, pégalo y presiona Enter.

## Paso 3: Configurar Google Cloud

Ejecuta este comando:

```powershell
.\setup.ps1
```

Esto creará:
- Repositorio en Artifact Registry
- Cuenta de servicio para GitHub Actions
- Archivo `github-actions-key.json` con las credenciales

## Paso 4: Configurar Secretos en GitHub

1. Ve a tu repositorio: **https://github.com/javierfernandezcabezas/jfc-cash-to-pay-audit**
2. Click en **Settings** → **Secrets and variables** → **Actions**
3. Click en **"New repository secret"**
4. Agrega estos secretos:

   **GCP_SA_KEY:**
   - Abre el archivo `github-actions-key.json` (creado en el paso 3)
   - Copia TODO el contenido
   - Pégalo como valor del secreto

   **GCP_SA_EMAIL:**
   - Valor: `github-actions@check-in-sf.iam.gserviceaccount.com`

## Paso 5: ¡Listo!

El siguiente push a `main` o `master` desplegará automáticamente tu función a Google Cloud Functions.

Para hacer un cambio y probar:

```powershell
# Hacer un cambio
# ... edita algún archivo ...

# Commit y push
git add .
git commit -m "Test deployment"
git push origin main
```

Ve a la pestaña **Actions** en GitHub para ver el progreso del despliegue.

## 🔗 Enlaces Útiles

- Repositorio: https://github.com/javierfernandezcabezas/jfc-cash-to-pay-audit
- GitHub Tokens: https://github.com/settings/tokens
- Google Cloud Console: https://console.cloud.google.com/
- Cloud Functions: https://console.cloud.google.com/functions

