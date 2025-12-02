# Solución: Permisos de BigQuery

## Problema

No tienes permisos de administrador en el proyecto `workflows-and-automations-1` para agregar permisos IAM.

## Solución

Necesitas que un **administrador del proyecto `workflows-and-automations-1`** ejecute estos comandos:

### Opción 1: Comandos Individuales

```powershell
# 1. BigQuery Data Viewer (para leer datos)
gcloud projects add-iam-policy-binding workflows-and-automations-1 `
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --role="roles/bigquery.dataViewer"

# 2. BigQuery Job User (para ejecutar queries)
gcloud projects add-iam-policy-binding workflows-and-automations-1 `
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --role="roles/bigquery.jobUser"

# 3. BigQuery Data Editor (opcional, para escribir resultados)
gcloud projects add-iam-policy-binding workflows-and-automations-1 `
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --role="roles/bigquery.dataEditor"
```

### Opción 2: Script para el Administrador

Copia este script y dáselo al administrador del proyecto:

```powershell
# configurar-bigquery-permisos-admin.ps1
$SOURCE_PROJECT = "workflows-and-automations-1"
$SERVICE_ACCOUNT = "github-actions@check-in-sf.iam.gserviceaccount.com"

Write-Host "Configurando permisos de BigQuery para $SERVICE_ACCOUNT" -ForegroundColor Cyan

$roles = @(
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataEditor"
)

foreach ($role in $roles) {
    Write-Host "Agregando $role..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding $SOURCE_PROJECT `
      --member="serviceAccount:$SERVICE_ACCOUNT" `
      --role=$role
}

Write-Host "Permisos configurados exitosamente!" -ForegroundColor Green
```

## Verificar Permisos

Después de que el administrador ejecute los comandos, puedes verificar:

```powershell
gcloud projects get-iam-policy workflows-and-automations-1 `
  --flatten="bindings[].members" `
  --filter="bindings.members:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --format="table(bindings.role)"
```

Deberías ver:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`
- `roles/bigquery.dataEditor`

## Alternativa: Usar Application Default Credentials

Si no puedes obtener permisos en `workflows-and-automations-1`, puedes:

1. Usar tu propia cuenta de usuario (javier.fernandez.cabezas@feverup.com) que ya tiene acceso
2. Modificar el código para usar Application Default Credentials en lugar de la cuenta de servicio

¿Quieres que modifique el código para usar tu cuenta de usuario en lugar de la cuenta de servicio?

