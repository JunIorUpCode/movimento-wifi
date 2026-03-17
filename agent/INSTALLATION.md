# Guia de Instalação - WiFiSense Agent

Este guia fornece instruções detalhadas para instalar e configurar o agente WiFiSense em diferentes plataformas.

---

## 📋 Requisitos

### Requisitos Mínimos

- **Python**: 3.11 ou superior
- **RAM**: 256 MB
- **Disco**: 500 MB (incluindo buffer)
- **Rede**: Conexão com internet (Wi-Fi ou Ethernet)
- **Adaptador Wi-Fi**: Qualquer adaptador compatível

### Requisitos Recomendados

- **Python**: 3.11+
- **RAM**: 512 MB
- **Disco**: 1 GB
- **Adaptador Wi-Fi**: 
  - Para plano BÁSICO: Qualquer adaptador
  - Para plano PREMIUM: Intel 5300, Atheros AR9xxx, ou ESP32-S3

---

## 🪟 Instalação no Windows

### 1. Instalar Python

Baixe e instale Python 3.11+ de [python.org](https://www.python.org/downloads/)

Durante a instalação, marque:
- ✅ Add Python to PATH
- ✅ Install pip

### 2. Baixar o Agente

```powershell
# Clone o repositório ou baixe o ZIP
git clone https://github.com/wifisense/agent.git
cd agent
```

### 3. Instalar Dependências

```powershell
pip install -r requirements.txt
```

### 4. Executar o Agente

```powershell
python main.py
```

### 5. Instalar como Serviço (Opcional)

**Usando NSSM (Non-Sucking Service Manager):**

1. Baixe NSSM: https://nssm.cc/download
2. Extraia e execute:

```powershell
nssm install WiFiSenseAgent "C:\Python311\python.exe" "C:\path\to\agent\main.py"
nssm set WiFiSenseAgent AppDirectory "C:\path\to\agent"
nssm set WiFiSenseAgent DisplayName "WiFiSense Agent"
nssm set WiFiSenseAgent Description "Agente local WiFiSense para monitoramento Wi-Fi"
nssm set WiFiSenseAgent Start SERVICE_AUTO_START
nssm start WiFiSenseAgent
```

---

## 🐧 Instalação no Linux

### 1. Instalar Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3-pip python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.11 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

### 2. Baixar o Agente

```bash
git clone https://github.com/wifisense/agent.git
cd agent
```

### 3. Criar Ambiente Virtual (Recomendado)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5. Executar o Agente

```bash
python main.py
```

### 6. Instalar como Serviço systemd

**Criar arquivo de serviço:**

```bash
sudo nano /etc/systemd/system/wifisense-agent.service
```

**Conteúdo:**

```ini
[Unit]
Description=WiFiSense Agent
After=network.target

[Service]
Type=simple
User=wifisense
Group=wifisense
WorkingDirectory=/opt/wifisense-agent
ExecStart=/opt/wifisense-agent/venv/bin/python /opt/wifisense-agent/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Habilitar e iniciar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable wifisense-agent
sudo systemctl start wifisense-agent
sudo systemctl status wifisense-agent
```

**Ver logs:**

```bash
sudo journalctl -u wifisense-agent -f
```

---

## 🥧 Instalação no Raspberry Pi

### 1. Preparar Raspberry Pi OS

**Baixar Raspberry Pi OS Lite:**
- https://www.raspberrypi.com/software/operating-systems/

**Gravar no SD card usando Raspberry Pi Imager**

### 2. Configuração Inicial

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
sudo apt install python3.11 python3-pip python3-venv git -y

# Instalar ferramentas Wi-Fi
sudo apt install wireless-tools iw -y
```

### 3. Baixar e Instalar Agente

```bash
# Criar diretório
sudo mkdir -p /opt/wifisense-agent
sudo chown pi:pi /opt/wifisense-agent

# Clonar repositório
cd /opt/wifisense-agent
git clone https://github.com/wifisense/agent.git .

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 4. Configurar como Serviço

```bash
sudo nano /etc/systemd/system/wifisense-agent.service
```

**Conteúdo:**

```ini
[Unit]
Description=WiFiSense Agent
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/wifisense-agent
ExecStart=/opt/wifisense-agent/venv/bin/python /opt/wifisense-agent/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Habilitar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable wifisense-agent
sudo systemctl start wifisense-agent
```

### 5. Configurar Auto-Start no Boot

```bash
# Adicionar ao rc.local (alternativa)
sudo nano /etc/rc.local
```

Adicionar antes de `exit 0`:

```bash
/opt/wifisense-agent/venv/bin/python /opt/wifisense-agent/main.py &
```

---

## 🔧 Configuração Pós-Instalação

### 1. Primeira Execução (Ativação)

Na primeira execução, o agente solicitará:

```
Digite a chave de ativação: XXXX-XXXX-XXXX-XXXX
```

**Onde obter a chave:**
1. Acesse o painel do cliente
2. Vá em "Dispositivos" → "Adicionar Dispositivo"
3. Copie a chave de ativação gerada

### 2. Verificar Status

**Linux/Raspberry Pi:**
```bash
sudo systemctl status wifisense-agent
```

**Windows:**
```powershell
nssm status WiFiSenseAgent
```

### 3. Ver Logs

**Linux/Raspberry Pi:**
```bash
sudo journalctl -u wifisense-agent -f
```

**Windows:**
```powershell
# Logs em: C:\ProgramData\WiFiSenseAgent\logs\
```

### 4. Configuração Manual (Avançado)

Editar arquivo de configuração:

```bash
nano ~/.wifisense_agent/config.json
```

**Exemplo:**

```json
{
  "device_id": "uuid-do-dispositivo",
  "backend_url": "https://api.wifisense.com",
  "sampling_interval": 1,
  "buffer_max_size_mb": 100,
  "heartbeat_interval": 60
}
```

---

## 🔍 Troubleshooting

### Problema: "Nenhum provider de captura disponível"

**Causa**: Adaptador Wi-Fi não detectado

**Solução:**

**Windows:**
```powershell
netsh wlan show interfaces
```

**Linux:**
```bash
iwconfig
# ou
iw dev
```

Verifique se o adaptador está ativo e conectado.

---

### Problema: "License not found or already activated"

**Causa**: Chave de ativação inválida

**Solução:**
1. Verifique se digitou corretamente
2. Gere nova chave no painel administrativo
3. Verifique limite de dispositivos da licença

---

### Problema: "Connection refused" ou "Timeout"

**Causa**: Backend inacessível

**Solução:**
1. Verifique conexão com internet
2. Teste conectividade:
   ```bash
   curl https://api.wifisense.com/health
   ```
3. Verifique firewall/proxy

---

### Problema: Alto uso de CPU

**Causa**: `sampling_interval` muito baixo

**Solução:**
1. Aumente intervalo de captura:
   ```json
   "sampling_interval": 2
   ```
2. Configure remotamente via painel

---

### Problema: Buffer cheio constantemente

**Causa**: Dispositivo offline por muito tempo

**Solução:**
1. Verifique conexão
2. Aumente tamanho do buffer:
   ```json
   "buffer_max_size_mb": 200
   ```

---

## 🔐 Segurança

### Permissões de Arquivo

O agente cria arquivos com permissões restritas:

```bash
~/.wifisense_agent/
├── config.json         # 0600 (rw-------)
├── encryption.key      # 0600 (rw-------)
└── agent_buffer.db     # 0600 (rw-------)
```

### Criptografia

- **Credenciais**: Criptografadas com Fernet (AES-128)
- **Comunicação**: HTTPS obrigatório
- **JWT**: Tokens expiram em 24 horas

### Firewall

**Portas necessárias:**
- **443 (HTTPS)**: Comunicação com backend
- **443 (WSS)**: WebSocket para configuração remota

**Configurar firewall (Linux):**

```bash
sudo ufw allow out 443/tcp
```

---

## 📊 Monitoramento

### Verificar Saúde do Agente

**Status do serviço:**
```bash
sudo systemctl status wifisense-agent
```

**Logs em tempo real:**
```bash
sudo journalctl -u wifisense-agent -f
```

**Estatísticas do buffer:**
```bash
sqlite3 ~/.wifisense_agent/agent_buffer.db "SELECT COUNT(*) FROM buffered_data WHERE uploaded = 0;"
```

### Métricas Coletadas

O agente envia a cada 60 segundos:
- CPU usage (%)
- Memory usage (MB)
- Disk usage (%)
- Timestamp

---

## 🔄 Atualização

### Atualizar Manualmente

```bash
cd /opt/wifisense-agent
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart wifisense-agent
```

### Auto-Update (Futuro)

O agente verificará atualizações automaticamente a cada 24 horas.

---

## 🗑️ Desinstalação

### Linux/Raspberry Pi

```bash
# Parar serviço
sudo systemctl stop wifisense-agent
sudo systemctl disable wifisense-agent

# Remover serviço
sudo rm /etc/systemd/system/wifisense-agent.service
sudo systemctl daemon-reload

# Remover arquivos
sudo rm -rf /opt/wifisense-agent
rm -rf ~/.wifisense_agent
```

### Windows

```powershell
# Parar serviço
nssm stop WiFiSenseAgent
nssm remove WiFiSenseAgent confirm

# Remover arquivos
Remove-Item -Recurse -Force C:\path\to\agent
Remove-Item -Recurse -Force $env:USERPROFILE\.wifisense_agent
```

---

## 📞 Suporte

- **Documentação**: https://docs.wifisense.com
- **Email**: support@wifisense.com
- **Tickets**: Painel do cliente → Suporte

---

## 📝 Licença

Proprietary - WiFiSense SaaS Platform
