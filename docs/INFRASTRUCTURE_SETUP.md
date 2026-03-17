# Guia de Configuração da Infraestrutura

Este documento detalha a configuração da infraestrutura base do WiFiSense SaaS Multi-Tenant Platform.

## 📋 Visão Geral

A infraestrutura é composta por:

1. **PostgreSQL 15** - Banco de dados principal com schemas isolados
2. **Redis 7** - Cache e armazenamento de sessões
3. **RabbitMQ 3.12** - Message queue para processamento assíncrono
4. **7 Microserviços** - Serviços independentes em Python/FastAPI

## 🏗️ Arquitetura de Schemas PostgreSQL

### Isolamento por Schema

Cada microserviço tem seu próprio schema no PostgreSQL, garantindo:
- **Isolamento de dados**: Serviços não acessam dados de outros serviços
- **Segurança**: Permissões granulares por schema
- **Manutenibilidade**: Migrações independentes por serviço
- **Performance**: Índices otimizados por domínio

### Schemas Criados

```sql
-- auth_schema: Autenticação e autorização
CREATE SCHEMA auth_schema;

-- tenant_schema: Gerenciamento de tenants
CREATE SCHEMA tenant_schema;

-- device_schema: Dispositivos e heartbeats
CREATE SCHEMA device_schema;

-- license_schema: Licenças e ativações
CREATE SCHEMA license_schema;

-- event_schema: Eventos detectados
CREATE SCHEMA event_schema;

-- notification_schema: Notificações e logs
CREATE SCHEMA notification_schema;

-- billing_schema: Faturamento e Stripe
CREATE SCHEMA billing_schema;
```

### Verificar Schemas

```bash
# Via Docker
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn"

# Resultado esperado:
#      List of schemas
#        Name           |  Owner   
# ----------------------+----------
#  auth_schema          | wifisense
#  billing_schema       | wifisense
#  device_schema        | wifisense
#  event_schema         | wifisense
#  license_schema       | wifisense
#  notification_schema  | wifisense
#  public               | postgres
#  tenant_schema        | wifisense
```

## 🔧 Configuração do PostgreSQL

### Connection Pooling

Cada microserviço mantém um pool de conexões:

```python
# shared/database.py
self.engine = create_async_engine(
    settings.database_url,
    pool_size=20,        # Mínimo de 20 conexões (Requisito 22.3)
    max_overflow=10,     # Até 30 conexões no total
    pool_pre_ping=True   # Verifica conexões antes de usar
)
```

### Search Path

Cada serviço define seu schema no `search_path`:

```python
connect_args={
    "server_settings": {
        "search_path": "auth_schema"  # Schema específico do serviço
    }
}
```

### Extensões Habilitadas

```sql
-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

## 🔴 Configuração do Redis

### Uso do Redis

1. **Cache de dados**: Tenant info, device status, notification config
2. **Sessões JWT**: Armazenamento de tokens ativos
3. **Rate limiting**: Contadores de requisições por tenant
4. **Locks distribuídos**: Coordenação entre serviços

### Estrutura de Chaves

```
# Cache
tenant:{tenant_id}                    # TTL: 3600s (1 hora)
device:{device_id}                    # TTL: 300s (5 minutos)
device_status:{device_id}             # TTL: 60s (1 minuto)
notification_config:{tenant_id}       # TTL: 600s (10 minutos)
license:{activation_key}              # TTL: 3600s (1 hora)

# Rate Limiting
rate_limit:{tenant_id}:{endpoint}     # TTL: 60s (1 minuto)

# Sessions
session:{token_hash}                  # TTL: 86400s (24 horas)
```

### Testar Conexão

```bash
# Conectar ao Redis
docker exec -it wifisense-redis redis-cli -a wifisense_redis_password

# Comandos úteis
127.0.0.1:6379> PING
PONG

127.0.0.1:6379> INFO stats
# Mostra estatísticas

127.0.0.1:6379> KEYS *
# Lista todas as chaves (use com cuidado em produção)

127.0.0.1:6379> GET tenant:123e4567-e89b-12d3-a456-426614174000
# Busca valor de uma chave
```

## 🐰 Configuração do RabbitMQ

### Filas Definidas

```python
QUEUES = {
    "event_processing": {
        "durable": True,
        "prefetch_count": 10,
        "workers": 5
    },
    "notification_delivery": {
        "durable": True,
        "prefetch_count": 5,
        "workers": 3
    },
    "billing_tasks": {
        "durable": True,
        "prefetch_count": 1,
        "workers": 2
    },
    "device_heartbeat": {
        "durable": False,  # Pode perder heartbeats
        "prefetch_count": 100,
        "workers": 2
    }
}
```

### Management UI

Acesse: http://localhost:15672

- **Usuário**: wifisense
- **Senha**: wifisense_password

### Monitorar Filas

```bash
# Via CLI
docker exec wifisense-rabbitmq rabbitmqctl list_queues

# Via API
curl -u wifisense:wifisense_password http://localhost:15672/api/queues
```

## 🐳 Docker Compose

### Estrutura

```yaml
services:
  postgres:    # Porta 5432
  redis:       # Porta 6379
  rabbitmq:    # Portas 5672 (AMQP), 15672 (Management)
  
  # Microserviços
  auth-service:         # Porta 8001
  tenant-service:       # Porta 8002
  device-service:       # Porta 8003
  license-service:      # Porta 8004
  event-service:        # Porta 8005
  notification-service: # Porta 8006
  billing-service:      # Porta 8007
```

### Health Checks

Todos os serviços de infraestrutura têm health checks:

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U wifisense"]
    interval: 10s
    timeout: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

rabbitmq:
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Volumes Persistentes

```yaml
volumes:
  postgres_data:   # Dados do PostgreSQL
  redis_data:      # Dados do Redis
  rabbitmq_data:   # Dados do RabbitMQ
```

## 📦 Módulo Shared

### Estrutura

```
shared/
├── __init__.py          # Inicialização do módulo
├── config.py            # Configurações globais (Settings)
├── logging.py           # Logging estruturado em JSON
├── database.py          # Gerenciamento de conexões PostgreSQL
└── requirements.txt     # Dependências compartilhadas
```

### Uso nos Microserviços

```python
# Importar configurações
from shared.config import settings

# Importar logger
from shared.logging import get_logger
logger = get_logger(__name__)

# Importar database manager
from shared.database import get_auth_db
db_manager = get_auth_db()
```

### PYTHONPATH

O módulo shared é adicionado ao PYTHONPATH nos Dockerfiles:

```dockerfile
COPY shared/ /shared/
ENV PYTHONPATH="${PYTHONPATH}:/shared"
```

## 🔐 Variáveis de Ambiente

### Arquivo .env

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
nano .env
```

### Variáveis Críticas

```bash
# Database
DATABASE_PASSWORD=use-senha-forte-aqui

# Redis
REDIS_PASSWORD=use-senha-forte-aqui

# RabbitMQ
RABBITMQ_PASSWORD=use-senha-forte-aqui

# JWT
JWT_SECRET_KEY=use-chave-secreta-forte-aqui

# Encryption
ENCRYPTION_KEY=use-chave-32-bytes-aqui
```

### Gerar Senhas Fortes

```bash
# Gerar senha aleatória
openssl rand -base64 32

# Gerar chave de 32 bytes para encriptação
openssl rand -hex 32
```

## 🚀 Comandos de Inicialização

### Método 1: Script QuickStart

```bash
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

### Método 2: Makefile

```bash
# Ver comandos disponíveis
make help

# Setup inicial
make setup

# Iniciar infraestrutura
make up-infra

# Iniciar todos os serviços
make up

# Verificar health
make health
```

### Método 3: Docker Compose Manual

```bash
# Iniciar infraestrutura
docker-compose up -d postgres redis rabbitmq

# Aguardar 30 segundos
sleep 30

# Iniciar microserviços
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## 🔍 Troubleshooting

### PostgreSQL não inicia

```bash
# Ver logs
docker-compose logs postgres

# Verificar se porta 5432 está disponível
netstat -tulpn | grep 5432

# Recriar container
docker-compose up -d --force-recreate postgres
```

### Redis não conecta

```bash
# Testar conexão
docker exec wifisense-redis redis-cli -a wifisense_redis_password ping

# Ver logs
docker-compose logs redis

# Verificar senha no .env
grep REDIS_PASSWORD .env
```

### RabbitMQ não inicia

```bash
# Ver logs
docker-compose logs rabbitmq

# Verificar se porta 5672 está disponível
netstat -tulpn | grep 5672

# Acessar Management UI
curl http://localhost:15672
```

### Schemas não foram criados

```bash
# Executar script manualmente
docker exec -i wifisense-postgres psql -U wifisense -d wifisense_saas < scripts/init-schemas.sql

# Verificar schemas
docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn"
```

### Microserviço não responde

```bash
# Ver logs do serviço
docker-compose logs auth-service

# Verificar se container está rodando
docker-compose ps

# Reiniciar serviço
docker-compose restart auth-service

# Reconstruir imagem
docker-compose build --no-cache auth-service
docker-compose up -d auth-service
```

## 📊 Monitoramento

### Verificar Status

```bash
# Status de todos os containers
docker-compose ps

# Health de todos os serviços
make health

# Logs em tempo real
docker-compose logs -f
```

### Métricas PostgreSQL

```bash
# Conexões ativas
docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "SELECT count(*) FROM pg_stat_activity;"

# Tamanho dos schemas
docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "SELECT schema_name, pg_size_pretty(sum(table_size)::bigint) FROM (SELECT pg_catalog.pg_namespace.nspname as schema_name, pg_relation_size(pg_catalog.pg_class.oid) as table_size FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid) t GROUP BY schema_name ORDER BY schema_name;"
```

### Métricas Redis

```bash
# Estatísticas
docker exec wifisense-redis redis-cli -a wifisense_redis_password INFO stats

# Memória usada
docker exec wifisense-redis redis-cli -a wifisense_redis_password INFO memory

# Número de chaves
docker exec wifisense-redis redis-cli -a wifisense_redis_password DBSIZE
```

### Métricas RabbitMQ

```bash
# Listar filas
docker exec wifisense-rabbitmq rabbitmqctl list_queues

# Listar conexões
docker exec wifisense-rabbitmq rabbitmqctl list_connections

# Status do cluster
docker exec wifisense-rabbitmq rabbitmqctl cluster_status
```

## 🔄 Backup e Restore

### Backup PostgreSQL

```bash
# Backup completo
make backup-db

# Ou manualmente
docker exec wifisense-postgres pg_dump -U wifisense wifisense_saas > backup.sql
```

### Restore PostgreSQL

```bash
# Restore
make restore-db FILE=backups/backup_20240101_120000.sql

# Ou manualmente
docker exec -i wifisense-postgres psql -U wifisense wifisense_saas < backup.sql
```

## 📚 Próximos Passos

Após configurar a infraestrutura:

1. ✅ **Task 1 Concluída**: Estrutura base e infraestrutura
2. ⏭️ **Task 2**: Implementar auth-service (autenticação JWT)
3. ⏭️ **Task 3**: Implementar tenant-service (CRUD de tenants)
4. ⏭️ **Task 4**: Implementar device-service (registro de dispositivos)

Consulte [tasks.md](../.kiro/specs/saas-multi-tenant-platform/tasks.md) para detalhes das próximas tarefas.
