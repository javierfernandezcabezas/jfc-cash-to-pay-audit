# Script para configurar permisos de BigQuery en el proyecto workflows-and-automations-1

$SOURCE_PROJECT = "workflows-and-automations-1"
$SERVICE_ACCOUNT = "github-actions@check-in-sf.iam.gserviceaccount.com"

Write-Host "Configurando permisos de BigQuery" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "IMPORTANTE: Necesitas permisos de administrador en el proyecto:" -ForegroundColor Yellow
Write-Host "  $SOURCE_PROJECT" -ForegroundColor White
Write-Host ""

# Verificar que estás autenticado
Write-Host "Verificando autenticacion..." -ForegroundColor Green
$currentAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)"
Write-Host "Cuenta activa: $currentAccount" -ForegroundColor Gray
Write-Host ""

# Verificar permisos actuales
Write-Host "Verificando permisos actuales..." -ForegroundColor Green
try {
    $currentRoles = gcloud projects get-iam-policy $SOURCE_PROJECT `
      --flatten="bindings[].members" `
      --filter="bindings.members:$SERVICE_ACCOUNT" `
      --format="table(bindings.role)" 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $currentRoles) {
        Write-Host "Permisos actuales:" -ForegroundColor Cyan
        Write-Host $currentRoles -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host "No se pudieron verificar permisos actuales" -ForegroundColor Yellow
}

# Agregar permisos
Write-Host "Agregando permisos..." -ForegroundColor Green
Write-Host ""

$roles = @(
    @{Name="BigQuery Data Viewer"; Role="roles/bigquery.dataViewer"},
    @{Name="BigQuery Job User"; Role="roles/bigquery.jobUser"},
    @{Name="BigQuery Data Editor (opcional)"; Role="roles/bigquery.dataEditor"}
)

foreach ($roleInfo in $roles) {
    Write-Host "Agregando $($roleInfo.Name)..." -ForegroundColor Yellow
    try {
        gcloud projects add-iam-policy-binding $SOURCE_PROJECT `
          --member="serviceAccount:$SERVICE_ACCOUNT" `
          --role=$roleInfo.Role 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK: $($roleInfo.Name) agregado" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: No se pudo agregar $($roleInfo.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Verificando permisos finales..." -ForegroundColor Green
$finalRoles = gcloud projects get-iam-policy $SOURCE_PROJECT `
  --flatten="bindings[].members" `
  --filter="bindings.members:$SERVICE_ACCOUNT" `
  --format="table(bindings.role)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Permisos configurados:" -ForegroundColor Cyan
    Write-Host $finalRoles -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "ERROR: No tienes permisos para modificar IAM en el proyecto $SOURCE_PROJECT" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solucion:" -ForegroundColor Yellow
    Write-Host "1. Pide a un administrador del proyecto que ejecute estos comandos:" -ForegroundColor White
    Write-Host ""
    Write-Host "   gcloud projects add-iam-policy-binding $SOURCE_PROJECT \" -ForegroundColor Gray
    Write-Host "     --member=`"serviceAccount:$SERVICE_ACCOUNT`" \" -ForegroundColor Gray
    Write-Host "     --role=`"roles/bigquery.dataViewer`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   gcloud projects add-iam-policy-binding $SOURCE_PROJECT \" -ForegroundColor Gray
    Write-Host "     --member=`"serviceAccount:$SERVICE_ACCOUNT`" \" -ForegroundColor Gray
    Write-Host "     --role=`"roles/bigquery.jobUser`"" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Configuracion completada!" -ForegroundColor Green

