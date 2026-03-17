# Tenant Service - Serviço de Gerenciamento de Tenants

## Visão Geral

O **tenant-service** é responsável pelo gerenciamento completo de tenants (clientes) na plataforma WiFiSense SaaS. Implementa operações CRUD, suspensão/ativação de contas, e gerenciamento automático de períodos de trial.

## Funcionalidades

### CRUD de Tenants
- ✅ Criar novos tenants com período de trial de 7 dias
- ✅ Listar tenants com filtros (status, plano)
- ✅ Obter detalhes de um tenant específico
- ✅ Atualizar informações do tenant
- ✅ Deletar tenant (cascade)

### Gerenciamento de Status
- ✅ Suspender tenant (bloqueia acesso)
- ✅ Ativar tenant (restaura acesso)
- ✅ Verificação automática de trials expirados
- ✅ Envio de lembretes de trial (3 dias e 1 dia antes)

### Isolamento Multi-Tenant
- ✅ Dados armazenados em `tenant_schema` isolado
- ✅ Autenticação via JWT com role `admin`
- ✅ Validação de permissões em todos os endpoints

## Arquitetura

```
tenant-service/
├── models/
│   ├── __init__.py
│   └── tenant.py              # Modelo Tenant com SQLAlchemy
├── services/
│   ├── __init__.py
│   ├── tenant_service.py      # Lógica de negócio
│   └── trial_manager.py       # Gerenciamento de trials
├── routes/
│   ├── __init__.py
│   └── tenant.py              # Endpoints REST
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py     # Autenticação admin
├── main.py                    # Aplicação FastAPI
├── requirements.txt
├── Dockerfile
└── README.md
```

## Endpoints

### Admin Endpoints (requer role `admin`)

#### POST /api/admin/tenants
Cria um novo tenant com trial de 7 dias.

**Request:**
```json
{
  "email": "cliente@example.com",
  "name": "Nome do Cliente",
  "plan_type": "basic"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "cliente@example.com",
  "name": "Nome do Cliente",
  "plan_type": "basic",
  "status": "trial",
  "trial_ends_at": "2024-01-15T00:00:00Z",
  "created_at": "2024-01-08T00:00:00Z",
  "updated_at": "2024-01-08T00:00:00Z",
  "language": "pt-BR",
  "metadata": {}
}
```

#### GET /api/admin/tenants
Lista todos os tenants com filtros opcionais.

**Query Parameters:**
- `status` (opcional): `trial`, `active`, `suspended`, `expired`
- `plan` (opcional): `basic`, `premium`
- `limit` (opcional): Limite de resultados (padrão: 100)
- `offset` (opcional): Offset para paginação (padrão: 0)

**Response:** `200 OK`
```json
{
  "tenants": [...],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/admin/tenants/{tenant_id}
Obtém detalhes de um tenant específico.

**Response:** `200 OK` ou `404 Not Found`

#### PUT /api/admin/tenants/{tenant_id}
Atualiza informações do tenant.

**Request:**
```json
{
  "name": "Novo Nome",
  "plan_type": "premium",
  "language": "en-US",
  "metadata": {"custom_field": "value"}
}
```

**Response:** `200 OK` ou `404 Not Found`

#### DELETE /api/admin/tenants/{tenant_id}
Deleta um tenant permanentemente (cascade).

**Response:** `200 OK` ou `404 Not Found`
```json
{
  "message": "Tenant {id} deletado com sucesso"
}
```

#### POST /api/admin/tenants/{tenant_id}/suspend
Suspende um tenant (bloqueia acesso).

**Response:** `200 OK` ou `404 Not Found`

#### POST /api/admin/tenants/{tenant_id}/activate
Ativa um tenant suspenso (restaura acesso).

**Response:** `200 OK` ou `404 Not Found`

### Health Check

#### GET /health
Verifica saúde do serviço.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "tenant-service",
  "version": "1.0.0",
  "database": "healthy",
  "trial_manager": "running"
}
```

## Modelo de Dados

### Tenant

```python
class Tenant:
    id: UUID                    # Identificador único
    email: str                  # Email (único)
    name: str                   # Nome do tenant
    plan_type: PlanType         # "basic" ou "premium"
    status: TenantStatus        # "trial", "active", "suspended", "expired"
    trial_ends_at: datetime     # Data de fim do trial
    created_at: datetime        # Data de criação
    updated_at: datetime        # Data de última atualização
    language: str               # Idioma preferido (padrão: "pt-BR")
    metadata: dict              # Metadados adicionais (JSON)
```

## Gerenciamento de Trials

O **Trial Manager** executa verificações periódicas:

### Verificação de Trials Expirados
- **Frequência:** A cada 1 hora
- **Ação:** Altera status de `trial` para `expired` quando `trial_ends_at < now()`
- **Requisito:** 18.4

### Lembretes de Trial
- **3 dias antes:** Envia lembrete (a cada 6 horas)
- **1 dia antes:** Envia lembrete (a cada 6 horas)
- **Requisitos:** 18.2, 18.3

> **Nota:** O envio de emails será implementado quando o notification-service estiver pronto.

## Autenticação

Todos os endpoints requerem autenticação via JWT com role `admin`.

**Header:**
```
Authorization: Bearer <jwt_token>
```

**JWT Payload:**
```json
{
  "sub": "admin_id",
  "email": "admin@example.com",
  "role": "admin",
  "exp": 1234567890
}
```

## Variáveis de Ambiente

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=wifisense_password
DATABASE_NAME=wifisense_saas
JWT_SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
DEBUG=false
```

## Executar Localmente

### Com Docker Compose
```bash
docker-compose up tenant-service
```

O serviço estará disponível em: `http://localhost:8002`

### Sem Docker
```bash
cd services/tenant-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Testes

### Criar Tenant
```bash
curl -X POST http://localhost:8002/api/admin/tenants \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "name": "Tenant Teste",
    "plan_type": "basic"
  }'
```

### Listar Tenants
```bash
curl http://localhost:8002/api/admin/tenants \
  -H "Authorization: Bearer <admin_token>"
```

### Suspender Tenant
```bash
curl -X POST http://localhost:8002/api/admin/tenants/{id}/suspend \
  -H "Authorization: Bearer <admin_token>"
```

## Requisitos Implementados

- ✅ **2.1** - Modelo Tenant com campos necessários
- ✅ **2.2** - Criar tenant (admin only)
- ✅ **2.3** - Listar e obter detalhes de tenants
- ✅ **2.4** - Suspender e ativar tenants
- ✅ **2.5** - Bloqueio de API para tenants suspensos
- ✅ **2.6** - Deletar tenant (cascade)
- ✅ **18.1** - Trial de 7 dias na criação
- ✅ **18.2** - Lembrete 3 dias antes do fim
- ✅ **18.3** - Lembrete 1 dia antes do fim
- ✅ **18.4** - Suspensão automática quando trial expira
- ✅ **37.2** - Isolamento por schema (tenant_schema)

## Próximos Passos

1. Integrar com notification-service para envio de emails
2. Implementar testes unitários
3. Implementar testes de propriedade
4. Adicionar métricas e monitoramento
5. Implementar audit logs para ações administrativas

## Dependências

- FastAPI 0.115.0
- SQLAlchemy 2.0.35
- PostgreSQL (via asyncpg)
- PyJWT 2.9.0
- Pydantic 2.9.0

## Logs

O serviço utiliza logging estruturado em JSON:

```json
{
  "timestamp": "2024-01-08T10:00:00Z",
  "level": "INFO",
  "message": "Tenant criado com sucesso: teste@example.com",
  "tenant_id": "uuid",
  "email": "teste@example.com",
  "plan": "basic"
}
```

## Suporte

Para dúvidas ou problemas, consulte a documentação completa em `/docs` (Swagger UI) ou `/redoc` (ReDoc).
