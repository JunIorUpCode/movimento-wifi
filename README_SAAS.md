# WiFiSense SaaS Multi-Tenant Platform

Plataforma SaaS multi-tenant para monitoramento de presença e movimento usando sinais Wi-Fi (RSSI/CSI).

## 📁 Estrutura do Projeto

```
wifisense-saas/
├── services/                      # Microserviços
│   ├── auth-service/             # Autenticação e autorização JWT
│   ├── tenant-service/           # Gerenciamento de tenants
│   ├── device-service/           # Gerenciamento de dispositivos
│   ├── license-service/          # Sistema de licenciamento
│   ├── event-service/            # Processamento de eventos
│   ├── notification-service/     # Notificações multi-canal
│   └── billing-service/          # Faturamento e Stripe
├── shared/                        # Módulo compartilhado
│   ├── config.py                 # Configurações globais
│   ├── logging.py                # Logging estruturado
│   └── database.py               # Gerenciamento de banco de dados
├── scripts/                       # Scripts de setup
│   └── init-schemas.sql          # Inicialização dos schemas PostgreSQL
├── docker-compose.yml            # Orquestração de containers
├── .env.example                  # Exemplo de variáveis de ambiente
└── README_SAAS.md               # Este arquivo
```

## 🏗️ Arquitetura

### Microserviços

Cada serviço é independente e se comunica via:
- **REST API**: Comunicação síncrona entre serviços
- **RabbitMQ**: Processamento assíncrono de eventos
- **Redis**: Cache e sessões compartilhadas

### Isolamento de Dados

- **PostgreSQL com schemas isolados**: Cada microserviço tem seu próprio schema
  - `auth_schema`: Usuários e tokens
  - `tenant_schema`: Contas de clientes
  - `device_schema`: Dispositivos registrados
  - `license_schema`: Licenças e ativações
  - `event_schema`: Eventos detectados
  - `notification_schema`: Configurações e logs de notificações
  - `billing_schema`: Faturas e pagamentos

### Infraestrutura

- **PostgreSQL 15**: Banco de dados principal
- **Redis 7**: Cache e armazenamento de sessões
- **RabbitMQ 3.12**: Message queue para processamento assíncrono

## 🚀 Início Rápido

### Pré-requisitos

- Docker 24.0+
- Docker Compose 2.20+
- 4GB RAM disponível
- 10GB espaço em disco

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 2. Iniciar Infraestrutura

```bash
# Subir PostgreSQL, Redis e RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Aguardar serviços ficarem saudáveis (30-60 segundos)
docker-compose ps
```

### 3. Verificar Schemas PostgreSQL

```bash
# Conectar ao PostgreSQL
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

# Listar schemas
\dn

# Deve mostrar:
# - auth_schema
# - tenant_schema
# - device_schema
# - license_schema
# - event_schema
# - notification_schema
# - billing_schema
```

### 4. Iniciar Microserviços

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Verificar status
docker-compose ps
```

### 5. Testar Health Checks

```bash
# Auth Service
curl http://localhost:8001/health

# Tenant Service
curl http://localhost:8002/health

# Device Service
curl http://localhost:8003/health

# License Service
curl http://localhost:8004/health

# Event Service
curl http://localhost:8005/health

# Notification Service
curl http://localhost:8006/health

# Billing Service
curl http://localhost:8007/health
```

## 🔧 Desenvolvimento

### Estrutura de um Microserviço

```
services/auth-service/
├── main.py                 # Aplicação FastAPI
├── routes/                 # Endpoints da API
├── models/                 # Modelos SQLAlchemy
├── services/               # Lógica de negócio
├── schemas/                # Schemas Pydantic
├── Dockerfile              # Imagem Docker
└── requirements.txt        # Dependências Python
```

### Adicionar Novo Endpoint

1. Criar rota em `routes/`
2. Adicionar lógica em `services/`
3. Definir schemas em `schemas/`
4. Testar localmente

### Logs Estruturados

Todos os serviços usam logging estruturado em JSON:

```python
from shared.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Tenant criado com sucesso",
    tenant_id=tenant_id,
    email=email,
    plan="basic"
)
```

### Conexão com Banco de Dados

```python
from shared.database import get_auth_db

# Obter gerenciador de banco
db_manager = get_auth_db()

# Inicializar
await db_manager.initialize()

# Usar sessão
async with db_manager.get_session() as session:
    result = await session.execute(query)
```

## 📊 Monitoramento

### RabbitMQ Management UI

- URL: http://localhost:15672
- Usuário: `wifisense`
- Senha: `wifisense_password`

### Logs

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f auth-service

# Ver últimas 100 linhas
docker-compose logs --tail=100 auth-service
```

### Health Checks

Todos os serviços expõem endpoint `/health`:

```bash
# Verificar todos os serviços
for port in 8001 8002 8003 8004 8005 8006 8007; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq
done
```

## 🧪 Testes

### Executar Testes Unitários

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov

# Executar testes de um serviço
cd services/auth-service
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=. --cov-report=html
```

## 🔒 Segurança

### Variáveis Sensíveis

- **NUNCA** commitar arquivo `.env`
- Usar secrets do Docker em produção
- Rotacionar `JWT_SECRET_KEY` regularmente
- Usar senhas fortes para PostgreSQL, Redis e RabbitMQ

### Encriptação

- Senhas: bcrypt com 12 rounds (Requisito 19.3)
- Tokens JWT: HS256
- Dados sensíveis: AES-256 via `ENCRYPTION_KEY`

## 📦 Deploy em Produção

### Kubernetes (Recomendado)

```bash
# Aplicar manifests
kubectl apply -f k8s/

# Verificar pods
kubectl get pods -n wifisense-prod
```

### Docker Swarm

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml wifisense
```

## 🐛 Troubleshooting

### Serviço não inicia

```bash
# Verificar logs
docker-compose logs service-name

# Verificar se portas estão disponíveis
netstat -tulpn | grep 8001

# Recriar container
docker-compose up -d --force-recreate service-name
```

### Erro de conexão com PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Testar conexão
docker exec -it wifisense-postgres pg_isready -U wifisense

# Verificar logs do PostgreSQL
docker-compose logs postgres
```

### Erro de conexão com Redis

```bash
# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão
docker exec -it wifisense-redis redis-cli -a wifisense_redis_password ping
```

## 📚 Documentação Adicional

- [Design Document](.kiro/specs/saas-multi-tenant-platform/design.md)
- [Requirements](.kiro/specs/saas-multi-tenant-platform/requirements.md)
- [Tasks](.kiro/specs/saas-multi-tenant-platform/tasks.md)

## 🤝 Contribuindo

1. Criar branch: `git checkout -b feature/nova-funcionalidade`
2. Fazer alterações e commitar
3. Executar testes: `pytest`
4. Push e criar Pull Request

## 📄 Licença

Proprietary - WiFiSense SaaS Platform

## 📞 Suporte

- Email: suporte@wifisense.com
- Documentação: https://docs.wifisense.com
