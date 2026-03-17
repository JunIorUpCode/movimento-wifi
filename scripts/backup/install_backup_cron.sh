#!/bin/bash
# install_backup_cron.sh — Instala cron job de backup automático do PostgreSQL
#
# Uso: sudo bash install_backup_cron.sh
# Remove: sudo bash install_backup_cron.sh --remove

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_postgres.sh"
CRON_FILE="/etc/cron.d/wifisense-backup"
LOG_FILE="/var/log/wifisense_backup.log"
BACKUP_DIR="/var/backups/wifisense"

log() { echo "[BACKUP-INSTALL] $*"; }

if [[ "${1:-}" == "--remove" ]]; then
    rm -f "$CRON_FILE"
    log "Cron de backup removido."
    exit 0
fi

chmod +x "$BACKUP_SCRIPT"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
touch "$LOG_FILE"
chmod 640 "$LOG_FILE"

# Variáveis de ambiente do backup (lidas do .env se existir)
ENV_FILE="${ENV_FILE:-/opt/wifisense/.env}"
ENV_VARS=""
if [[ -f "$ENV_FILE" ]]; then
    # Exporta variáveis DATABASE_* para o cron
    ENV_VARS=$(grep -E "^DATABASE_" "$ENV_FILE" | tr '\n' ' ' | sed 's/ $//')
fi

# Cria cron job: backup diário às 02:00
cat > "$CRON_FILE" <<EOF
# WiFiSense — Backup automático do PostgreSQL
# Gerado por install_backup_cron.sh em $(date)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Backup diário às 02:00 com retenção de 7 dias
0 2 * * * postgres ${ENV_VARS:+$ENV_VARS }BACKUP_DIR=$BACKUP_DIR RETENTION_DAYS=7 bash $BACKUP_SCRIPT >> $LOG_FILE 2>&1

# Verificação de saúde do standby às 06:00 (se configurado)
0 6 * * * postgres psql -c "SELECT pg_is_in_recovery(), now() - pg_last_xact_replay_timestamp() AS replication_lag;" >> $LOG_FILE 2>&1 || true
EOF

chmod 644 "$CRON_FILE"

log "Cron de backup instalado: $CRON_FILE"
log "Backup diário às 02:00 — logs em: $LOG_FILE"
log "Para testar agora: sudo -u postgres bash $BACKUP_SCRIPT"
