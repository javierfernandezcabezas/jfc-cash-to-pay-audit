# Usar imagen base de Python para Cloud Functions
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /function

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la función
COPY main.py .

# Configurar variables de entorno
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 8080

# Comando para ejecutar la función usando Functions Framework
CMD exec functions-framework --target=jfc_cash_to_pay_audit --port=$PORT --host=0.0.0.0

