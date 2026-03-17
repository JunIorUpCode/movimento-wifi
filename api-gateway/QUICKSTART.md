# API Gateway - Guia Rápido

## 🚀 Início Rápido

### 1. Iniciar o Gateway

```bash
# Iniciar todos os serviços (incluindo gateway)
docker-compose up -d

# Verificar se o gateway está rodando
docker-compose ps api-gateway

# Verificar logs
docker-compose logs -f api-gateway
```

### 2. Verificar Status

```bash
# Health check simples
curl http://localhost/health

# Health check detalhado (todos os serviços)
curl http://localhost/health/detailed | jq

# Health check de um serviço específico
curl http://localhost/health/services/auth | jq
```

### 3. Testar Roteamento

```bash
# Auth Service
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"senha123"}'

# Device Service (requer autenticação)
curl http://localhost/api/devices \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Event Service
curl http://localhost/api/events \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 4. Testar Rate Limiting

```bash
# Enviar múltiplas requisições rapidamente
for i in {1..105}; do
  echo "Request $i:"
  curl -w "\nStatus: %{http_code}\n" http://localhost/health \
    -H "X-Tenant-ID: test-tenant-123"
  sleep 0.1
done

# Após 100 requisições, deve retornar HTTP 429
```

### 5. Verificar Headers de Segurança

```bash
# Ver todos os headers
curl -I http://localhost/health

# Verificar headers específicos
curl -I http://localhost/health | grep -E "X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security"
```

### 6. Testar CORS

```bash
# Preflight request
curl -X OPTIONS http://localhost/api/devices \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Verificar headers CORS
curl http://localhost/health \
  -H "Origin: http://localhost:3000" \
  -v | grep -i "access-control"
```

## 📊 Monitoramento

### Ver Logs em Tempo Real

```bash
# Logs de acesso (JSON)
docker-compose exec api-gateway tail -f /var/log/nginx/access.log

# Logs de erro
docker-compose exec api-gateway tail -f /var/log/nginx/error.log

# Filtrar por tenant
docker-compose exec api-gateway tail -f /var/log/nginx/access.log | grep "tenant-123"
```

### Verificar Configuração

```bash
# Testar configuração do Nginx
docker-compose exec api-gateway nginx -t

# Recarregar configuração (sem downtime)
docker-compose exec api-gateway nginx -s reload
```

## 🔧 Troubleshooting

### Gateway não inicia

```bash
# Ver logs de erro
docker-compose logs api-gateway

# Verificar se as portas estão disponíveis
netstat -tuln | grep -E "80|443"

# Verificar configuração
docker-compose exec api-gateway nginx -t
```

### Microserviço não responde

```bash
# Verificar status de todos os serviços
curl http://localhost/health/detailed | jq '.services[] | {service: .service_id, status: .status}'

# Testar conectividade direta
docker-compose exec api-gateway curl http://auth-service:8000/health
```

### Rate limiting não funciona

```bash
# Verificar se X-Tenant-ID está sendo enviado
curl -v http://localhost/health -H "X-Tenant-ID: test-123" 2>&1 | grep "X-Tenant-ID"

# Ver logs de rate limiting
docker-compose logs api-gateway | grep "limiting"
```

## 📝 Exemplos de Uso

### Autenticação Completa

```bash
# 1. Registrar usuário
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "senha123",
    "name": "Usuário Teste"
  }'

# 2. Fazer login
TOKEN=$(curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "senha123"
  }' | jq -r '.access_token')

# 3. Usar token para acessar recursos
curl http://localhost/api/devices \
  -H "Authorization: Bearer $TOKEN"
```

### Gerenciar Dispositivos

```bash
# Listar dispositivos
curl http://localhost/api/devices \
  -H "Authorization: Bearer $TOKEN"

# Registrar novo dispositivo
curl -X POST http://localhost/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "activation_key": "XXXX-XXXX-XXXX-XXXX",
    "hardware_info": {
      "type": "raspberry_pi",
      "os": "Raspbian",
      "csi_capable": true
    }
  }'

# Ver status de um dispositivo
curl http://localhost/api/devices/{device_id}/status \
  -H "Authorization: Bearer $TOKEN"
```

### Consultar Eventos

```bash
# Listar eventos
curl http://localhost/api/events \
  -H "Authorization: Bearer $TOKEN"

# Filtrar por tipo
curl "http://localhost/api/events?event_type=fall_suspected" \
  -H "Authorization: Bearer $TOKEN"

# Timeline de eventos
curl http://localhost/api/events/timeline \
  -H "Authorization: Bearer $TOKEN"
```

## 🎯 Próximos Passos

1. Configurar certificados SSL para produção
2. Ajustar whitelist de CORS para domínios de produção
3. Configurar monitoramento com Prometheus
4. Integrar logs com ELK Stack
5. Configurar múltiplas instâncias para alta disponibilidade

## 📚 Documentação Adicional

- [README.md](README.md) - Documentação completa
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Resumo da implementação
- [nginx.conf](nginx.conf) - Configuração do Nginx (comentada)
