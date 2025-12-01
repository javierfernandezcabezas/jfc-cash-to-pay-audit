# Solución Definitiva para el Error de Permisos

## Error Actual

La cuenta de servicio `github-actions@check-in-sf.iam.gserviceaccount.com` no tiene permisos para:
- `artifactregistry.repositories.uploadArtifacts` - Subir artefactos

## Solución: Agregar Permisos

**IMPORTANTE**: Necesitas permisos de administrador en el proyecto `check-in-sf` para ejecutar estos comandos.

### Opción 1: Ejecutar el Script

```powershell
.\agregar-permisos.ps1
```

### Opción 2: Comandos Manuales

Ejecuta estos comandos en PowerShell (uno por uno):

```powershell
# 1. Permiso para escribir en Artifact Registry (CRÍTICO)
gcloud projects add-iam-policy-binding check-in-sf `
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --role="roles/artifactregistry.writer"

# 2. Permiso para administrar Artifact Registry (opcional pero recomendado)
gcloud projects add-iam-policy-binding check-in-sf `
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --role="roles/artifactregistry.admin"
```

### Opción 3: Si NO Tienes Permisos de Administrador

Pide a un administrador del proyecto que ejecute los comandos de la Opción 2.

## Verificar que los Permisos se Agregaron

Después de ejecutar los comandos, verifica:

```powershell
gcloud projects get-iam-policy check-in-sf `
  --flatten="bindings[].members" `
  --filter="bindings.members:github-actions@check-in-sf.iam.gserviceaccount.com" `
  --format="table(bindings.role)"
```

Deberías ver al menos:
- `roles/artifactregistry.writer`
- `roles/cloudfunctions.developer`
- `roles/iam.serviceAccountUser`
- `roles/run.admin`

## Después de Agregar Permisos

1. Ve a GitHub Actions: https://github.com/javierfernandezcabezas/jfc-cash-to-pay-audit/actions
2. Ejecuta el workflow de nuevo (puedes hacer un nuevo push o ejecutarlo manualmente)
3. El workflow debería funcionar correctamente ahora

## Nota sobre el Repositorio

El repositorio `cloud-functions` ya existe en Artifact Registry, así que no necesitas crearlo. El workflow ahora solo verifica que existe y luego sube la imagen.

