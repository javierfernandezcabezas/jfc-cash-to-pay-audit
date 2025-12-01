# jfc-cash-to-pay-audit

Función de Google Cloud Functions para procesar auditorías de cash-to-pay.

## 📋 Descripción

Esta función está diseñada para ejecutarse en Google Cloud Functions (Gen 2) usando contenedores Docker. Incluye integración con GitHub Actions para despliegues automáticos mediante CI/CD.

## 🏗️ Arquitectura

```
GitHub → GitHub Actions → Google Cloud (Artifact Registry) → Cloud Functions
```

- **GitHub**: Repositorio de código
- **GitHub Actions**: Pipeline de CI/CD
- **Artifact Registry**: Almacenamiento de imágenes Docker
- **Cloud Functions**: Ejecución de la función

## 🚀 Configuración Inicial

### Prerrequisitos

1. **Google Cloud Project**: `check-in-sf`
2. **Google Cloud CLI** instalado y configurado
3. **Cuenta de servicio** con permisos necesarios
4. **Repositorio GitHub** configurado

### 1. Habilitar APIs necesarias

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  --project=check-in-sf
```

### 2. Crear repositorio en Artifact Registry

```bash
gcloud artifacts repositories create cloud-functions \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repositorio para Cloud Functions" \
  --project=check-in-sf
```

### 3. Crear cuenta de servicio para GitHub Actions

```bash
# Crear cuenta de servicio
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account" \
  --project=check-in-sf

# Asignar roles necesarios
gcloud projects add-iam-policy-binding check-in-sf \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding check-in-sf \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding check-in-sf \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding check-in-sf \
  --member="serviceAccount:github-actions@check-in-sf.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Crear y descargar clave JSON
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@check-in-sf.iam.gserviceaccount.com \
  --project=check-in-sf
```

### 4. Configurar secretos en GitHub

Ve a tu repositorio en GitHub → Settings → Secrets and variables → Actions, y agrega:

- **`GCP_SA_KEY`**: Contenido completo del archivo `github-actions-key.json`
- **`GCP_SA_EMAIL`**: `github-actions@check-in-sf.iam.gserviceaccount.com`
- **`ARTIFACT_REGISTRY`** (opcional): `us-central1-docker.pkg.dev`

## 📦 Despliegue

### Despliegue automático (GitHub Actions)

El despliegue se ejecuta automáticamente cuando haces push a las ramas `main` o `master`:

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

También puedes ejecutarlo manualmente desde la pestaña "Actions" en GitHub.

### Despliegue manual

#### Opción 1: Usando gcloud CLI

```bash
# Construir y subir imagen
docker build -t us-central1-docker.pkg.dev/check-in-sf/cloud-functions/jfc-cash-to-pay-audit:latest .
docker push us-central1-docker.pkg.dev/check-in-sf/cloud-functions/jfc-cash-to-pay-audit:latest

# Desplegar función
gcloud functions deploy jfc-cash-to-pay-audit \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=jfc_cash_to_pay_audit \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --timeout=60s \
  --max-instances=10 \
  --docker-registry=artifact-registry \
  --docker-repository=cloud-functions \
  --project=check-in-sf
```

#### Opción 2: Usando Cloud Build

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_FUNCTION_NAME=jfc-cash-to-pay-audit,_REGION=us-central1 \
  --project=check-in-sf
```

## 🧪 Pruebas Locales

### Ejecutar con Functions Framework

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar localmente
functions-framework --target=jfc_cash_to_pay_audit --port=8080
```

### Probar la función

```bash
# GET request
curl http://localhost:8080

# POST request
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Ejecutar con Docker

```bash
# Construir imagen
docker build -t jfc-cash-to-pay-audit .

# Ejecutar contenedor
docker run -p 8080:8080 jfc-cash-to-pay-audit
```

## 📝 Estructura del Proyecto

```
jfc-cash-to-pay-audit/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Workflow de GitHub Actions
├── main.py                      # Código de la función
├── Dockerfile                   # Configuración del contenedor
├── requirements.txt             # Dependencias de Python
├── cloudbuild.yaml             # Configuración de Cloud Build (opcional)
├── .gcloudignore               # Archivos ignorados por gcloud
├── .dockerignore               # Archivos ignorados por Docker
├── .gitignore                  # Archivos ignorados por Git
└── README.md                    # Este archivo
```

## 🔧 Configuración

### Variables de entorno

Puedes configurar variables de entorno en Cloud Functions:

```bash
gcloud functions deploy jfc-cash-to-pay-audit \
  --gen2 \
  --region=us-central1 \
  --set-env-vars KEY1=value1,KEY2=value2 \
  --project=check-in-sf
```

### Ajustar recursos

Modifica los parámetros en el workflow o en el comando de despliegue:

- `--memory`: Memoria asignada (256MB, 512MB, 1GB, etc.)
- `--timeout`: Tiempo máximo de ejecución (60s, 300s, etc.)
- `--max-instances`: Número máximo de instancias concurrentes

## 🔐 Seguridad

- La función está configurada con `--allow-unauthenticated` para permitir acceso público
- Para restringir el acceso, elimina este flag y configura autenticación IAM
- Asegúrate de no exponer información sensible en el código
- Usa Secret Manager para credenciales y secretos

## 📊 Monitoreo

Puedes ver los logs de la función en:

```bash
gcloud functions logs read jfc-cash-to-pay-audit \
  --gen2 \
  --region=us-central1 \
  --project=check-in-sf
```

O en la consola de Google Cloud: Cloud Functions → jfc-cash-to-pay-audit → Logs

## 🐛 Troubleshooting

### Error: "Permission denied"
- Verifica que la cuenta de servicio tenga los roles necesarios
- Revisa los permisos en IAM

### Error: "Repository not found"
- Asegúrate de que el repositorio de Artifact Registry existe
- Verifica el nombre y la región

### Error: "Function deployment failed"
- Revisa los logs de Cloud Build
- Verifica que el Dockerfile y el código sean correctos
- Asegúrate de que el entry-point coincida con el nombre de la función

## 📚 Recursos

- [Documentación de Cloud Functions Gen 2](https://cloud.google.com/functions/docs/2nd-gen/overview)
- [GitHub Actions para Google Cloud](https://github.com/google-github-actions)
- [Functions Framework para Python](https://github.com/GoogleCloudPlatform/functions-framework-python)

## 📄 Licencia

Este proyecto es privado y pertenece a check-in-sf.

