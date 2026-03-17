# WiFiSense Tenant Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY services/tenant-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/tenant-service/ .
COPY shared/ /shared/

ENV PYTHONPATH="${PYTHONPATH}:/shared"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
