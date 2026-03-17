#!/bin/bash
# run_migrations.sh — Executa migrations Alembic no banco de dados
# Uso: bash scripts/migrations/run_migrations.sh [upgrade|downgrade|history|current]

set -euo pipefail

COMMAND="${1:-upgrade}"
TARGET="${2:-head}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Carrega variáveis do .env se existir
if [[ -f ".env.production" ]]; then
    export $(grep -v '^#' .env.production | xargs)
elif [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Constrói DATABASE_URL se não definida
if [[ -z "${DATABASE_URL:-}" ]]; then
    export DATABASE_URL="postgresql://${DATABASE_USER:-wifisense}:${DATABASE_PASSWORD:-wifisense_password}@${DATABASE_HOST:-localhost}:${DATABASE_PORT:-5432}/${DATABASE_NAME:-wifisense_saas}"
fi

echo "[MIGRATIONS] DATABASE_URL: ${DATABASE_URL//:*@/:***@}"

cd "$SCRIPT_DIR"

case "$COMMAND" in
    upgrade)
        echo "[MIGRATIONS] Aplicando migrations até: $TARGET"
        python3 -m alembic -c alembic.ini upgrade "$TARGET"
        ;;
    downgrade)
        echo "[MIGRATIONS] Revertendo para: $TARGET"
        python3 -m alembic -c alembic.ini downgrade "$TARGET"
        ;;
    history)
        python3 -m alembic -c alembic.ini history --verbose
        ;;
    current)
        python3 -m alembic -c alembic.ini current
        ;;
    generate)
        DESCRIPTION="${2:-auto_migration}"
        echo "[MIGRATIONS] Gerando nova migration: $DESCRIPTION"
        python3 -m alembic -c alembic.ini revision --autogenerate -m "$DESCRIPTION"
        ;;
    *)
        echo "Uso: $0 [upgrade [head|revision]|downgrade [base|revision]|history|current|generate [desc]]"
        exit 1
        ;;
esac

echo "[MIGRATIONS] Concluído."
