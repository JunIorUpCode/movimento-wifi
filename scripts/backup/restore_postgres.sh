#!/bin/bash
# restore_postgres.sh — Restaura um backup do PostgreSQL WiFiSense
#
# Uso:
#   bash restore_postgres.sh /var/backups/wifisense/wifisense_20260317_020000.sql.gz
#   bash restore_postgres.sh --latest   # restaura o backup mais recente

set -euo pipefail

PG_HOST="${DATABASE_HOST:-localhost}"
PG_PORT="${DATABASE_PORT:-5432}"
PG_USER="${DATABASE_USER:-wifisense}"
PG_PASS="${DATABASE_PASSWORD:-wifisense_password}"
PG_DB="${DATABASE_NAME:-wifisense_saas}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/wifisense}"

export PGPASSWORD="$PG_PASS"
log() { echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [RESTORE] $*"; }
err() { log "ERRO: $*"; exit 1; }

# ── Seleciona o arquivo de backup ────────────────────────────────────────────
if [[ "${1:-}" == "--latest" ]]; then
    BACKUP_FILE=$(find "$BACKUP_DIR" -name "wifisense_*.sql.gz" | sort | tail -1)
    [[ -n "$BACKUP_FILE" ]] || err "Nenhum backup encontrado em $BACKUP_DIR"
elif [[ -n "${1:-}" ]]; then
    BACKUP_FILE="$1"
else
    err "Uso: $0 <arquivo.sql.gz>  ou  $0 --latest"
fi

[[ -f "$BACKUP_FILE" ]] || err "Arquivo não encontrado: $BACKUP_FILE"

# ── Verifica checksum (se disponível) ────────────────────────────────────────
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [[ -f "$CHECKSUM_FILE" ]]; then
    log "Verificando integridade do backup..."
    sha256sum --check "$CHECKSUM_FILE" --quiet || err "Checksum inválido — backup pode estar corrompido."
    log "Integridade OK."
fi

# ── Verifica integridade gzip ────────────────────────────────────────────────
gzip -t "$BACKUP_FILE" 2>/dev/null || err "Arquivo gzip corrompido: $BACKUP_FILE"

# ── Confirmação interativa ────────────────────────────────────────────────────
SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
log "ATENÇÃO: Esta operação irá substituir todos os dados de '$PG_DB'!"
log "Arquivo: $BACKUP_FILE ($SIZE)"
read -rp "Confirma a restauração? [sim/não]: " CONFIRM
[[ "$CONFIRM" == "sim" ]] || { log "Restauração cancelada."; exit 0; }

# ── Recria o banco ────────────────────────────────────────────────────────────
log "Encerrando conexões ativas..."
psql --host="$PG_HOST" --port="$PG_PORT" --username="$PG_USER" \
    --dbname=postgres --no-password -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$PG_DB' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

log "Recriando banco de dados..."
psql --host="$PG_HOST" --port="$PG_PORT" --username="$PG_USER" \
    --dbname=postgres --no-password \
    -c "DROP DATABASE IF EXISTS \"$PG_DB\";" \
    -c "CREATE DATABASE \"$PG_DB\" OWNER \"$PG_USER\";" \
    > /dev/null

# ── Restaura dados ────────────────────────────────────────────────────────────
log "Restaurando dados de $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | psql \
    --host="$PG_HOST" \
    --port="$PG_PORT" \
    --username="$PG_USER" \
    --dbname="$PG_DB" \
    --no-password \
    --quiet

log "Restauração concluída com sucesso."
unset PGPASSWORD
