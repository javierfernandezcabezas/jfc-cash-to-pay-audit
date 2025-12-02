#!/bin/bash
# Script para configurar Cloud Scheduler que ejecute la función diariamente a las 10 PM

PROJECT_ID="check-in-sf"
SERVICE_NAME="jfc-cash-to-pay-audit"
REGION="us-central1"
SERVICE_URL="https://jfc-cash-to-pay-audit-432377064948.us-central1.run.app"

# Obtener la URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(status.url)" \
  --project=$PROJECT_ID)

echo "Configurando Cloud Scheduler..."
echo "URL del servicio: $SERVICE_URL"

# Crear job de Cloud Scheduler
gcloud scheduler jobs create http jfc-cash-to-pay-audit-daily \
  --location=$REGION \
  --schedule="0 22 * * *" \
  --uri="$SERVICE_URL?query_type=invoice_summary" \
  --http-method=GET \
  --time-zone="Europe/Madrid" \
  --description="Ejecuta jfc-cash-to-pay-audit diariamente a las 10 PM" \
  --project=$PROJECT_ID \
  || echo "El job ya existe, actualizando..."

# Si el job ya existe, actualizarlo
gcloud scheduler jobs update http jfc-cash-to-pay-audit-daily \
  --location=$REGION \
  --schedule="0 22 * * *" \
  --uri="$SERVICE_URL?query_type=invoice_summary" \
  --http-method=GET \
  --time-zone="Europe/Madrid" \
  --project=$PROJECT_ID

echo "Cloud Scheduler configurado exitosamente"
echo "El servicio se ejecutará diariamente a las 10 PM (22:00)"

