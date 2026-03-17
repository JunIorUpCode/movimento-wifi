#!/bin/bash
# backup_postgres.sh — Backup automático do PostgreSQL WiFiSense
#
# Funcionalidades:
# - pg_dump comprimido (gzip) de todos os schemas WiFiSense
# - Retenção configurável (padrão: 7 dias)
# - Verificação de integridade do arquivo gerado
# - Notificação de falha por log estruturado
#
# Agendamento com cron (todo dia às 02:00):
#   0 2 * * * /opt/wifisense/scripts/backup/backup_postgres.sh >> /var/log/wifisense_backup.log 2>&1

set -euo pipefail

# ── Configuração ──────────────────────────────────────────────────────────────
PG_HOST="${DATABASE_HOST:-localhost}"
PG_PORT="${DATABASE_PORT:-5432}"
PG_USER="${DATABASE_USER:-wifisense}"
PG_PASS="${DATABASE_PASSWORD:-wifisense_password}"
PG_DB="${DATABASE_NAME:-wifisense_saas}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/wifisense}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/wifisense_${TIMESTAMP}.sql.gz"

export PGPASSWORD="$PG_PASS"

log() { echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [BACKUP] $*"; }

# ── Prepara diretório ────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

log "Iniciando backup de $PG_DB em $PG_HOST:$PG_PORT..."

# ── Executa pg_dump ──────────────────────────────────────────────────────────
pg_dump \
    --host="$PG_HOST" \
    --port="$PG_PORT" \
    --username="$PG_USER" \
    --dbname="$PG_DB" \
    --format=plain \
    --no-password \
    --verbose \
    2>/dev/null \
  | gzip -9 > "$BACKUP_FILE"

# ── Verifica integridade ─────────────────────────────────────────────────────
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    log "ERRO: arquivo de backup corrompido: $BACKUP_FILE"
    rm -f "$BACKUP_FILE"
    exit 1
fi

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
SHA256=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
log "Backup concluído: $BACKUP_FILE ($SIZE) — SHA256: $SHA256"

# Salva checksum
echo "$SHA256  $BACKUP_FILE" > "${BACKUP_FILE}.sha256"

# ── Remove backups antigos ────────────────────────────────────────────────────
log "Removendo backups com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name "wifisense_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "wifisense_*.sha256" -mtime +"$RETENTION_DAYS" -delete

REMAINING=$(find "$BACKUP_DIR" -name "wifisense_*.sql.gz" | wc -l)
log "Backups mantidos: $REMAINING arquivo(s)."

unset PGPASSWORD
