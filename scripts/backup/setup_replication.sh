#!/bin/bash
# setup_replication.sh — Configura replicação streaming (hot standby) do PostgreSQL
#
# Executa no PRIMARY para configurar o STANDBY para receber replicação.
#
# Uso:
#   PRIMARY:  bash setup_replication.sh primary --standby-ip 192.168.1.101
#   STANDBY:  bash setup_replication.sh standby --primary-ip 192.168.1.100
#
# Requisitos:
#   - PostgreSQL 15+ instalado nos dois servidores
#   - SSH sem senha do primary para o standby (para pg_basebackup)
#   - Executar como root ou usuário postgres

set -euo pipefail

MODE="${1:-}"
shift || true

PRIMARY_IP=""
STANDBY_IP=""
REPLICATION_USER="replicator"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-wifisense_replication_2026}"
PG_DATA="${PGDATA:-/var/lib/postgresql/15/main}"
PG_CONF="$PG_DATA/postgresql.conf"
PG_HBA="$PG_DATA/pg_hba.conf"

log() { echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [REPLICATION] $*"; }
err() { log "ERRO: $*"; exit 1; }

# Processa argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        --standby-ip) STANDBY_IP="$2"; shift 2 ;;
        --primary-ip) PRIMARY_IP="$2"; shift 2 ;;
        *) err "Argumento desconhecido: $1" ;;
    esac
done

# ── MODO PRIMARY ──────────────────────────────────────────────────────────────
setup_primary() {
    [[ -n "$STANDBY_IP" ]] || err "Informe --standby-ip <IP>"
    log "Configurando PRIMARY em $PG_DATA..."

    # Cria usuário de replicação
    sudo -u postgres psql -c \
        "CREATE ROLE $REPLICATION_USER REPLICATION LOGIN PASSWORD '$REPLICATION_PASSWORD';" \
        2>/dev/null || \
    sudo -u postgres psql -c \
        "ALTER ROLE $REPLICATION_USER PASSWORD '$REPLICATION_PASSWORD';"

    # postgresql.conf — habilita replicação streaming
    cat >> "$PG_CONF" <<EOF

# ── Replicação Streaming (WiFiSense) ──────────────────────────────────
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3
wal_keep_size = 256MB
hot_standby = on
synchronous_commit = local
EOF

    # pg_hba.conf — permite conexão do standby
    cat >> "$PG_HBA" <<EOF
# Replicação streaming — standby
host    replication     $REPLICATION_USER    $STANDBY_IP/32    scram-sha-256
EOF

    log "Recarregando PostgreSQL..."
    systemctl reload postgresql 2>/dev/null || pg_ctlcluster 15 main reload

    log "PRIMARY configurado. Próximo passo:"
    log "  1. Execute no STANDBY: bash setup_replication.sh standby --primary-ip $(hostname -I | awk '{print $1}')"
    log "  2. Verifique: SELECT * FROM pg_stat_replication;"
}

# ── MODO STANDBY ──────────────────────────────────────────────────────────────
setup_standby() {
    [[ -n "$PRIMARY_IP" ]] || err "Informe --primary-ip <IP>"
    log "Configurando STANDBY. Primary: $PRIMARY_IP"

    # Para PostgreSQL se estiver rodando
    systemctl stop postgresql 2>/dev/null || true

    # Limpa data directory do standby
    log "Limpando data directory do standby..."
    rm -rf "${PG_DATA:?}/"*

    # pg_basebackup copia o primary completo
    log "Executando pg_basebackup do primary $PRIMARY_IP..."
    export PGPASSWORD="$REPLICATION_PASSWORD"
    sudo -u postgres pg_basebackup \
        --host="$PRIMARY_IP" \
        --username="$REPLICATION_USER" \
        --pgdata="$PG_DATA" \
        --wal-method=stream \
        --progress \
        --verbose \
        --checkpoint=fast
    unset PGPASSWORD

    # Cria arquivo de sinalização de standby
    sudo -u postgres touch "$PG_DATA/standby.signal"

    # Configura conexão de replicação no postgresql.conf do standby
    cat >> "$PG_DATA/postgresql.conf" <<EOF

# ── Standby — conexão com primary ──────────────────────────────────────
primary_conninfo = 'host=$PRIMARY_IP port=5432 user=$REPLICATION_USER password=$REPLICATION_PASSWORD application_name=wifisense_standby'
hot_standby = on
EOF

    # Inicia standby
    log "Iniciando standby PostgreSQL..."
    sudo -u postgres pg_ctlcluster 15 main start 2>/dev/null || \
        systemctl start postgresql

    log "STANDBY configurado e rodando em modo hot standby!"
    log "Verifique no PRIMARY: SELECT * FROM pg_stat_replication;"
    log "Verifique no STANDBY: SELECT pg_is_in_recovery();"
}

# ── Roteamento ────────────────────────────────────────────────────────────────
case "$MODE" in
    primary)  setup_primary ;;
    standby)  setup_standby ;;
    *)        err "Uso: $0 [primary|standby] [--standby-ip IP | --primary-ip IP]" ;;
esac
