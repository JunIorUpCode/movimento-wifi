# WiFiSense Local — Guia da API REST

**Versão:** 1.0.0
**Base URL:** `http://localhost:8000`
**Documentação interativa:** [Swagger UI](/docs) | [ReDoc](/redoc) | [OpenAPI JSON](/openapi.json)

---

## Visão Geral

A API do WiFiSense Local expõe endpoints REST para:
- Monitoramento em tempo real via WebSocket
- Calibração do ambiente
- Coleta e treinamento de dados ML
- Gerenciamento de zonas RSSI
- Configuração de notificações (Telegram, WhatsApp, Webhook)
- Exportação de dados (CSV, JSON, ZIP)
- Métricas de saúde e Prometheus

---

## Autenticação

A API local não requer autenticação. O acesso é restrito à rede local (localhost).

---

## Grupos de Endpoints

### Monitor (`/api/signal`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/signal/current` | Sinal e detecção atuais |
| POST | `/api/signal/start` | Inicia monitoramento |
| POST | `/api/signal/stop` | Para monitoramento |
| GET | `/api/config` | Configuração atual |
| PUT | `/api/config` | Atualiza configuração |
| POST | `/api/config/power-save/enable` | Ativa modo economia de energia |
| POST | `/api/config/power-save/disable` | Desativa modo economia de energia |
| POST | `/api/config/simulation/enable` | Ativa modo simulação |
| POST | `/api/config/profiles` | Lista perfis de configuração |
| POST | `/api/config/profiles/{name}/save` | Salva perfil de configuração |
| POST | `/api/config/profiles/{name}/load` | Carrega perfil de configuração |

### Calibração (`/api/calibration`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/calibration/start` | Inicia calibração em background |
| GET | `/api/calibration/progress` | Status da calibração em andamento |
| POST | `/api/calibration/stop` | Cancela calibração |
| GET | `/api/calibration/profiles` | Lista perfis salvos |
| GET | `/api/calibration/profiles/{name}` | Detalhe de um perfil |
| POST | `/api/calibration/profiles/{name}/activate` | Ativa perfil |
| DELETE | `/api/calibration/profiles/{name}` | Remove perfil |

**Exemplo — Iniciar calibração:**
```json
POST /api/calibration/start
{
  "duration_seconds": 60,
  "profile_name": "meu_ambiente"
}
```

### ML (`/api/ml`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/ml/data-collection/start` | Inicia coleta de dados |
| POST | `/api/ml/data-collection/stop` | Para coleta e retorna contagem |
| GET | `/api/ml/data-collection/status` | Status da coleta |
| POST | `/api/ml/label` | Rotula os últimos N segundos |
| GET | `/api/ml/export` | Exporta dataset CSV |
| POST | `/api/ml/train` | Inicia treinamento assíncrono |
| GET | `/api/ml/train/status` | Status do treinamento |
| GET | `/api/ml/models` | Lista modelos disponíveis |
| POST | `/api/ml/models/{name}/activate` | Ativa modelo |

**Exemplo — Rotular evento:**
```json
POST /api/ml/label
{
  "label": "fall_suspected",
  "window_seconds": 10
}
```

**Labels válidos:** `no_presence`, `presence_still`, `presence_moving`, `fall_suspected`, `prolonged_inactivity`

### Zonas (`/api/zones`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/zones` | Lista todas as zonas |
| POST | `/api/zones` | Cria nova zona |
| PUT | `/api/zones/{id}` | Atualiza zona |
| DELETE | `/api/zones/{id}` | Remove zona |
| GET | `/api/zones/current` | Zona em que o sinal atual se encontra |

**Exemplo — Criar zona:**
```json
POST /api/zones
{
  "name": "Sala",
  "rssi_min": -70,
  "rssi_max": -40,
  "alert_config_json": "{}"
}
```

### Notificações (`/api/notifications`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/notifications/config` | Configuração atual |
| PUT | `/api/notifications/config` | Atualiza configuração |
| POST | `/api/notifications/test` | Envia notificação de teste |
| GET | `/api/notifications/logs` | Histórico de notificações |

### Estatísticas (`/api/stats`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/stats?period_hours=24` | Resumo de eventos |
| GET | `/api/stats/patterns` | Padrões comportamentais (heatmap) |
| GET | `/api/stats/anomalies?period_hours=24` | Anomalias críticas |
| GET | `/api/stats/performance` | Métricas de latência/CPU/memória |

### Exportação (`/api/export`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/export/events.csv` | Eventos em CSV |
| GET | `/api/export/events.json` | Eventos em JSON |
| GET | `/api/export/backup.zip` | Backup completo (ZIP) |

### Saúde (`/api/health`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health/ready` | Readiness probe (DB + monitor) |
| GET | `/metrics` | Métricas no formato Prometheus |

---

## WebSocket

**URL:** `ws://localhost:8000/ws`

### Mensagens recebidas

**`live_update`** — Enviado a cada ciclo de detecção:
```json
{
  "rssi": -55.3,
  "event_type": "presence_moving",
  "confidence": 0.87,
  "provider": "heuristic",
  "timestamp": 1700000000.0,
  "is_running": true
}
```

**`calibration_progress`** — Durante calibração:
```json
{
  "type": "calibration_progress",
  "data": {
    "profile_name": "sala",
    "elapsed_seconds": 15.3,
    "duration_seconds": 60,
    "progress_percent": 25.5,
    "phase": "collecting"
  }
}
```

**`anomaly_detected`** — Anomalia crítica (confiança ≥ 85%):
```json
{
  "type": "anomaly_detected",
  "data": {
    "event_type": "fall_suspected",
    "confidence": 0.92,
    "timestamp": 1700000000.0,
    "details": {}
  }
}
```

**`notification_sent`** — Após envio de notificação:
```json
{
  "type": "notification_sent",
  "data": {
    "channel": "telegram",
    "event_type": "fall_suspected",
    "confidence": 0.92,
    "success": true,
    "recipient": ""
  }
}
```

---

## Tipos de Evento

| Código | Descrição | Severidade |
|--------|-----------|------------|
| `no_presence` | Sem presença detectada | — |
| `presence_still` | Presença parada | Baixa |
| `presence_moving` | Presença em movimento | Baixa |
| `prolonged_inactivity` | Inatividade prolongada (>30s parado) | Alta |
| `fall_suspected` | Queda suspeita | Crítica |

---

## Exemplos de Uso

### Iniciar monitoramento completo

```bash
# 1. Iniciar backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Iniciar monitoramento
curl -X POST http://localhost:8000/api/signal/start

# 3. Ver sinal atual
curl http://localhost:8000/api/signal/current

# 4. Health check
curl http://localhost:8000/api/health/ready
```

### Calibrar e treinar modelo ML

```bash
# Calibrar (60s)
curl -X POST http://localhost:8000/api/calibration/start \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 60, "profile_name": "escritorio"}'

# Iniciar coleta ML
curl -X POST http://localhost:8000/api/ml/data-collection/start

# Rotular presença parada (últimos 10s)
curl -X POST http://localhost:8000/api/ml/label \
  -H "Content-Type: application/json" \
  -d '{"label": "presence_still", "window_seconds": 10}'

# Treinar modelo
curl -X POST http://localhost:8000/api/ml/train
```
