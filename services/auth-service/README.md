# Auth Service - Serviço de Autenticação e Autorização

## Visão Geral

O Auth Service é responsável por gerenciar autenticação JWT, registro e login de tenants na plataforma WiFiSense SaaS Multi-Tenant.

## Funcionalidades Implementadas

### ✅ Task 2.1: Estrutura do Microserviço
- ✅ Estrutura de pastas (routes/, models/, services/, middleware/)
- ✅ Conexão com auth_schema do PostgreSQL
- ✅ Modelos SQLAlchemy (User, AuditLog)
- ✅ Logging estruturado em português

### ✅ Task 2.2: Geração e Validação de JWT
- ✅ Função `generate_jwt_token(tenant_id, email, role, plan)`
- ✅ Middleware `require_auth()` para validar tokens
- ✅ Middleware `require_admin()` para endpoints administrativos
- ✅ Payload JWT inclui: tenant_id (sub), email, role, plan
- ✅ Expiração configurável (padrão 24 horas)

### ✅ Task 2.4: Endpoints de Autenticação
- ✅ `POST /api/auth/register` - Registro de tenant
- ✅ `POST /api/auth/login` - Login com email/senha
- ✅ `POST /api/auth/refresh` - Refresh de token
- ✅ `POST /api/auth/logout` - Invalidar token
- ✅ Hash de senhas com bcrypt (12 rounds)

### ✅ Task 2.6: Rate Limiting com Redis
- ✅ Middleware de rate limiting (100 req/min por tenant)
- ✅ Retorna HTTP 429 quando limite excedido
- ✅ Headers: X-RateLimit-Limit, X-RateLimit-Remaining
- ✅ Chave Redis: `rate_limit:{tenant_id}:{endpoint}`

### ✅ Task 2.8: Bloqueio de Conta
- ✅ Rastreamento de tentativas de login falhadas no Redis
- ✅ Bloqueio por 30 minutos após 5 falhas em 15 minutos
- ✅ Registro de tentativas em audit_logs (modelo criado)

## Estrutura de Arquivos

```
services/auth-service/
├── main.py                      # Aplicação FastAPI principal
├── Dockerfile                   # Container Docker
├── requirements.txt             # Dependências Python
├── README.md                    # Esta documentação
├── test_auth_service.py         # Testes unitários
├── models/
│   ├── __init__.py
│   ├── user.py                  # Modelo User (tenant)
│   └── audit_log.py             # Modelo AuditLog
├── services/
│   ├── __init__.py
│   ├── auth_service.py          # Lógica de autenticação
│   ├── jwt_service.py           # Geração/validação JWT
│   └── rate_limiter.py          # Rate limiting
├── routes/
│   ├── __init__.py
│   └── auth.py                  # Endpoints de autenticação
└── middleware/
    ├── __init__.py
    └── auth_middleware.py       # Middlewares de auth
```

## Modelos de Dados

### User (auth_schema.users)
```python
- id: UUID (PK)
- email: String (unique, indexed)
- password_hash: String (bcrypt, 12 rounds)
- name: String
- plan_type: Enum (basic, premium)
- status: Enum (trial, active, suspended, expired)
- trial_ends_at: DateTime
- created_at: DateTime
- updated_at: DateTime
```

### AuditLog (auth_schema.audit_logs)
```python
- id: UUID (PK)
- tenant_id: UUID (indexed)
- admin_id: UUID
- action: String (indexed)
- resource_type: String
- resource_id: UUID
- before_state: JSONB
- after_state: JSONB
- ip_address: String
- timestamp: DateTime (indexed)
```

## Endpoints da API

### POST /api/auth/register
Registra um novo tenant no sistema.

**Request:**
```json
{
  "email": "tenant@example.com",
  "password": "senha_segura_123",
  "name": "Nome do Tenant",
  "plan_type": "basic"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "tenant@example.com",
  "plan": "basic"
}
```

### POST /api/auth/login
Autentica tenant e retorna token JWT.

**Request:**
```json
{
  "email": "tenant@example.com",
  "password": "senha_segura_123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "tenant@example.com",
  "plan": "basic"
}
```

**Erros:**
- `401`: Credenciais inválidas
- `401`: Conta bloqueada (5 tentativas falhadas)

### POST /api/auth/refresh
Renova token JWT.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "tenant@example.com",
  "plan": "basic"
}
```

### POST /api/auth/logout
Invalida token JWT (adiciona à blacklist).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

### GET /health
Health check do serviço.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "database": "healthy",
  "redis": "healthy"
}
```

## Segurança

### Hash de Senhas
- Algoritmo: bcrypt
- Rounds: 12 (conforme requisito 19.3)
- Formato: `$2b$12$...`

### JWT Tokens
- Algoritmo: HS256
- Expiração: 24 horas (configurável)
- Payload inclui: tenant_id, email, role, plan

### Rate Limiting
- Limite: 100 requisições/minuto por tenant
- Armazenamento: Redis
- Headers de resposta: X-RateLimit-Limit, X-RateLimit-Remaining

### Bloqueio de Conta
- Máximo: 5 tentativas de login falhadas
- Janela: 15 minutos
- Duração do bloqueio: 30 minutos
- Armazenamento: Redis

## Variáveis de Ambiente

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wifisense
DATABASE_PASSWORD=wifisense_password
DATABASE_NAME=wifisense_saas

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=wifisense_redis_password

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application
LOG_LEVEL=INFO
DEBUG=false
```

## Como Executar

### Desenvolvimento Local

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente (criar arquivo .env)

3. Iniciar serviço:
```bash
uvicorn main:app --reload --port 8001
```

### Docker

1. Build da imagem:
```bash
docker build -t wifisense-auth-service -f services/auth-service/Dockerfile .
```

2. Executar container:
```bash
docker run -p 8001:8000 --env-file .env wifisense-auth-service
```

### Docker Compose

```bash
docker-compose up auth-service
```

## Testes

### Executar Testes Unitários
```bash
cd services/auth-service
python test_auth_service.py
```

### Testes Implementados
- ✅ Hash de senha com bcrypt (12 rounds)
- ✅ Geração de token JWT com payload correto
- ✅ Expiração de token JWT após 24 horas
- ✅ Verificação de rounds do bcrypt

## Requisitos Atendidos

- ✅ **1.1**: Multi-tenancy com tenant_id em todas as tabelas
- ✅ **1.2**: JWT token contém tenant_id, role e plan
- ✅ **19.2**: JWT com expiração de 24 horas
- ✅ **19.3**: Hash de senhas com bcrypt (12 rounds)
- ✅ **19.4**: Rate limiting de 100 req/min por tenant
- ✅ **19.6**: Bloqueio após 5 falhas em 15 minutos
- ✅ **19.7**: Bloqueio dura 30 minutos
- ✅ **34.1-34.4**: Headers de rate limit e HTTP 429

## Próximos Passos

### Testes de Propriedade (Opcionais)
- [ ] Task 2.3: Property test para JWT Token Contains Tenant ID
- [ ] Task 2.5: Property test para Password Bcrypt Hashing
- [ ] Task 2.7: Property test para Rate Limit Enforcement
- [ ] Task 2.9: Testes unitários adicionais

### Integrações
- [ ] Integração com tenant-service para validação de status
- [ ] Integração com audit-service para logs centralizados
- [ ] Métricas Prometheus para monitoramento

## Logs Estruturados

Todos os logs são emitidos em formato JSON estruturado:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "name": "auth-service",
  "levelname": "INFO",
  "message": "Login bem-sucedido: tenant@example.com",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "tenant@example.com",
  "plan": "basic"
}
```

## Autor

Implementado como parte do WiFiSense SaaS Multi-Tenant Platform - Task 2.
