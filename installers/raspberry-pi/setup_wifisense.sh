#!/bin/bash
# setup_wifisense.sh — Instala WiFiSense Local no Raspberry Pi (Raspberry Pi OS)
# Compatível com: Raspberry Pi 3B+, 4, 5 — Raspberry Pi OS Bullseye/Bookworm (64-bit)
# Uso: curl -sSL https://wifisense.com/install.sh | sudo bash
#  ou: sudo bash setup_wifisense.sh

set -euo pipefail

VERSION="1.0.0"
INSTALL_DIR="/opt/wifisense"
SERVICE_USER="wifisense"
REPO_URL="https://github.com/wifisense/wifisense-local/releases/download/v${VERSION}"

log()  { echo -e "\033[1;32m[WiFiSense]\033[0m $*"; }
warn() { echo -e "\033[1;33m[AVISO]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERRO]\033[0m $*" >&2; exit 1; }

# ── Verifica root ─────────────────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || err "Execute como root: sudo bash $0"

# ── Detecta arquitetura ──────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) ARCH_TAG="arm64" ;;
    armv7l)  ARCH_TAG="armv7" ;;
    x86_64)  ARCH_TAG="amd64" ;;
    *)       err "Arquitetura não suportada: $ARCH" ;;
esac
log "Arquitetura detectada: $ARCH ($ARCH_TAG)"

# ── Atualiza sistema ─────────────────────────────────────────────────────
log "Atualizando pacotes do sistema..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    libssl-dev libffi-dev \
    wireless-tools iw net-tools \
    git curl

# ── Cria usuário de serviço ─────────────────────────────────────────────
log "Criando usuário de serviço..."
if ! id -u "$SERVICE_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

# Adiciona usuário ao grupo netdev para acesso Wi-Fi sem root
usermod -aG netdev "$SERVICE_USER" 2>/dev/null || true

# ── Instala WiFiSense ─────────────────────────────────────────────────────
log "Instalando WiFiSense Local v${VERSION}..."
mkdir -p "$INSTALL_DIR"/{data,logs,models}

# Clona ou atualiza repositório
if [[ -d "$INSTALL_DIR/.git" ]]; then
    log "Atualizando instalação existente..."
    git -C "$INSTALL_DIR" pull --quiet
else
    # Em produção, baixa o release; em dev, copia do diretório atual
    if [[ -f "$(dirname "$0")/../../backend/app/main.py" ]]; then
        log "Copiando arquivos do desenvolvimento local..."
        cp -r "$(dirname "$0")/../../backend/app"    "$INSTALL_DIR/"
        cp -r "$(dirname "$0")/../../backend/models" "$INSTALL_DIR/"
        cp    "$(dirname "$0")/../../backend/requirements.txt" "$INSTALL_DIR/"
        cp -r "$(dirname "$0")/../../shared"         "$INSTALL_DIR/shared"
    else
        log "Baixando release v${VERSION}..."
        curl -sSL "${REPO_URL}/wifisense-local-${VERSION}-${ARCH_TAG}.tar.gz" \
            | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi
fi

# ── Ambiente Python virtual ─────────────────────────────────────────────
log "Criando ambiente virtual Python..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# ── Configura permissões ─────────────────────────────────────────────────
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# ── Cria arquivo .env padrão ────────────────────────────────────────────
ENV_FILE="$INSTALL_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log "Criando arquivo de configuração padrão..."
    cat > "$ENV_FILE" <<EOF
HOST=0.0.0.0
PORT=8000
DB_PATH=${INSTALL_DIR}/data/wifisense.db
LOG_LEVEL=INFO
SIMULATION_MODE=false
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

# ── Instala serviço systemd ─────────────────────────────────────────────
log "Configurando serviço systemd..."
cat > /etc/systemd/system/wifisense.service <<EOF
[Unit]
Description=WiFiSense Local — Detecção de presença via Wi-Fi
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${INSTALL_DIR}/.venv/bin/uvicorn app.main:app --host \${HOST} --port \${PORT}
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wifisense
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=${INSTALL_DIR}/data ${INSTALL_DIR}/logs ${INSTALL_DIR}/models
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wifisense.service
systemctl start wifisense.service

# ── Resultado ─────────────────────────────────────────────────────────────
IP=$(hostname -I | awk '{print $1}')
log ""
log "========================================================"
log "  WiFiSense Local v${VERSION} instalado com sucesso!"
log "  Acesse pelo navegador: http://${IP}:8000"
log "  Logs: journalctl -u wifisense -f"
log "  Status: systemctl status wifisense"
log "========================================================"
