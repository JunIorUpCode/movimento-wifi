# WiFiSense Auth Service Dockerfile
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY services/auth-service/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do serviço
COPY services/auth-service/ .

# Copiar módulo shared
COPY shared/ /shared/

# Adicionar shared ao PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/shared"

# Expor porta
EXPOSE 8000

# Comando para iniciar o serviço
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
