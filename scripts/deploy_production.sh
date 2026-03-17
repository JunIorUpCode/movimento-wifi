#!/bin/bash
# deploy_production.sh — Deploy completo do WiFiSense SaaS em produção
#
# Uso: sudo bash scripts/deploy_production.sh --domain wifisense.example.com
# Pré-requisitos: Ubuntu 22.04+, Docker + Docker Compose v2, certbot

set -euo pipefail

DOMAIN=""
EMAIL=""
SKIP_SSL=false
SKIP_MIGRATIONS=false

log()  { echo -e "\033[1;32m[DEPLOY]\033[0m $*"; }
warn() { echo -e "\033[1;33m[AVISO]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERRO]\033[0m $*" >&2; exit 1; }

# ── Argumentos ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)      DOMAIN="$2";  shift 2 ;;
        --email)       EMAIL="$2";   shift 2 ;;
        --skip-ssl)    SKIP_SSL=true; shift ;;
        --skip-migrations) SKIP_MIGRATIONS=true; shift ;;
        *) err "Argumento desconhecido: $1" ;;
    esac
done

[[ -n "$DOMAIN" ]] || err "Informe --domain <seu-dominio.com>"

# ── 1. Verifica dependências ──────────────────────────────────────────────────
log "Verificando dependências..."
command -v docker     &>/dev/null || err "Docker não instalado."
docker compose version &>/dev/null || err "Docker Compose v2 não instalado."

# ── 2. Gera segredos se não existir .env.production ──────────────────────────
if [[ ! -f ".env.production" ]]; then
    log "Gerando segredos de produção..."
    bash scripts/generate_secrets.sh > .env.production
    sed -i "s/seu-dominio.com/$DOMAIN/" .env.production
    chmod 600 .env.production
    warn ".env.production gerado — edite STRIPE_API_KEY e notificações antes de continuar."
    warn "Pressione ENTER para continuar ou Ctrl+C para editar primeiro."
    read -r
fi

export $(grep -v '^#' .env.production | xargs)

# ── 3. Certificado SSL (Let's Encrypt) ───────────────────────────────────────
if [[ "$SKIP_SSL" == "false" ]]; then
    log "Obtendo certificado SSL para $DOMAIN..."
    mkdir -p ssl/certs ssl/www

    if ! command -v certbot &>/dev/null; then
        apt-get update -qq && apt-get install -y -qq certbot
    fi

    # Inicia Nginx temporário para validação ACME
    docker run -d --rm --name certbot-nginx \
        -v "$(pwd)/ssl/www:/var/www/certbot:ro" \
        -p 80:80 \
        nginx:alpine \
        nginx -g "daemon off; events{} http{server{listen 80; root /var/www/certbot;}}" &>/dev/null || true

    certbot certonly \
        --webroot \
        --webroot-path ./ssl/www \
        --email "${EMAIL:-admin@${DOMAIN}}" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" \
        --cert-path ./ssl/certs/fullchain.pem \
        --key-path ./ssl/certs/privkey.pem \
        2>/dev/null || {
            warn "certbot falhou — usando certificado auto-assinado para teste."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/certs/privkey.pem \
                -out ssl/certs/fullchain.pem \
                -subj "/CN=$DOMAIN" 2>/dev/null
        }

    docker stop certbot-nginx 2>/dev/null || true

    # Cron para renovação automática (certbot renew)
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker exec wifisense-prod-gateway nginx -s reload") | crontab -
    log "Renovação automática de SSL configurada (cron 03:00)."
fi

# ── 4. Migrations do banco ────────────────────────────────────────────────────
if [[ "$SKIP_MIGRATIONS" == "false" ]]; then
    log "Executando migrations do banco..."
    bash scripts/migrations/run_migrations.sh upgrade head
fi

# ── 5. Sobe os serviços ───────────────────────────────────────────────────────
log "Iniciando serviços de produção..."
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# ── 6. Aguarda health checks ──────────────────────────────────────────────────
log "Aguardando serviços ficarem saudáveis..."
MAX_WAIT=120
ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    HEALTHY=$(docker compose -f docker-compose.prod.yml ps --format json 2>/dev/null | \
              python3 -c "import sys,json; data=sys.stdin.read(); items=[json.loads(l) for l in data.splitlines() if l]; print(sum(1 for i in items if 'healthy' in i.get('Health','').lower()))" 2>/dev/null || echo "0")
    log "Serviços saudáveis: $HEALTHY"
    [[ "$HEALTHY" -ge 5 ]] && break
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

# ── 7. Instala cron de backup ─────────────────────────────────────────────────
log "Configurando backup automático..."
bash scripts/backup/install_backup_cron.sh

# ── 8. Resultado final ────────────────────────────────────────────────────────
log ""
log "════════════════════════════════════════════════════════"
log "  WiFiSense SaaS — Deploy de Produção Concluído!"
log ""
log "  URL:      https://$DOMAIN"
log "  Status:   https://$DOMAIN/status"
log "  Grafana:  https://$DOMAIN/grafana  (admin / \$GRAFANA_ADMIN_PASSWORD)"
log "  Kibana:   http://$DOMAIN:5601"
log ""
log "  Logs:     docker compose -f docker-compose.prod.yml logs -f"
log "  Status:   docker compose -f docker-compose.prod.yml ps"
log "  Backups:  /var/backups/wifisense/"
log "════════════════════════════════════════════════════════"
