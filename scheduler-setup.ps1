# Script PowerShell para configurar Cloud Scheduler

$PROJECT_ID = "check-in-sf"
$SERVICE_NAME = "jfc-cash-to-pay-audit"
$REGION = "us-central1"

Write-Host "Obteniendo URL del servicio Cloud Run..." -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
  --region=$REGION `
  --format="value(status.url)" `
  --project=$PROJECT_ID

Write-Host "URL del servicio: $SERVICE_URL" -ForegroundColor Green

Write-Host "`nConfigurando Cloud Scheduler..." -ForegroundColor Cyan

# Intentar crear el job
try {
    gcloud scheduler jobs create http jfc-cash-to-pay-audit-daily `
      --location=$REGION `
      --schedule="0 22 * * *" `
      --uri="$SERVICE_URL`?query_type=invoice_summary" `
      --http-method=GET `
      --time-zone="Europe/Madrid" `
      --description="Ejecuta jfc-cash-to-pay-audit diariamente a las 10 PM" `
      --project=$PROJECT_ID 2>&1 | Out-Null
    
    Write-Host "Job creado exitosamente" -ForegroundColor Green
} catch {
    Write-Host "El job ya existe, actualizando..." -ForegroundColor Yellow
    
    gcloud scheduler jobs update http jfc-cash-to-pay-audit-daily `
      --location=$REGION `
      --schedule="0 22 * * *" `
      --uri="$SERVICE_URL`?query_type=invoice_summary" `
      --http-method=GET `
      --time-zone="Europe/Madrid" `
      --project=$PROJECT_ID
}

Write-Host "`nCloud Scheduler configurado exitosamente!" -ForegroundColor Green
Write-Host "El servicio se ejecutara diariamente a las 10 PM (22:00)" -ForegroundColor Cyan

