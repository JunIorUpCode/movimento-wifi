#!/bin/bash
# generate_secrets.sh — Gera segredos criptograficamente seguros para produção
# Uso: bash scripts/generate_secrets.sh > .env.production

set -euo pipefail

# Gera string aleatória de N bytes em base64 URL-safe
rand_b64() { python3 -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes($1)).decode().rstrip('='))"; }
rand_hex()  { python3 -c "import secrets; print(secrets.token_hex($1))"; }
rand_fernet(){ python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || rand_b64 32; }

cat <<EOF
# WiFiSense SaaS — Configuração de PRODUÇÃO
# Gerado em: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# NUNCA commitar este arquivo no git!

# ── Domínio ──────────────────────────────────────────────────────────────────
DOMAIN=seu-dominio.com

# ── Banco de dados ────────────────────────────────────────────────────────────
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=$(rand_hex 24)
DATABASE_NAME=wifisense_saas

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$(rand_hex 24)

# ── RabbitMQ ──────────────────────────────────────────────────────────────────
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=wifisense
RABBITMQ_PASSWORD=$(rand_hex 24)

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY=$(rand_b64 48)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ── Criptografia ──────────────────────────────────────────────────────────────
ENCRYPTION_KEY=$(rand_fernet)

# ── Segurança ─────────────────────────────────────────────────────────────────
BCRYPT_ROUNDS=12
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# ── Grafana ───────────────────────────────────────────────────────────────────
GRAFANA_ADMIN_PASSWORD=$(rand_b64 24)

# ── Stripe (substitua pela chave real de produção) ────────────────────────────
STRIPE_API_KEY=sk_live_SUBSTITUA_PELA_CHAVE_REAL

# ── Notificações (preencha conforme necessário) ───────────────────────────────
TELEGRAM_BOT_TOKEN=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# ── Docker images ─────────────────────────────────────────────────────────────
REGISTRY=ghcr.io
IMAGE_PREFIX=wifisense/wifisense
IMAGE_TAG=latest

# ── Aplicação ─────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
DEBUG=false
EOF
