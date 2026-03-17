# 🚀 Guia de Teste Rápido - WiFiSense SaaS

## Pré-requisitos

✅ Docker Desktop instalado e rodando  
✅ Git Bash ou PowerShell  
✅ Python 3.11+ instalado

## Passo 1: Iniciar Infraestrutura

```bash
# Opção 1: Usando Makefile (recomendado)
make infra-up

# Opção 2: Docker Compose direto
docker-compose up -d postgres redis rabbitmq
```

Aguarde 10-15 segundos para os serviços iniciarem.

## Passo 2: Verificar Infraestrutura

```bash
# Verificar status
make infra-health

# Ou manualmente
docker ps
```

Você deve ver 3 containers rodando:
- `wifisense-postgres`
- `wifisense-redis`
- `wifisense-rabbitmq`

## Passo 3: Verificar Schemas PostgreSQL

```bash
# Verificar schemas criados
make db-check

# Ou manualmente
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn"
```

Deve mostrar 7 schemas:
- auth_schema
- tenant_schema
- device_schema
- license_schema
- event_schema
- notification_schema
- billing_schema

## Passo 4: Testar Auth-Service

```bash
# Teste simples (não requer PostgreSQL)
make test-auth

# Ou manualmente
cd services/auth-service
python test_auth_simple.py
```

Resultado esperado:
```
✓ Teste de hash de senha com bcrypt passou
✓ Teste de geração de JWT passou
✓ Teste de expiração de JWT passou
✓ Teste de conexão com Redis passou

✅ Todos os testes básicos passaram!
```

## Passo 5: Testar Tenant-Service

```bash
# Teste completo (requer PostgreSQL)
make test-tenant

# Ou manualmente
cd services/tenant-service
python test_tenant_service.py
```

Resultado esperado:
```
=== Teste do Tenant Service ===

✅ 1. Criar tenant
✅ 2. Buscar tenant por ID
✅ 3. Listar tenants
✅ 4. Atualizar tenant
✅ 5. Suspender tenant
✅ 6. Ativar tenant
✅ 7. Deletar tenant
✅ 8. Verificar deleção

✅ Todos os testes passaram!
```

## Passo 6: Teste de Integração Completa

```bash
# Teste completo de integração
make test-integration

# Ou manualmente
python scripts/test-integration.py
```

Este teste verifica:
1. ✅ Infraestrutura (PostgreSQL, Redis, RabbitMQ)
2. ✅ Auth-Service (JWT, bcrypt, rate limiting)
3. ✅ Tenant-Service (CRUD, trial, suspensão)
4. ✅ Isolamento Multi-Tenant

## Comandos Úteis

### Ver Logs
```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs específicos
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f rabbitmq
```

### Acessar Serviços

**PostgreSQL:**
```bash
make db-shell
# Ou
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas
```

**Redis:**
```bash
make redis-shell
# Ou
docker exec -it wifisense-redis redis-cli
```

**RabbitMQ Management UI:**
```bash
make rabbitmq-ui
# Ou abra: http://localhost:15672
# Usuário: wifisense
# Senha: wifisense_password
```

### Parar Serviços
```bash
# Parar tudo
make down

# Ou
docker-compose down
```

### Limpar Tudo (CUIDADO: apaga dados)
```bash
make clean

# Ou
docker-compose down -v
```

## Solução de Problemas

### Erro: "Cannot connect to PostgreSQL"
```bash
# Verificar se está rodando
docker ps | grep postgres

# Ver logs
docker-compose logs postgres

# Reiniciar
docker-compose restart postgres
```

### Erro: "Port already in use"
```bash
# Ver o que está usando a porta
netstat -ano | findstr :5432

# Parar o processo
taskkill /PID <PID> /F

# Ou mudar a porta no docker-compose.yml
```

### Erro: "Redis connection refused"
```bash
# Verificar se está rodando
docker ps | grep redis

# Testar conexão
docker exec wifisense-redis redis-cli ping

# Reiniciar
docker-compose restart redis
```

### Containers não iniciam
```bash
# Ver logs de erro
docker-compose logs

# Recriar containers
docker-compose up -d --force-recreate

# Limpar e reiniciar
docker-compose down -v
docker-compose up -d
```

## Checklist de Validação

Antes de prosseguir para Task 5, verifique:

- [ ] Docker Desktop instalado e rodando
- [ ] 3 containers de infraestrutura online (postgres, redis, rabbitmq)
- [ ] 7 schemas PostgreSQL criados
- [ ] Auth-service: 4/4 testes passando
- [ ] Tenant-service: 8/8 testes passando
- [ ] Teste de integração: 4/4 testes passando
- [ ] Isolamento multi-tenant validado

## Próximos Passos

Após validar tudo:

1. ✅ Marcar Task 4 como completa
2. 🚀 Iniciar Task 5: License-Service
3. 🚀 Iniciar Task 6: Device-Service
4. 🔍 Checkpoint Task 7

## Recursos

- **Documentação completa:** `README_SAAS.md`
- **Infraestrutura:** `docs/INFRASTRUCTURE_SETUP.md`
- **Auth-Service:** `services/auth-service/README.md`
- **Tenant-Service:** `services/tenant-service/README.md`
- **Makefile:** `make help`

---

**Dúvidas?** Execute `make help` para ver todos os comandos disponíveis.
