# Guia de Testes - Tenant Service

## Pré-requisitos

1. **Docker e Docker Compose** instalados
2. **PostgreSQL** rodando (via docker-compose)
3. **Auth Service** rodando (para obter token admin)

## Passo 1: Iniciar Infraestrutura

```bash
# Iniciar PostgreSQL, Redis e RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Aguardar serviços ficarem prontos (30 segundos)
sleep 30
```

## Passo 2: Iniciar Auth Service

```bash
# Iniciar auth-service para obter token admin
docker-compose up -d auth-service

# Aguardar serviço ficar pronto
sleep 10
```

## Passo 3: Criar Usuário Admin

O auth-service não tem endpoint público para criar admin, então precisamos criar diretamente no banco:

```bash
# Conectar ao PostgreSQL
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

# Criar usuário admin
INSERT INTO auth_schema.users (id, email, password_hash, name, plan_type, status, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'admin@wifisense.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNx8qKvKe', -- senha: admin123
  'Administrador',
  'premium',
  'active',
  NOW(),
  NOW()
);

# Sair do psql
\q
```

## Passo 4: Obter Token Admin

```bash
# Login como admin
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@wifisense.com",
    "password": "admin123"
  }'
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "uuid",
  "email": "admin@wifisense.com",
  "plan": "premium"
}
```

**IMPORTANTE:** O token retornado ainda não tem role "admin". Para testes, você pode:

### Opção A: Modificar o auth-service para adicionar role admin

Edite `services/auth-service/services/auth_service.py` e adicione lógica para detectar email admin:

```python
# No método login(), após validar senha:
role = "admin" if user.email == "admin@wifisense.com" else "tenant"

token = jwt_service.generate_jwt_token(
    tenant_id=str(user.id),
    email=user.email,
    role=role,  # Usar role detectada
    plan=user.plan_type.value
)
```

### Opção B: Gerar token manualmente para testes

```python
import jwt
from datetime import datetime, timedelta

payload = {
    "sub": "admin-id",
    "email": "admin@wifisense.com",
    "role": "admin",
    "plan": "premium",
    "exp": datetime.utcnow() + timedelta(days=365)
}

token = jwt.encode(payload, "dev-secret-key-change-in-production", algorithm="HS256")
print(token)
```

## Passo 5: Iniciar Tenant Service

```bash
# Iniciar tenant-service
docker-compose up tenant-service

# Ou em modo detached
docker-compose up -d tenant-service
```

## Passo 6: Testar Endpoints

### Usando curl

```bash
# Definir token
export ADMIN_TOKEN="seu-token-aqui"

# Health check
curl http://localhost:8002/health

# Criar tenant
curl -X POST http://localhost:8002/api/admin/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente@example.com",
    "name": "Cliente Teste",
    "plan_type": "basic"
  }'

# Listar tenants
curl http://localhost:8002/api/admin/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Usando script bash

```bash
# Editar test_endpoints.sh e adicionar seu token
nano services/tenant-service/test_endpoints.sh

# Executar
bash services/tenant-service/test_endpoints.sh
```

### Usando Python

```bash
# Editar example_usage.py e adicionar seu token
nano services/tenant-service/example_usage.py

# Executar
cd services/tenant-service
python example_usage.py
```

### Usando Swagger UI

1. Abrir navegador em: http://localhost:8002/docs
2. Clicar em "Authorize" no topo
3. Inserir: `Bearer seu-token-aqui`
4. Testar endpoints interativamente

## Passo 7: Testes Unitários

```bash
cd services/tenant-service
python test_tenant_service.py
```

## Verificar Logs

```bash
# Logs do tenant-service
docker-compose logs -f tenant-service

# Logs estruturados em JSON
docker-compose logs tenant-service | grep "Tenant criado"
```

## Verificar Database

```bash
# Conectar ao PostgreSQL
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

# Ver tenants criados
SELECT id, email, name, plan_type, status, trial_ends_at 
FROM tenant_schema.tenants 
ORDER BY created_at DESC 
LIMIT 10;

# Ver total por status
SELECT status, COUNT(*) 
FROM tenant_schema.tenants 
GROUP BY status;

# Sair
\q
```

## Troubleshooting

### Erro: "Token inválido"
- Verifique se o token está correto
- Verifique se JWT_SECRET_KEY é o mesmo em auth-service e tenant-service
- Token pode ter expirado (gere um novo)

### Erro: "Acesso restrito a administradores"
- Token não tem role "admin"
- Use Opção A ou B acima para obter token admin válido

### Erro: "Database connection failed"
- Verifique se PostgreSQL está rodando: `docker-compose ps postgres`
- Verifique logs: `docker-compose logs postgres`
- Verifique se schema foi criado: `\dn` no psql

### Erro: "Email já está em uso"
- Email deve ser único
- Use email diferente ou delete tenant existente

### Serviço não inicia
- Verifique logs: `docker-compose logs tenant-service`
- Verifique se porta 8002 está livre: `netstat -an | grep 8002`
- Verifique dependências: PostgreSQL e Redis devem estar rodando

## Testes de Trial Manager

### Verificar trials expirados

```bash
# Criar tenant com trial expirado manualmente
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

UPDATE tenant_schema.tenants 
SET trial_ends_at = NOW() - INTERVAL '1 day',
    status = 'trial'
WHERE email = 'cliente@example.com';

\q

# Aguardar 1 hora ou reiniciar serviço para forçar verificação
docker-compose restart tenant-service

# Verificar logs
docker-compose logs tenant-service | grep "Trial expirado"

# Verificar status no banco
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas -c \
  "SELECT email, status, trial_ends_at FROM tenant_schema.tenants WHERE email = 'cliente@example.com';"
```

### Verificar lembretes de trial

```bash
# Criar tenant com trial terminando em 3 dias
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

UPDATE tenant_schema.tenants 
SET trial_ends_at = NOW() + INTERVAL '3 days',
    status = 'trial'
WHERE email = 'cliente@example.com';

\q

# Verificar logs (lembretes são enviados a cada 6 horas)
docker-compose logs tenant-service | grep "Lembrete de trial"
```

## Limpeza

```bash
# Parar todos os serviços
docker-compose down

# Remover volumes (ATENÇÃO: deleta todos os dados)
docker-compose down -v
```

## Próximos Passos

Após validar o tenant-service:

1. Implementar testes unitários com pytest
2. Implementar testes de propriedade
3. Integrar com notification-service para emails
4. Implementar audit logs
5. Adicionar métricas Prometheus

## Recursos

- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc
- **Health Check:** http://localhost:8002/health
- **README:** services/tenant-service/README.md
