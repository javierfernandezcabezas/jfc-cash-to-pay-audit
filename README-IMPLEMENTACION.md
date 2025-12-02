# Implementación: jfc-cash-to-pay-audit

## Funcionalidad

Esta función ejecuta queries complejas de BigQuery sobre el dataset `amn_op_automatic_invoicing` y:
1. Ejecuta las queries según parámetros
2. Guarda los resultados en tablas de BigQuery
3. Exporta automáticamente a Google Sheets (opcional)
4. Se ejecuta diariamente a las 10 PM mediante Cloud Scheduler

## Queries Implementadas

### Queries Básicas
- `get_partner_id_by_contract`: Obtiene partner_id por cd_contract
- `get_contract_by_partner`: Obtiene cd_contract por partner_id
- `get_contracts_by_partner`: Obtiene todos los cd_contracts de un partner
- `get_account_name`: Obtiene nombre de cuenta por partner_id

### Queries Complejas
- `get_invoice_summary`: Query RESUMEN INVOICES con todas las CTEs
- `get_settlement_summary`: Query RESUMEN SETTLEMENT con todas las CTEs

## Configuración

### 1. Permisos de BigQuery

La cuenta de servicio necesita permisos en el proyecto `workflows-and-automations-1`:

```bash
gcloud projects add-iam-policy-binding workflows-and-automations-1 \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding workflows-and-automations-1 \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### 2. Configurar Cloud Scheduler

Ejecuta el script para configurar la ejecución diaria:

```powershell
.\scheduler-setup.ps1
```

Esto creará un job que ejecuta la función diariamente a las 10 PM (22:00).

### 3. Configurar Exportación a Google Sheets (Opcional)

Para exportar automáticamente a Google Sheets:

1. Crea una hoja de cálculo en Google Sheets
2. Comparte la hoja con la cuenta de servicio: `github-actions@check-in-sf.iam.gserviceaccount.com`
3. Obtén el ID de la hoja (está en la URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/...`)
4. Configura variables de entorno en Cloud Run:

```bash
gcloud run services update jfc-cash-to-pay-audit \
  --region=us-central1 \
  --set-env-vars="GOOGLE_SHEETS_ID=tu_spreadsheet_id" \
  --project=check-in-sf
```

## Uso

### Ejecución Manual

Puedes ejecutar la función manualmente haciendo una petición HTTP:

```bash
# Invoice summary
curl "https://jfc-cash-to-pay-audit-432377064948.us-central1.run.app?query_type=invoice_summary"

# Settlement summary
curl "https://jfc-cash-to-pay-audit-432377064948.us-central1.run.app?query_type=settlement_summary"

# Con filtro por partner
curl "https://jfc-cash-to-pay-audit-432377064948.us-central1.run.app?query_type=invoice_summary&id_partner=12345"
```

### Ejecución Automática

El Cloud Scheduler ejecuta automáticamente la función diariamente a las 10 PM.

## Resultados

Los resultados se guardan en BigQuery en tablas con formato:
- `invoice_summary_YYYYMMDD`
- `settlement_summary_YYYYMMDD`

Si está configurado, también se exportan a Google Sheets en la hoja especificada.

## Estructura del Proyecto

```
jfc-cash-to-pay-audit/
├── main.py                    # Función principal con todas las queries
├── export_to_sheets.py        # Módulo para exportar a Google Sheets
├── Dockerfile                 # Contenedor Docker
├── requirements.txt           # Dependencias Python
├── scheduler-setup.ps1        # Script para configurar Cloud Scheduler
└── .github/workflows/         # CI/CD con GitHub Actions
```

## Próximos Pasos

1. ✅ Esperar a que termine el despliegue del workflow
2. ✅ Ejecutar `.\scheduler-setup.ps1` para configurar el scheduler
3. ⏳ Configurar permisos de BigQuery en el proyecto `workflows-and-automations-1`
4. ⏳ (Opcional) Configurar exportación a Google Sheets

