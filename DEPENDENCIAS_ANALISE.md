# Análise Completa de Dependências - WiFiSense SaaS Platform

## Resumo Executivo

Análise completa do arquivo tasks.md identificando TODAS as dependências Python necessárias para implementar a plataforma WiFiSense SaaS multi-tenant.

## Dependências por Categoria

### 1. Framework Web e API (FastAPI)
- **fastapi** - Framework web assíncrono para APIs REST
- **uvicorn[standard]** - Servidor ASGI para FastAPI
- **python-multipart** - Suporte para upload de arquivos
- **websockets** - Suporte para WebSocket (real-time)

### 2. Banco de Dados (PostgreSQL)
- **sqlalchemy** - ORM para PostgreSQL
- **asyncpg** - Driver assíncrono PostgreSQL (REQUER COMPILAÇÃO C++)
- **psycopg2-binary** - Driver PostgreSQL alternativo (REQUER COMPILAÇÃO C++)
- **alembic** - Migrations de banco de dados

### 3. Cache e Filas (Redis e RabbitMQ)
- **redis** - Cliente Redis para cache e rate limiting
- **aio-pika** - Cliente assíncrono RabbitMQ para filas de mensagens

### 4. Autenticação e Segurança
- **pyjwt** - Geração e validação de tokens JWT
- **python-jose[cryptography]** - JWT com suporte criptográfico
- **bcrypt** - Hash de senhas (12 rounds)
- **passlib[bcrypt]** - Biblioteca de hashing de senhas
- **cryptography** - Criptografia de dados sensíveis (Fernet)

### 5. Validação e Configuração
- **pydantic** - Validação de dados e schemas
- **pydantic-settings** - Gerenciamento de configurações
- **python-dotenv** - Carregamento de variáveis de ambiente
- **pyyaml** - Parser de arquivos YAML

### 6. Notificações
- **python-telegram-bot** - Integração com Telegram Bot API
- **sendgrid** - Envio de emails via SendGrid
- **requests** - HTTP client para webhooks
- **httpx** - HTTP client assíncrono

### 7. Pagamentos
- **stripe** - Integração com Stripe para billing

### 8. Agente Local
- **psutil** - Métricas de sistema (CPU, memória, disco)
- **aiosqlite** - SQLite assíncrono para buffer local

### 9. Testes
- **pytest** - Framework de testes
- **pytest-asyncio** - Suporte para testes assíncronos
- **hypothesis** - Property-based testing
- **pytest-cov** - Cobertura de testes
- **httpx** - Cliente HTTP para testes de API

### 10. Logging e Monitoramento
- **python-json-logger** - Logging estruturado em JSON
- **structlog** - Logging estruturado avançado
- **prometheus-client** - Métricas para Prometheus

### 11. Utilitários
- **python-dateutil** - Manipulação de datas
- **pytz** - Timezones
- **click** - CLI tools

### 12. Frontend (React + TypeScript) - NÃO PYTHON
- Node.js e npm (separado)
- React, TypeScript, Vite, TanStack Query, Tailwind CSS, Recharts

## Dependências com Problemas de Compilação no Windows

### ⚠️ ATENÇÃO: Pacotes que requerem Visual C++ Build Tools

1. **asyncpg** - Driver PostgreSQL assíncrono
2. **psycopg2-binary** - Driver PostgreSQL

### Soluções:

#### Opção 1: Instalar Visual C++ Build Tools (RECOMENDADO para produção)
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Instalar "Desktop development with C++"
- Reiniciar terminal após instalação

#### Opção 2: Usar alternativas sem compilação (PARA DESENVOLVIMENTO)
- Remover asyncpg e psycopg2-binary
- Usar apenas SQLAlchemy com driver padrão
- Rodar testes unitários sem banco de dados real
- Usar Docker para PostgreSQL em produção

#### Opção 3: Usar Docker (MELHOR PARA DESENVOLVIMENTO)
- Rodar todos os serviços em containers Docker
- Evita problemas de compilação no Windows
- Ambiente idêntico à produção

## Dependências por Microserviço

### auth-service
```
fastapi, uvicorn, sqlalchemy, redis, pyjwt, bcrypt, passlib
python-dotenv, pydantic, pydantic-settings, python-json-logger
```

### tenant-service
```
fastapi, uvicorn, sqlalchemy, redis, pyjwt
python-dotenv, pydantic, sendgrid (emails de trial)
```

### license-service
```
fastapi, uvicorn, sqlalchemy, redis, pyjwt, cryptography
python-dotenv, pydantic
```

### device-service
```
fastapi, uvicorn, sqlalchemy, redis, pyjwt
python-dotenv, pydantic, psutil (métricas)
```

### event-service
```
fastapi, uvicorn, sqlalchemy, redis, aio-pika (RabbitMQ)
python-dotenv, pydantic, websockets
```

### notification-service
```
fastapi, uvicorn, sqlalchemy, redis, aio-pika
python-telegram-bot, sendgrid, httpx (webhooks)
python-dotenv, pydantic, cryptography
```

### billing-service
```
fastapi, uvicorn, sqlalchemy, redis, stripe
python-dotenv, pydantic, sendgrid
```

### agent (Agente Local)
```
requests, psutil, aiosqlite, cryptography
python-dotenv, pyyaml
```

### shared (Código Compartilhado)
```
sqlalchemy, redis, python-json-logger, structlog
cryptography, pyyaml, python-dotenv
```

## Estratégia de Instalação Recomendada

### Fase 1: Dependências Básicas (SEM compilação C++)
```bash
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv
pip install pyjwt bcrypt passlib redis python-json-logger
pip install sqlalchemy pyyaml httpx requests
```

### Fase 2: Dependências de Testes
```bash
pip install pytest pytest-asyncio hypothesis pytest-cov
```

### Fase 3: Dependências Específicas (conforme necessário)
```bash
# Notificações
pip install python-telegram-bot sendgrid

# Pagamentos
pip install stripe

# Agente Local
pip install psutil aiosqlite

# Filas
pip install aio-pika

# Monitoramento
pip install prometheus-client structlog
```

### Fase 4: PostgreSQL (USAR DOCKER)
```bash
# NÃO instalar asyncpg/psycopg2-binary no Windows
# Usar Docker Compose para PostgreSQL
docker-compose up postgres
```

## Próximos Passos

1. ✅ Criar requirements.txt consolidado
2. ✅ Instalar dependências básicas
3. ✅ Testar auth-service (já implementado)
4. ⏭️ Implementar tenant-service
5. ⏭️ Implementar license-service
6. ⏭️ Continuar com outros serviços

## Notas Importantes

- **Docker é ESSENCIAL** para desenvolvimento no Windows
- Evitar compilação C++ usando Docker para PostgreSQL
- Testes unitários podem rodar sem banco de dados real
- Usar mocks para testes de integração
- Frontend (React) é separado - usa npm, não pip
