# WiFiSense Agent - Agente Local

Agente Python que roda em dispositivos cliente (Raspberry Pi ou PC Windows/Linux) para capturar sinais Wi-Fi e transmitir para o backend central.

## Características

- **Captura de Sinais**: RSSI (todos os planos) e CSI (plano PREMIUM)
- **Processamento Local**: Extração de features antes de transmissão
- **Buffer Offline**: Armazena até 100 MB de dados durante offline
- **Compressão**: Comprime dados com gzip antes de transmitir
- **Heartbeat**: Envia status de saúde a cada 60 segundos
- **Configuração Remota**: Recebe atualizações via WebSocket
- **Auto-Retry**: Retry com exponential backoff em caso de falha

## Arquitetura

```
agent/
├── agent.py                 # Coordenador principal
├── main.py                  # Script de entrada
├── config.py                # Gerenciamento de configuração
├── hardware_detector.py     # Detecção de hardware
├── capture/                 # Módulo de captura
│   ├── __init__.py
│   └── capture_manager.py   # Gerenciador de captura (reutiliza backend)
├── processing/              # Módulo de processamento
│   ├── __init__.py
│   └── feature_extractor.py # Extrator de features (reutiliza backend)
├── storage/                 # Módulo de armazenamento
│   ├── __init__.py
│   └── buffer_manager.py    # Buffer SQLite para offline
└── api_client/              # Módulo de comunicação
    ├── __init__.py
    ├── http_client.py       # Cliente HTTP com retry
    └── websocket_client.py  # Cliente WebSocket
```

## Instalação

### Requisitos

- Python 3.11+
- Adaptador Wi-Fi
- Conexão com internet

### Instalação de Dependências

```bash
cd agent
pip install -r requirements.txt
```

## Uso

### Primeira Execução (Ativação)

Na primeira execução, o agente solicitará uma chave de ativação:

```bash
python main.py
```

O agente irá:
1. Detectar hardware automaticamente
2. Solicitar chave de ativação
3. Registrar dispositivo no backend
4. Salvar credenciais localmente (criptografadas)

### Execuções Subsequentes

Após ativação, o agente inicia automaticamente:

```bash
python main.py
```

### Executar como Serviço

#### Linux (systemd)

Criar arquivo `/etc/systemd/system/wifisense-agent.service`:

```ini
[Unit]
Description=WiFiSense Agent
After=network.target

[Service]
Type=simple
User=wifisense
WorkingDirectory=/opt/wifisense-agent
ExecStart=/usr/bin/python3 /opt/wifisense-agent/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Habilitar e iniciar:

```bash
sudo systemctl enable wifisense-agent
sudo systemctl start wifisense-agent
sudo systemctl status wifisense-agent
```

#### Windows (Windows Service)

TODO: Implementar instalador Windows com NSIS

## Configuração

As configurações são armazenadas em `~/.wifisense_agent/config.json` (criptografadas).

### Configurações Disponíveis

- `sampling_interval`: Intervalo de captura em segundos (padrão: 1)
- `buffer_max_size_mb`: Tamanho máximo do buffer offline (padrão: 100 MB)
- `heartbeat_interval`: Intervalo de heartbeat em segundos (padrão: 60)
- `presence_threshold`: Threshold para detecção de presença (padrão: 0.7)
- `movement_threshold`: Threshold para detecção de movimento (padrão: 0.8)
- `fall_threshold`: Threshold para detecção de queda (padrão: 0.85)

### Configuração Remota

O agente recebe atualizações de configuração via WebSocket do backend. As configurações são aplicadas automaticamente em até 30 segundos.

## Funcionamento

### Fluxo de Dados

1. **Captura**: Captura sinal Wi-Fi a cada `sampling_interval` segundos
2. **Processamento**: Extrai features localmente (variance, energy, rate_of_change)
3. **Compressão**: Comprime dados com gzip
4. **Transmissão**: Envia para backend via HTTPS
5. **Buffer**: Se offline, armazena em SQLite (até 100 MB)
6. **Upload**: Quando online, envia dados buffered

### Detecção de Hardware

O agente detecta automaticamente:
- Tipo de dispositivo (Raspberry Pi, Windows, Linux)
- Sistema operacional e versão
- Adaptador Wi-Fi disponível
- Capacidade CSI (se hardware suporta)

### Buffer Offline

Durante offline:
- Dados são armazenados em SQLite local
- Limite de 100 MB (configurável)
- Política FIFO: descarta mais antigos quando cheio
- Timestamps originais preservados

Quando conexão é restaurada:
- Upload automático de dados buffered
- Envio em lotes de 100 registros
- Limpeza após upload bem-sucedido

### Heartbeat

A cada 60 segundos, o agente envia:
- Timestamp
- CPU usage (%)
- Memory usage (MB)
- Disk usage (%)

Se 3 heartbeats consecutivos falharem (3 minutos), o dispositivo é marcado como offline no backend.

## Segurança

- **Credenciais Criptografadas**: JWT token e activation_key são criptografados com Fernet
- **HTTPS**: Toda comunicação usa HTTPS
- **Permissões de Arquivo**: Arquivos de config têm permissão 0600 (apenas dono)
- **JWT Expiration**: Tokens expiram em 24 horas

## Troubleshooting

### Erro: "Nenhum provider de captura disponível"

**Causa**: Nenhum adaptador Wi-Fi detectado

**Solução**:
- Verifique se o adaptador Wi-Fi está conectado
- No Linux, execute `iwconfig` ou `iw dev`
- No Windows, execute `netsh wlan show interfaces`

### Erro: "License not found or already activated"

**Causa**: Chave de ativação inválida ou já usada

**Solução**:
- Verifique se a chave foi digitada corretamente
- Gere nova chave no painel administrativo
- Verifique se o limite de dispositivos não foi atingido

### Buffer cheio constantemente

**Causa**: Dispositivo offline por muito tempo

**Solução**:
- Verifique conexão com internet
- Verifique se o backend está acessível
- Aumente `buffer_max_size_mb` se necessário

### Alto uso de CPU

**Causa**: `sampling_interval` muito baixo

**Solução**:
- Aumente `sampling_interval` para 2-5 segundos
- Configure remotamente via painel do cliente

## Desenvolvimento

### Estrutura de Código

Todo código está 100% comentado em português seguindo padrões de clean code.

### Testes

TODO: Implementar testes unitários

```bash
pytest tests/
```

## Licença

Proprietary - WiFiSense SaaS Platform
