# WiFiSense SaaS - Documentação Master

> **Documento Único e Vivo** - Toda atualização no projeto deve ser refletida aqui.
> 
> **Última Atualização:** 2024-01-15
> 
> **Status do Projeto:** 🟡 Em Planejamento

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura de Microserviços](#arquitetura-de-microserviços)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Banco de Dados](#banco-de-dados)
5. [Microserviços](#microserviços)
6. [APIs](#apis)
7. [Fluxos Principais](#fluxos-principais)
8. [Segurança](#segurança)
9. [Deployment](#deployment)
10. [Guia de Desenvolvimento](#guia-de-desenvolvimento)
11. [Changelog](#changelog)
12. [Status de Implementação](#status-de-implementação)

---

## 🎯 Visão Geral

### O que é o WiFiSense SaaS?

Plataforma SaaS multi-tenant para monitoramento de presença e movimento usando sinais Wi-Fi (RSSI/CSI).

### Modelo de Negócio

**Dois Modos de Instalação:**
- **Hardware Dedicado:** Raspberry Pi pré-configurado (Plano PREMIUM)
- **Software Instalável:** Windows/Linux PC (Plano BÁSICO)

**Dois Planos:**
- **BÁSICO (R$ 29,90/mês):** RSSI, detecção de presença e movimento
- **PREMIUM (R$ 79,90/mês):** CSI, detecção avançada incluindo quedas

### Objetivos Técnicos

- ✅ Suportar 10,000+ tenants simultâneos
- ✅ Latência < 2 segundos para processamento
- ✅ Isolamento completo de dados entre tenants
- ✅ 99.5% uptime
- ✅ Escalabilidade horizontal

---

## 🏗️ Arquitetura de Microserviços

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENTE (Dispositivos)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Raspberry Pi │  │ Windows PC   │  │  Linux PC    │      │
│  │ (Agente)     │  │ (Agente)     │  │  (Agente)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Nginx)                     │
│                    Load Balancer + SSL/TLS                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  auth-service    │ │ tenant-service   │ │ device-service   │
│  (Port 8001)     │ │ (Port 8002)      │ │ (Port 8003)      │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │                    ▼                    │
         │          ┌──────────────────┐          │
         │          │ license-service  │          │
         │          │ (Port 8004)      │          │
         │          └────────┬─────────┘          │
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  event-service   │ │notification-svc  │ │ billing-service  │
│  (Port 8005)     │ │ (Port 8006)      │ │ (Port 8007)      │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────────────────────┐  ┌──────────────────────────┐
│     PostgreSQL (Único DB)       │  │   Redis + RabbitMQ       │
│  ┌─────────────────────────┐   │  │  ┌────────┐ ┌─────────┐  │
│  │ auth_schema             │   │  │  │ Cache  │ │ Queues  │  │
│  │ tenant_schema           │   │  │  └────────┘ └─────────┘  │
│  │ device_schema           │   │  └──────────────────────────┘
│  │ license_schema          │   │
│  │ event_schema            │   │
│  │ notification_schema     │   │
│  │ billing_schema          │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### Princípios da Arquitetura

1. **Isolamento:** Cada microserviço é independente
2. **Comunicação:** APIs REST + RabbitMQ para async
3. **Dados:** PostgreSQL único com schemas isolados
4. **Escalabilidade:** Horizontal (adicionar instâncias)
5. **Observabilidade:** Logs estruturados + métricas

---

## 💻 Stack Tecnológico

### Backend (Microserviços)
- **Linguagem:** Python 3.11+
- **Framework:** FastAPI (async/await)
- **ORM:** SQLAlchemy (async)
- **Validação:** Pydantic

### Frontend (Painéis)
- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **State:** TanStack Query
- **Styling:** Tailwind CSS
- **Charts:** Recharts

### Agente Local
- **Linguagem:** Python 3.11+
- **Buffer:** SQLite
- **Instaladores:** PyInstaller + NSIS/fpm

### Infraestrutura
- **Database:** PostgreSQL 15+
- **Cache:** Redis 7+
- **Queue:** RabbitMQ 3.12+
- **Gateway:** Nginx
- **Container:** Docker + Docker Compose
- **Orquestração:** Kubernetes (produção)

### Monitoramento
- **Métricas:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing:** OpenTelemetry

### Serviços Externos
- **Pagamentos:** Stripe
- **Email:** SendGrid
- **CDN:** CloudFlare

---

## 🗄️ Banco de Dados

### Estratégia: PostgreSQL com Schemas Isolados

**Um único banco de dados, schemas separados por microserviço:**

```sql
wifisense_db
├── auth_schema          -- Autenticação e usuários
├── tenant_schema        -- Tenants e configurações
├── device_schema        -- Dispositivos e heartbeats
├── license_schema       -- Licenças e ativações
├── event_schema         -- Eventos detectados
├── notification_schema  -- Configurações e logs de notificações
└── billing_schema       -- Faturas e pagamentos
```

### Vantagens

- ✅ Gerenciamento simplificado (um backup, uma conexão)
- ✅ Transações entre schemas quando necessário
- ✅ Menor custo operacional
- ✅ Isolamento lógico mantido
- ✅ Migrations mais fáceis

### Regras de Acesso

- Cada microserviço acessa **apenas seu schema**
- Comunicação entre serviços via **API REST** (não via banco)
- Todas as queries incluem **tenant_id** para isolamento

---

## 🔧 Microserviços

### 1. auth-service (Port 8001)

**Responsabilidade:** Autenticação JWT e autorização

**Schema:** `auth_schema`

**Endpoints:**
- `POST /api/auth/register` - Registro de tenant
- `POST /api/auth/login` - Login (retorna JWT)
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Invalidar token

**Tecnologias:**
- JWT com expiração de 24h
- Bcrypt (12 rounds) para senhas
- Rate limiting (100 req/min)
- Account lockout (5 falhas = 30min bloqueio)

---

### 2. tenant-service (Port 8002)

**Responsabilidade:** Gerenciamento de tenants

**Schema:** `tenant_schema`

**Endpoints:**
- `POST /api/admin/tenants` - Criar tenant (admin)
- `GET /api/admin/tenants` - Listar tenants
- `GET /api/admin/tenants/{id}` - Detalhes
- `PUT /api/admin/tenants/{id}` - Atualizar
- `DELETE /api/admin/tenants/{id}` - Deletar (cascade)
- `POST /api/admin/tenants/{id}/suspend` - Suspender
- `POST /api/admin/tenants/{id}/activate` - Ativar

**Funcionalidades:**
- Trial de 7 dias automático
- Emails de lembrete (3 dias, 1 dia antes)
- Suspensão automática após trial

---

### 3. device-service (Port 8003)

**Responsabilidade:** Gerenciamento de dispositivos

**Schema:** `device_schema`

**Endpoints:**
- `POST /api/devices/register` - Registrar dispositivo
- `GET /api/devices` - Listar dispositivos do tenant
- `GET /api/devices/{id}` - Detalhes
- `PUT /api/devices/{id}` - Atualizar config
- `DELETE /api/devices/{id}` - Desativar
- `POST /api/devices/{id}/heartbeat` - Heartbeat (60s)
- `POST /api/devices/{id}/data` - Enviar dados

**Funcionalidades:**
- Detecção automática de hardware (CSI capable)
- Validação de plano vs hardware
- Heartbeat monitoring (offline após 3 falhas)
- Métricas de saúde (CPU, memória, disco)

---

### 4. license-service (Port 8004)

**Responsabilidade:** Sistema de licenciamento

**Schema:** `license_schema`

**Endpoints:**
- `POST /api/admin/licenses` - Gerar licença (admin)
- `GET /api/admin/licenses` - Listar licenças
- `GET /api/admin/licenses/{id}` - Detalhes
- `PUT /api/admin/licenses/{id}/revoke` - Revogar
- `PUT /api/admin/licenses/{id}/extend` - Estender
- `POST /api/licenses/validate` - Validar chave

**Funcionalidades:**
- Geração criptográfica de chaves (XXXX-XXXX-XXXX-XXXX)
- Validação online a cada 24h
- Limite de dispositivos por licença
- Expiração automática

---

### 5. event-service (Port 8005)

**Responsabilidade:** Processamento de eventos

**Schema:** `event_schema`

**Endpoints:**
- `GET /api/events` - Listar eventos (paginado)
- `GET /api/events/{id}` - Detalhes
- `GET /api/events/timeline` - Timeline com filtros
- `GET /api/events/stats` - Estatísticas
- `POST /api/events/{id}/feedback` - Marcar falso positivo

**Funcionalidades:**
- Detecção RSSI (BÁSICO): presence, movement, inactivity
- Detecção CSI (PREMIUM): fall_suspected + acima
- Broadcast via WebSocket
- Persistência com confidence >= 0.7

---

### 6. notification-service (Port 8006)

**Responsabilidade:** Envio de notificações

**Schema:** `notification_schema`

**Endpoints:**
- `GET /api/notifications/config` - Obter config
- `PUT /api/notifications/config` - Atualizar config
- `POST /api/notifications/test` - Testar canal
- `GET /api/notifications/logs` - Logs de entrega

**Funcionalidades:**
- Multi-canal: Telegram, email, webhook
- Filtros: min_confidence, quiet_hours, cooldown
- Bot Telegram multi-tenant (cada tenant usa seu bot)
- Retry com exponential backoff
- Logs de todas as tentativas

---

### 7. billing-service (Port 8007)

**Responsabilidade:** Faturamento e pagamentos

**Schema:** `billing_schema`

**Endpoints:**
- `GET /api/billing/subscription` - Assinatura atual
- `POST /api/billing/upgrade` - Upgrade de plano
- `POST /api/billing/payment-method` - Atualizar método
- `GET /api/billing/invoices` - Histórico
- `GET /api/billing/usage` - Estatísticas de uso

**Funcionalidades:**
- Geração automática de faturas (dia 1 do mês)
- Integração com Stripe
- Descontos por volume (10% para 3+, 20% para 10+)
- Retry de pagamentos falhados (3 tentativas)
- Suspensão automática após 3 falhas

---

## 📡 APIs

### Autenticação

Todos os endpoints (exceto `/auth/login` e `/auth/register`) requerem JWT token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Formato de Resposta

**Sucesso:**
```json
{
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Erro:**
```json
{
  "error": {
    "code": "TENANT_NOT_FOUND",
    "message": "Tenant não encontrado",
    "request_id": "req_xyz789"
  }
}
```

### Rate Limiting

- **Padrão:** 100 req/min, 1000 req/hora
- **Device data:** Ilimitado
- **Admin:** 500 req/min, 5000 req/hora

Headers de resposta:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

---

## 🔄 Fluxos Principais

### 1. Registro de Tenant

```
Admin → POST /api/admin/tenants
  ↓
tenant-service cria tenant
  ↓
Gera tenant_id único
  ↓
Envia email de boas-vindas
  ↓
Ativa trial de 7 dias
```

### 2. Geração de Licença

```
Admin → POST /api/admin/licenses
  ↓
license-service gera chave
  ↓
Formato: XXXX-XXXX-XXXX-XXXX
  ↓
Armazena com tenant_id, plano, device_limit
  ↓
Retorna activation_key
```

### 3. Ativação de Dispositivo

```
Agente Local → Solicita activation_key
  ↓
POST /api/devices/register {activation_key, hardware_info}
  ↓
device-service valida via license-service
  ↓
Verifica device_limit
  ↓
Cria device_id e JWT token
  ↓
Marca licença como 'activated'
  ↓
Retorna credenciais ao agente
```

### 4. Captura e Detecção de Eventos

```
Agente Local captura sinal (1s)
  ↓
Processa features localmente
  ↓
Comprime dados (gzip)
  ↓
POST /api/devices/{id}/data
  ↓
event-service recebe e publica na fila
  ↓
Worker consome da fila
  ↓
Executa algoritmo de detecção
  ↓
Se confidence >= 0.7:
  ├─ Persiste no banco
  ├─ Broadcast via WebSocket
  └─ Publica na fila de notificações
```

### 5. Envio de Notificações

```
notification-service consome fila
  ↓
Carrega config do tenant
  ↓
Aplica filtros (min_confidence, quiet_hours, cooldown)
  ↓
Se passa filtros:
  ├─ Envia via Telegram (bot do tenant)
  ├─ Envia via Email (SendGrid)
  └─ Envia via Webhook (tenant URL)
  ↓
Registra tentativas em notification_logs
```

### 6. Faturamento Mensal

```
Cron (dia 1, 00:00 UTC)
  ↓
billing-service lista tenants ativos
  ↓
Para cada tenant:
  ├─ Calcula charge (dispositivos × preço)
  ├─ Aplica descontos
  ├─ Cria invoice
  └─ Cobra via Stripe
  ↓
Se falha:
  ├─ Envia email ao tenant
  ├─ Agenda retry em 3 dias
  └─ Suspende após 3 falhas
```

---

## 🔒 Segurança

### Autenticação e Autorização

- **JWT:** Tokens com expiração de 24h
- **Bcrypt:** Hash de senhas com 12 rounds
- **Rate Limiting:** 100 req/min por tenant
- **Account Lockout:** 5 falhas = 30min bloqueio

### Isolamento Multi-Tenant

- **tenant_id** em todas as queries
- Middleware valida tenant_id do JWT
- HTTP 403 para acesso cross-tenant
- WebSocket channels isolados por tenant

### Criptografia

- **Em trânsito:** HTTPS/TLS 1.3
- **Em repouso:** Fernet para dados sensíveis
  - Bot tokens
  - Webhook secrets
  - Payment info

### Headers de Segurança

```http
Strict-Transport-Security: max-age=31536000
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### Audit Logs

Todas as ações são registradas:
- Timestamp
- Tenant ID / Admin ID
- Ação (create, update, delete, suspend)
- Recurso (tenant, device, license)
- Before/After state
- IP address

---

## 🚀 Deployment

### Desenvolvimento Local (Docker Compose)

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/wifisense-saas.git
cd wifisense-saas

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# Subir todos os serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Acessar
# API Gateway: http://localhost:8000
# Admin Panel: http://localhost:3000
# Client Panel: http://localhost:3001
```

### Produção (Kubernetes)

```bash
# Aplicar configurações
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml

# Deploy de serviços
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/services/

# Verificar status
kubectl get pods -n wifisense-prod
kubectl get services -n wifisense-prod
```

---

## 👨‍💻 Guia de Desenvolvimento

### Estrutura de Pastas

```
wifisense-saas/
├── services/
│   ├── auth-service/
│   ├── tenant-service/
│   ├── device-service/
│   ├── license-service/
│   ├── event-service/
│   ├── notification-service/
│   └── billing-service/
├── api-gateway/
├── agent/
├── frontend/
│   ├── admin-panel/
│   └── client-panel/
├── shared/
├── k8s/
├── docker-compose.yml
├── .env.example
└── WIFISENSE_SAAS_MASTER.md
```

### Padrão de Código

**Todos os arquivos Python devem ser 100% comentados em português:**

```python
"""
Módulo de autenticação JWT.

Este módulo implementa a geração e validação de tokens JWT para
autenticação multi-tenant na plataforma WiFiSense SaaS.
"""

def generate_jwt_token(tenant_id: str, email: str) -> str:
    """
    Gera um token JWT para autenticação do tenant.
    
    Args:
        tenant_id: ID único do tenant
        email: Email do tenant
    
    Returns:
        str: Token JWT assinado com expiração de 24 horas
    """
    # Implementação...
```

### Testes

**Executar todos os testes:**
```bash
# Testes unitários
pytest services/*/tests/

# Testes de propriedade
pytest services/*/tests/property_tests/

# Testes de integração
pytest tests/integration/

# Coverage
pytest --cov=services --cov-report=html
```

### Migrations

```bash
# Criar migration
alembic revision --autogenerate -m "Descrição"

# Aplicar migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 📝 Changelog

### [Em Planejamento] - 2024-01-15

**Adicionado:**
- ✅ Documento de requisitos (42 requisitos)
- ✅ Documento de design técnico
- ✅ Documento de tasks (MVP 6 semanas)
- ✅ Arquitetura de microserviços definida
- ✅ Stack tecnológico escolhido (Python + FastAPI)
- ✅ Estratégia de banco de dados (schemas isolados)
- ✅ Sistema de auto-detecção de hardware implementado

**Decisões Técnicas:**
- Python mantido para todo o backend (não migrar)
- Microserviços com schemas isolados (não DBs separados)
- MVP de 6 semanas priorizando funcionalidades essenciais
- Todo código será 100% comentado em português

---

## 📊 Status de Implementação

### Semana 1-2: Fundação Multi-Tenancy
- [ ] 1. Infraestrutura base (0%)
- [ ] 2. auth-service (0%)
- [ ] 3. tenant-service (0%)
- [ ] 4. Checkpoint (0%)

### Semana 2-3: Licenciamento e Dispositivos
- [ ] 5. license-service (0%)
- [ ] 6. device-service (0%)
- [ ] 7. Checkpoint (0%)

### Semana 3-4: Agente Local e Eventos
- [ ] 8. Agente local (0%)
- [ ] 9. event-service (0%)
- [ ] 10. Checkpoint (0%)

### Semana 4-5: Painéis e Notificações
- [ ] 11. notification-service (0%)
- [ ] 12. admin-panel (0%)
- [ ] 13. client-panel (0%)
- [ ] 14. Checkpoint (0%)

### Semana 5-6: Billing e Finalização
- [ ] 15. billing-service (0%)
- [ ] 16. api-gateway (0%)
- [ ] 17. WebSocket (0%)
- [ ] 18. shared/ (0%)
- [ ] 19. Monitoramento (0%)
- [ ] 20. Instaladores (0%)
- [ ] 21. Backup/DR (0%)
- [ ] 22. Checkpoint Final (0%)

**Progresso Geral:** 0% (0/22 tarefas principais)

---

## 🔗 Links Úteis

### Documentação Técnica
- [Requisitos](/.kiro/specs/saas-multi-tenant-platform/requirements.md)
- [Design](/.kiro/specs/saas-multi-tenant-platform/design.md)
- [Tasks](/.kiro/specs/saas-multi-tenant-platform/tasks.md)

### Documentação Existente
- [Auto-Detecção de Hardware](/backend/docs/AUTO_DETECCAO_HARDWARE.md)
- [Arquitetura Multi-Tenant Telegram](/backend/docs/ARQUITETURA_MULTI_TENANT_TELEGRAM.md)
- [Guia Raspberry Pi](/backend/docs/GUIA_RASPBERRY_PI.md)

### Ferramentas
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [React Docs](https://react.dev/)
- [Stripe API](https://stripe.com/docs/api)

---

**Última atualização:** 2024-01-15 | **Versão:** 1.0.0 | **Status:** 🟡 Em Planejamento
