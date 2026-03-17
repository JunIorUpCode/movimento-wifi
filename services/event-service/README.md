# Event Service - Serviço de Processamento de Eventos

Microserviço responsável por processar dados de sinais Wi-Fi, detectar eventos e gerenciar consultas de eventos.

## Funcionalidades

### 1. Recepção de Dados
- **POST /api/devices/{id}/data**: Recebe dados processados do agente local
- Valida JWT token do dispositivo
- Valida plano vs tipo de dados (BÁSICO não aceita CSI)
- Publica dados na fila RabbitMQ para processamento assíncrono

### 2. Processamento de Eventos
- Consome dados da fila RabbitMQ
- Carrega configuração do tenant (thresholds, min_confidence)
- Executa algoritmos de detecção:
  - **RSSI** (plano BÁSICO): Detecção baseada em força de sinal
  - **CSI** (plano PREMIUM): Detecção avançada com dados de canal
- Detecta eventos: presence, movement, fall_suspected, prolonged_inactivity

### 3. Persistência de Eventos
- Salva eventos com confidence >= 0.7 no banco de dados
- Inclui tenant_id, device_id, event_type, confidence, timestamp, metadata
- Índices otimizados para queries eficientes

### 4. Broadcast WebSocket
- Publica eventos em canal WebSocket específico do tenant
- Formato: {event_type, confidence, timestamp, device_id, metadata}
- Isolamento multi-tenant: tenant A não recebe eventos de tenant B

### 5. Consulta de Eventos
- **GET /api/events**: Lista eventos do tenant (paginado)
- **GET /api/events/{id}**: Detalhes do evento
- **GET /api/events/timeline**: Timeline com filtros
- **GET /api/events/stats**: Estatísticas de eventos
- **POST /api/events/{id}/feedback**: Marcar falso positivo

### 6. WebSocket Real-Time
- **WS /ws**: Conexão WebSocket para eventos em tempo real
- Requer JWT token para autenticação
- Heartbeat a cada 30-60 segundos

## Arquitetura

```
┌─────────────┐
│ Agente Local│
└──────┬──────┘
       │ POST /api/devices/{id}/data
       ▼
┌─────────────────────────────────┐
│   Event Service (FastAPI)       │
│                                  │
│  ┌────────────────────────────┐ │
│  │ device_data.py             │ │
│  │ - Valida JWT               │ │
│  │ - Valida plano vs dados    │ │
│  │ - Publica em RabbitMQ      │ │
│  └────────────────────────────┘ │
└─────────────┬───────────────────┘
              │
              ▼
       ┌─────────────┐
       │  RabbitMQ   │
       │ event_queue │
       └──────┬──────┘
              │
              ▼
┌─────────────────────────────────┐
│   EventProcessor (Worker)       │
│                                  │
│  ┌────────────────────────────┐ │
│  │ 1. Consome fila            │ │
│  │ 2. Carrega config tenant   │ │
│  │ 3. Executa detecção        │ │
│  │ 4. Persiste evento (DB)    │ │
│  │ 5. Enfileira notificação   │ │
│  │ 6. Broadcast WebSocket     │ │
│  └────────────────────────────┘ │
└─────────────┬───────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌────────────┐  ┌──────────┐
│ PostgreSQL │  │ WebSocket│
│event_schema│  │ Clients  │
└────────────┘  └──────────┘
```

## Algoritmos de Detecção

### RSSI-Based (Plano BÁSICO)

Usa features simples:
- `rssi_normalized`: Força do sinal normalizada (0.0-1.0)
- `signal_variance`: Variância do sinal
- `rate_of_change`: Taxa de mudança
- `instability_score`: Score de instabilidade

**Eventos Detectados**:
- **presence**: Sinal forte + alta variância
- **movement**: Alta taxa de mudança
- **prolonged_inactivity**: Baixa instabilidade com presença

### CSI-Based (Plano PREMIUM)

Usa features avançadas:
- `csi_amplitude`: Amplitude do CSI
- `csi_variance`: Variância do CSI
- `doppler_shift`: Deslocamento Doppler

**Eventos Detectados**:
- **presence**: Alta amplitude + variância (confidence 0.92)
- **movement**: Doppler shift detectado (confidence 0.88)
- **fall_suspected**: Padrão de queda no CSI (confidence 0.85)
- **prolonged_inactivity**: Baixa variância com presença

## Modelo de Dados

### Event

```python
{
    "id": UUID,
    "tenant_id": UUID,
    "device_id": UUID,
    "event_type": "presence|movement|fall_suspected|prolonged_inactivity",
    "confidence": float (0.0-1.0),
    "timestamp": datetime,
    "metadata": dict,
    "is_false_positive": bool,
    "user_notes": str,
    "created_at": datetime
}
```

### Índices

- `idx_events_tenant_id`: Para isolamento multi-tenant
- `idx_events_device_id`: Para filtrar por dispositivo
- `idx_events_timestamp`: Para ordenação temporal
- `idx_events_tenant_timestamp`: Para queries paginadas
- `idx_events_tenant_type_time`: Para filtros por tipo

## Configuração

### Variáveis de Ambiente

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=wifisense_password
DATABASE_NAME=wifisense_saas

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=wifisense
RABBITMQ_PASSWORD=wifisense_password

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Application
LOG_LEVEL=INFO
```

## Executar Localmente

### 1. Instalar Dependências

```bash
cd services/event-service
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

```bash
# Criar schema event_schema no PostgreSQL
psql -U wifisense -d wifisense_saas -c "CREATE SCHEMA IF NOT EXISTS event_schema;"
```

### 3. Iniciar Serviço

```bash
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### 4. Testar Endpoints

```bash
# Health check
curl http://localhost:8004/health

# Listar eventos (requer JWT)
curl -H "Authorization: Bearer <token>" http://localhost:8004/api/events

# Conectar WebSocket
wscat -c "ws://localhost:8004/ws?token=<jwt_token>"
```

## Docker

### Build

```bash
docker build -t wifisense/event-service:latest .
```

### Run

```bash
docker run -p 8004:8000 \
  -e DATABASE_HOST=postgres \
  -e RABBITMQ_HOST=rabbitmq \
  wifisense/event-service:latest
```

## Testes

### Executar Testes Unitários

```bash
pytest test_event_service.py -v
```

### Executar Testes de Propriedade

```bash
pytest test_event_properties.py -v
```

## Integração com Outros Serviços

### device-service
- Valida JWT tokens de dispositivos
- Verifica plano do tenant

### notification-service
- Publica tarefas de notificação na fila `notification_delivery`

### tenant-service
- Carrega configuração do tenant (thresholds, min_confidence)

## Isolamento Multi-Tenant

Todas as queries incluem filtro por `tenant_id`:

```python
# ✅ CORRETO - Com isolamento
events = await session.execute(
    select(Event).where(Event.tenant_id == tenant_id)
)

# ❌ ERRADO - Sem isolamento
events = await session.execute(
    select(Event)  # Retorna eventos de todos os tenants!
)
```

## Performance

- **Latência de processamento**: < 2 segundos
- **Throughput**: 10,000 dispositivos simultâneos
- **WebSocket connections**: 1,000 por instância
- **Paginação**: Máximo 100 eventos por página

## Monitoramento

### Métricas Prometheus

- `event_processing_duration_seconds`: Tempo de processamento
- `events_detected_total`: Total de eventos detectados
- `events_by_type`: Eventos por tipo
- `websocket_connections`: Conexões WebSocket ativas

### Logs Estruturados

Todos os logs incluem `tenant_id` e `device_id` para rastreamento.

## Troubleshooting

### RabbitMQ não conecta
- Verificar se RabbitMQ está rodando: `docker ps | grep rabbitmq`
- Verificar credenciais em `.env`

### WebSocket não recebe eventos
- Verificar token JWT válido
- Verificar que tenant_id está correto
- Verificar logs do EventProcessor

### Eventos não são detectados
- Verificar thresholds de configuração do tenant
- Verificar que confidence >= min_confidence_to_store (0.7)
- Verificar logs do EventDetector
