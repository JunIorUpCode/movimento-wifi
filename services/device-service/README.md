# Device Service - Serviço de Gerenciamento de Dispositivos

## Visão Geral

O Device Service é responsável pelo gerenciamento completo de dispositivos na plataforma WiFiSense SaaS. Implementa registro, configuração, monitoramento e heartbeat de dispositivos.

## Funcionalidades

### ✅ Implementadas

#### 1. Registro de Dispositivos (Task 6.2)
- **POST /api/devices/register** - Registra novo dispositivo com activation_key
- Valida activation_key via license-service
- Verifica limite de dispositivos por licença
- Gera device_id e JWT token para o dispositivo
- Marca licença como 'activated' e associa device_id
- **Requisitos:** 3.2, 3.3, 4.4

#### 2. Gerenciamento de Dispositivos (Task 6.5)
- **GET /api/devices** - Lista dispositivos do tenant
- **GET /api/devices/{id}** - Detalhes do dispositivo
- **PUT /api/devices/{id}** - Atualiza configuração do dispositivo
- **DELETE /api/devices/{id}** - Desativa dispositivo (soft delete)
- **GET /api/devices/{id}/status** - Status em tempo real
- **Requisitos:** 3.5, 3.6, 13.2-13.7

#### 3. Heartbeat de Dispositivos (Task 6.7)
- **POST /api/devices/{id}/heartbeat** - Recebe heartbeat a cada 60s
- Atualiza last_seen timestamp
- Inclui métricas de saúde (CPU, memória, disco)
- Worker automático marca dispositivo como offline após 3 heartbeats perdidos (3 minutos)
- **Requisitos:** 39.1-39.3

#### 4. Detecção de Hardware e Validação de Plano (Task 6.8)
- Recebe hardware_info durante registro (csi_capable, wifi_adapter, os)
- Valida capacidades vs plano subscrito
- Sugere upgrade se BÁSICO tem hardware CSI
- Alerta se PREMIUM não tem hardware CSI
- **Requisitos:** 5.2, 5.3, 27.1-27.8

## Arquitetura

### Estrutura de Pastas

```
services/device-service/
├── models/
│   ├── __init__.py
│   └── device.py              # Modelo Device com status e hardware_type
├── services/
│   ├── __init__.py
│   ├── device_service.py      # CRUD de dispositivos
│   ├── device_registration.py # Registro e validação de licenças
│   └── device_heartbeat.py    # Heartbeat e detecção de offline
├── routes/
│   ├── __init__.py
│   └── device.py              # Endpoints da API
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py     # Autenticação JWT (tenant e device)
├── main.py                    # Aplicação FastAPI
├── requirements.txt
├── Dockerfile
└── README.md
```

### Modelos de Dados

#### Device
```python
{
    "id": "uuid",
    "tenant_id": "uuid",
    "name": "string",
    "hardware_type": "raspberry_pi|windows|linux",
    "status": "online|offline|error",
    "last_seen": "datetime",
    "registered_at": "datetime",
    "hardware_info": {
        "csi_capable": bool,
        "wifi_adapter": "string",
        "os": "string",
        "last_health_metrics": {
            "cpu_percent": float,
            "memory_mb": float,
            "disk_percent": float,
            "timestamp": "datetime"
        }
    },
    "config": {
        "sampling_interval": int,
        "detection_thresholds": {...}
    },
    "jwt_token_hash": "string"
}
```

## Endpoints da API

### Registro de Dispositivos

#### POST /api/devices/register
Registra um novo dispositivo com activation_key.

**Request:**
```json
{
    "activation_key": "XXXX-XXXX-XXXX-XXXX",
    "hardware_info": {
        "type": "raspberry_pi",
        "csi_capable": true,
        "wifi_adapter": "Intel 5300",
        "os": "Linux"
    },
    "device_name": "Sala de Estar"
}
```

**Response (201):**
```json
{
    "device_id": "uuid",
    "jwt_token": "eyJ...",
    "config": {
        "sampling_interval": 1,
        "detection_thresholds": {...}
    },
    "hardware_validation": {
        "valid": true,
        "warnings": [],
        "suggestions": ["Considere upgrade para PREMIUM..."]
    }
}
```

### Gerenciamento de Dispositivos

#### GET /api/devices
Lista todos os dispositivos do tenant autenticado.

**Headers:**
```
Authorization: Bearer <tenant_jwt_token>
```

**Response (200):**
```json
[
    {
        "id": "uuid",
        "tenant_id": "uuid",
        "name": "Sala de Estar",
        "hardware_type": "raspberry_pi",
        "status": "online",
        "last_seen": "2024-01-15T10:30:00Z",
        "registered_at": "2024-01-01T08:00:00Z",
        "hardware_info": {...},
        "config": {...}
    }
]
```

#### GET /api/devices/{id}
Obtém detalhes de um dispositivo específico.

**Headers:**
```
Authorization: Bearer <tenant_jwt_token>
```

**Response (200):**
```json
{
    "id": "uuid",
    "tenant_id": "uuid",
    "name": "Sala de Estar",
    "hardware_type": "raspberry_pi",
    "status": "online",
    "last_seen": "2024-01-15T10:30:00Z",
    "registered_at": "2024-01-01T08:00:00Z",
    "hardware_info": {...},
    "config": {...}
}
```

#### PUT /api/devices/{id}
Atualiza configuração de um dispositivo.

**Headers:**
```
Authorization: Bearer <tenant_jwt_token>
```

**Request:**
```json
{
    "name": "Quarto Principal",
    "config": {
        "sampling_interval": 2,
        "detection_thresholds": {
            "presence": 0.8,
            "movement": 0.75,
            "fall": 0.85
        }
    }
}
```

**Response (200):**
```json
{
    "id": "uuid",
    "name": "Quarto Principal",
    "config": {...},
    ...
}
```

#### DELETE /api/devices/{id}
Desativa um dispositivo (soft delete).

**Headers:**
```
Authorization: Bearer <tenant_jwt_token>
```

**Response (204):** No content

#### GET /api/devices/{id}/status
Obtém status em tempo real de um dispositivo.

**Headers:**
```
Authorization: Bearer <tenant_jwt_token>
```

**Response (200):**
```json
{
    "device_id": "uuid",
    "name": "Sala de Estar",
    "status": "online",
    "last_seen": "2024-01-15T10:30:00Z",
    "seconds_since_last_seen": 15,
    "hardware_type": "raspberry_pi",
    "hardware_info": {
        "last_health_metrics": {
            "cpu_percent": 45.2,
            "memory_mb": 512,
            "disk_percent": 65.8,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
}
```

### Heartbeat

#### POST /api/devices/{id}/heartbeat
Recebe heartbeat de um dispositivo.

**Headers:**
```
Authorization: Bearer <device_jwt_token>
```

**Request:**
```json
{
    "health_metrics": {
        "cpu_percent": 45.2,
        "memory_mb": 512,
        "disk_percent": 65.8
    }
}
```

**Response (200):**
```json
{
    "status": "ok",
    "device_id": "uuid",
    "last_seen": "2024-01-15T10:30:00Z",
    "device_status": "online"
}
```

## Autenticação

### Tenant JWT Token
Usado para endpoints de gerenciamento (GET, PUT, DELETE).

**Payload:**
```json
{
    "sub": "tenant_id",
    "tenant_id": "uuid",
    "email": "tenant@example.com",
    "role": "tenant",
    "exp": 1234567890
}
```

### Device JWT Token
Usado para endpoint de heartbeat.

**Payload:**
```json
{
    "sub": "device_id",
    "tenant_id": "uuid",
    "type": "device",
    "exp": 1234567890
}
```

## Workers em Background

### OfflineDetectionWorker
- Executa a cada 60 segundos
- Verifica dispositivos que não enviaram heartbeat há mais de 3 minutos
- Marca automaticamente como offline
- Registra logs de dispositivos offline detectados

## Integração com Outros Serviços

### License Service
- **POST /api/licenses/validate** - Valida activation_key durante registro
- **POST /api/licenses/activate** - Marca licença como ativada após registro

## Isolamento Multi-Tenant

- Todos os endpoints filtram por `tenant_id` automaticamente
- JWT token contém `tenant_id` para isolamento
- Queries no banco sempre incluem filtro por `tenant_id`
- Tenant A não pode acessar dispositivos de Tenant B

## Configuração

### Variáveis de Ambiente
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=wifisense_password
DATABASE_NAME=wifisense_saas

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

LOG_LEVEL=INFO
```

## Executando o Serviço

### Desenvolvimento Local
```bash
cd services/device-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

### Docker
```bash
docker build -t device-service .
docker run -p 8003:8003 device-service
```

### Docker Compose
```bash
docker-compose up device-service
```

## Health Check

### GET /health
Verifica saúde do serviço.

**Response (200):**
```json
{
    "status": "healthy",
    "service": "device-service",
    "version": "1.0.0",
    "database": "healthy",
    "offline_worker": "running"
}
```

## Testes

### Executar Testes
```bash
pytest test_device_service.py -v
```

### Cobertura de Testes
- Registro de dispositivos com activation_key válida e inválida
- Verificação de limite de dispositivos
- Heartbeat e detecção de offline
- Validação de hardware vs plano
- Isolamento multi-tenant

## Próximos Passos

- [ ] Implementar testes unitários (Task 6.10)
- [ ] Implementar testes de propriedade (Tasks 6.3, 6.4, 6.6, 6.9)
- [ ] Integrar com event-service para processamento de dados
- [ ] Implementar configuração remota via WebSocket

## Requisitos Atendidos

- ✅ 3.2 - Registro de dispositivos com activation_key
- ✅ 3.3 - Validação de activation_key e geração de credentials
- ✅ 3.4 - Armazenamento de metadata de dispositivos
- ✅ 3.5 - Listagem de dispositivos com status
- ✅ 3.6 - Desativação de dispositivos
- ✅ 3.7 - Revogação de credenciais ao remover dispositivo
- ✅ 4.4 - Marcação de licença como ativada
- ✅ 5.2 - Validação de hardware vs plano
- ✅ 5.3 - Sugestão de upgrade
- ✅ 13.2 - GET /api/devices
- ✅ 13.3 - GET /api/devices/{id}
- ✅ 13.4 - PUT /api/devices/{id}
- ✅ 13.5 - DELETE /api/devices/{id}
- ✅ 13.6 - GET /api/devices/{id}/status
- ✅ 27.1-27.8 - Detecção e validação de hardware
- ✅ 39.1 - Heartbeat a cada 60s
- ✅ 39.2 - Detecção de offline após 3 minutos
- ✅ 39.3 - Marcação automática como offline
- ✅ 39.6 - Métricas de saúde no heartbeat
