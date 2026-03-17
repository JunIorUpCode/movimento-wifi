# Notification Service - Serviço de Notificações

Microserviço responsável por enviar notificações multi-canal (Telegram, Email, Webhook) para tenants da plataforma WiFiSense SaaS.

## Funcionalidades

### ✅ Multi-Tenant com Isolamento Completo
- Cada tenant tem sua própria configuração de notificações
- Tokens e secrets isolados por tenant
- Logs de notificações isolados por tenant

### ✅ Canais de Notificação

#### 1. Telegram (Multi-Tenant)
- Usa bot_token específico do tenant
- Suporta múltiplos chat_ids por tenant
- Mensagens formatadas em português com detalhes do evento
- Retry com exponential backoff (até 3 tentativas)

#### 2. Email (SendGrid)
- Templates HTML responsivos em português
- Suporta múltiplos destinatários
- Retry com exponential backoff (até 3 tentativas)
- Respeita quiet_hours e min_confidence

#### 3. Webhook
- Envia POST para URLs configuradas
- Formato JSON: `{event_type, confidence, timestamp, device_id, metadata}`
- Timeout de 10 segundos
- Retry até 3 vezes com exponential backoff
- Suporta assinatura HMAC com webhook_secret

### ✅ Filtros de Notificação

#### 1. Min Confidence
- Só envia notificações se `confidence >= min_confidence`
- Configurável por tenant (padrão: 0.7)

#### 2. Quiet Hours
- Suprime notificações durante horários de silêncio
- Formato: `{"start": "22:00", "end": "07:00"}`
- Suporta intervalos que cruzam meia-noite

#### 3. Cooldown
- Evita spam de notificações do mesmo tipo
- Período configurável em segundos (padrão: 300s = 5 minutos)
- Cooldown independente por tipo de evento

### ✅ Segurança

#### Criptografia de Tokens Sensíveis
- `telegram_bot_token` criptografado com Fernet (AES-128)
- `sendgrid_api_key` criptografado
- `webhook_secret` criptografado
- Chave derivada de `ENCRYPTION_KEY` via SHA256

#### Autenticação JWT
- Todos os endpoints requerem JWT token
- Isolamento multi-tenant via `tenant_id` no token

### ✅ Logs de Notificações
- Registra todas as tentativas de envio
- Armazena: canal, destinatário, sucesso/falha, erro, dados do alerta
- Consulta com paginação e filtros (canal, sucesso)

## Arquitetura

```
notification-service/
├── models/                    # Modelos SQLAlchemy
│   ├── notification_config.py # Configuração de notificações
│   └── notification_log.py    # Logs de entrega
├── schemas/                   # Schemas Pydantic
│   ├── notification_config.py # Validação de configuração
│   └── notification_log.py    # Validação de logs
├── channels/                  # Implementação de canais
│   ├── telegram_channel.py    # Canal Telegram
│   ├── email_channel.py       # Canal Email (SendGrid)
│   └── webhook_channel.py     # Canal Webhook
├── services/                  # Lógica de negócio
│   ├── notification_service.py # CRUD de configurações e logs
│   └── notification_worker.py  # Worker RabbitMQ
├── routes/                    # Endpoints FastAPI
│   ├── notification_config.py # Endpoints de configuração
│   └── notification_logs.py   # Endpoints de logs
├── middleware/                # Middlewares
│   └── auth_middleware.py     # Autenticação JWT
├── utils/                     # Utilitários
│   └── encryption.py          # Criptografia de tokens
└── main.py                    # Aplicação FastAPI

```

## Endpoints

### Configuração de Notificações

#### GET /api/notifications/config
Obtém configuração de notificações do tenant.

**Autenticação**: JWT token

**Resposta**:
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "enabled": true,
  "channels": ["telegram", "email", "webhook"],
  "min_confidence": 0.7,
  "cooldown_seconds": 300,
  "quiet_hours": {"start": "22:00", "end": "07:00"},
  "telegram_configured": true,
  "telegram_chat_ids": ["123456789"],
  "email_configured": true,
  "email_recipients": ["user@example.com"],
  "webhook_configured": true,
  "webhook_urls": ["https://example.com/webhook"],
  "updated_at": "2024-01-01T12:00:00",
  "created_at": "2024-01-01T12:00:00"
}
```

#### PUT /api/notifications/config
Atualiza configuração de notificações.

**Autenticação**: JWT token

**Body**:
```json
{
  "enabled": true,
  "channels": ["telegram", "email"],
  "min_confidence": 0.8,
  "cooldown_seconds": 600,
  "quiet_hours": {"start": "22:00", "end": "07:00"},
  "telegram_bot_token": "123456:ABC-DEF",
  "telegram_chat_ids": ["123456789", "987654321"],
  "sendgrid_api_key": "SG.xxx",
  "email_recipients": ["user@example.com"],
  "webhook_urls": ["https://example.com/webhook"],
  "webhook_secret": "my-secret"
}
```

#### POST /api/notifications/test
Testa canal de notificação.

**Autenticação**: JWT token

**Body**:
```json
{
  "channel": "telegram",
  "recipient": "123456789"
}
```

**Resposta**:
```json
{
  "success": true,
  "message": "Teste enviado para 1/1 chat(s)",
  "details": {
    "success": true,
    "sent_to": ["123456789"],
    "failed": []
  }
}
```

### Logs de Notificações

#### GET /api/notifications/logs
Lista logs de notificações com paginação e filtros.

**Autenticação**: JWT token

**Query Parameters**:
- `page`: Número da página (padrão: 1)
- `page_size`: Tamanho da página (padrão: 20, máx: 100)
- `channel`: Filtro por canal (telegram, email, webhook)
- `success`: Filtro por sucesso (true/false)

**Resposta**:
```json
{
  "logs": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "event_id": "uuid",
      "channel": "telegram",
      "recipient": "123456789",
      "success": true,
      "error_message": null,
      "alert_data": {...},
      "response_data": {...},
      "retry_count": 0,
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## Notification Worker

### Funcionamento

O `NotificationWorker` consome eventos da fila RabbitMQ `notification_delivery` e processa notificações:

1. **Carrega configuração do tenant** (com tokens descriptografados)
2. **Aplica filtros**:
   - Verifica se notificações estão habilitadas
   - Verifica `min_confidence`
   - Verifica `quiet_hours`
   - Verifica `cooldown`
3. **Envia para canais configurados** (Telegram, Email, Webhook)
4. **Registra logs** de todas as tentativas

### Formato da Mensagem (RabbitMQ)

```json
{
  "tenant_id": "uuid",
  "event_id": "uuid",
  "event_type": "fall_suspected",
  "confidence": 0.95,
  "timestamp": "2024-01-01T12:00:00",
  "device_id": "uuid",
  "device_name": "Sala de Estar",
  "metadata": {}
}
```

## Configuração

### Variáveis de Ambiente

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=wifisense_password
DATABASE_NAME=wifisense_saas

# Redis (para cooldown)
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=wifisense
RABBITMQ_PASSWORD=wifisense_password

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256

# Encryption
ENCRYPTION_KEY=change-me-32-byte-encryption-key
```

## Instalação

### 1. Instalar Dependências

```bash
cd services/notification-service
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e configure as variáveis.

### 3. Iniciar Serviço

```bash
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

## Docker

### Build

```bash
docker build -t wifisense-notification-service -f services/notification-service/Dockerfile .
```

### Run

```bash
docker run -p 8006:8000 \
  -e DATABASE_HOST=postgres \
  -e REDIS_HOST=redis \
  -e RABBITMQ_HOST=rabbitmq \
  wifisense-notification-service
```

## Testes

### Testar Configuração

```bash
# Obter configuração
curl -X GET http://localhost:8006/api/notifications/config \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Atualizar configuração
curl -X PUT http://localhost:8006/api/notifications/config \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "channels": ["telegram"],
    "telegram_bot_token": "123456:ABC-DEF",
    "telegram_chat_ids": ["123456789"]
  }'

# Testar Telegram
curl -X POST http://localhost:8006/api/notifications/test \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"channel": "telegram"}'
```

### Testar Logs

```bash
# Listar logs
curl -X GET "http://localhost:8006/api/notifications/logs?page=1&page_size=20" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Filtrar por canal
curl -X GET "http://localhost:8006/api/notifications/logs?channel=telegram" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Filtrar por sucesso
curl -X GET "http://localhost:8006/api/notifications/logs?success=false" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

## Integração com Event-Service

O `event-service` publica eventos na fila `notification_delivery` quando detecta eventos com `confidence >= min_confidence`:

```python
# event-service publica evento
await rabbitmq_client.publish(
    queue_name="notification_delivery",
    message={
        "tenant_id": str(tenant_id),
        "event_id": str(event_id),
        "event_type": "fall_suspected",
        "confidence": 0.95,
        "timestamp": "2024-01-01T12:00:00",
        "device_id": str(device_id),
        "device_name": "Sala de Estar",
        "metadata": {}
    }
)
```

## Requisitos Implementados

- ✅ **12.1**: Configuração de notificações por tenant
- ✅ **12.2**: Endpoints de configuração e teste
- ✅ **12.3**: Tokens criptografados (bot_token, API keys, secrets)
- ✅ **12.4**: Múltiplos chat IDs por tenant
- ✅ **12.5**: Uso de bot_token específico do tenant
- ✅ **12.6**: Respeito a quiet_hours
- ✅ **12.7**: Filtro de min_confidence
- ✅ **12.8**: Logs de todas as tentativas
- ✅ **9.6**: Suporte a múltiplos canais (Telegram, Email, Webhook)
- ✅ **9.7**: Cooldown para evitar spam
- ✅ **15.1-15.8**: Integração com webhooks
- ✅ **19.5**: Criptografia de dados sensíveis
- ✅ **28.1-28.8**: Sistema de email com SendGrid
- ✅ **37.5**: Isolamento por notification_schema

## Próximos Passos

1. ✅ Implementar testes unitários
2. ✅ Implementar testes de propriedade
3. ⏳ Adicionar métricas Prometheus
4. ⏳ Implementar rate limiting por tenant
5. ⏳ Adicionar suporte a templates customizados
