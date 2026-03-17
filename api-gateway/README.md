# WiFiSense SaaS - API Gateway

## Visão Geral

Gateway unificado que roteia requisições HTTP/HTTPS para os microserviços da plataforma WiFiSense SaaS. Implementa rate limiting, CORS, segurança e health checks.

## Funcionalidades

### ✅ Roteamento de Microserviços
- **Auth Service** (`/api/auth/*`) - Autenticação e autorização
- **Tenant Service** (`/api/admin/tenants`) - Gerenciamento de tenants
- **Device Service** (`/api/devices`) - Gerenciamento de dispositivos
- **License Service** (`/api/licenses`, `/api/admin/licenses`) - Gerenciamento de licenças
- **Event Service** (`/api/events`) - Processamento de eventos
- **Notification Service** (`/api/notifications`) - Notificações multi-canal
- **Billing Service** (`/api/billing`) - Faturamento e pagamentos
- **WebSocket** (`/ws`) - Conexões em tempo real

### ✅ Rate Limiting (Requisitos 34.1-34.4)
- **100 requisições/minuto** por tenant
- **1000 requisições/hora** por tenant
- Retorna **HTTP 429** quando limite excedido
- Headers `X-RateLimit-Limit` e `X-RateLimit-Remaining` em todas as respostas

### ✅ Segurança (Requisito 19.8)
- **SSL/TLS** com certificados (Let's Encrypt em produção)
- **HSTS** - Force HTTPS por 1 ano
- **X-Frame-Options** - Prevenir clickjacking
- **X-Content-Type-Options** - Prevenir MIME type sniffing
- **X-XSS-Protection** - Proteção contra XSS
- **Content-Security-Policy** - Política de segurança de conteúdo
- **Permissions-Policy** - Controle de permissões

### ✅ CORS (Requisito 19.8)
- Permite apenas domínios autorizados
- Suporta credenciais (cookies, headers de autenticação)
- Responde automaticamente a requisições OPTIONS (preflight)

### ✅ Health Checks (Requisitos 36.1-36.3)
- **GET /health** - Health check simples do gateway
- **GET /health/detailed** - Status agregado de todos os microserviços
- **GET /health/services/{service_id}** - Status de um serviço específico
- Status possíveis: `operational`, `degraded`, `outage`

### ✅ Load Balancing
- Algoritmo **least_conn** (menos conexões)
- Suporte a múltiplas instâncias de cada microserviço
- Health checks automáticos dos upstreams
- Failover automático em caso de falha

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                     │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Rate Limit  │  │ SSL/TLS      │  │ Security Headers │   │
│  │ 100 req/min │  │ TLS 1.2/1.3  │  │ HSTS, CSP, etc.  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ CORS        │  │ Load Balance │  │ Health Checks    │   │
│  │ Whitelist   │  │ Least Conn   │  │ /health/*        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │  Auth   │          │ Device  │          │  Event  │
   │ Service │          │ Service │          │ Service │
   └─────────┘          └─────────┘          └─────────┘
```

## Configuração

### Variáveis de Ambiente

Não há variáveis de ambiente específicas para o gateway. A configuração é feita através dos arquivos:

- `nginx.conf` - Configuração principal do Nginx
- `proxy_params.conf` - Parâmetros comuns de proxy
- `health_check.py` - Serviço de health check

### Certificados SSL

#### Desenvolvimento
O Dockerfile gera automaticamente um certificado auto-assinado para desenvolvimento local.

#### Produção
Usar certificados Let's Encrypt:

```bash
# Instalar certbot
apt-get install certbot python3-certbot-nginx

# Obter certificado
certbot --nginx -d api.wifisense.com

# Renovação automática
certbot renew --dry-run
```

Atualizar `nginx.conf`:
```nginx
ssl_certificate /etc/letsencrypt/live/api.wifisense.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.wifisense.com/privkey.pem;
```

## Uso

### Iniciar com Docker Compose

```bash
# Iniciar todos os serviços incluindo o gateway
docker-compose up -d

# Verificar logs do gateway
docker-compose logs -f api-gateway

# Verificar status
curl http://localhost/health
```

### Testar Endpoints

```bash
# Health check simples
curl http://localhost/health

# Health check detalhado
curl http://localhost/health/detailed

# Autenticação
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha123"}'

# Listar dispositivos (com autenticação)
curl http://localhost/api/devices \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Testar Rate Limiting

```bash
# Enviar 101 requisições em 1 minuto
for i in {1..101}; do
  curl -w "\n%{http_code}\n" http://localhost/api/devices \
    -H "Authorization: Bearer <JWT_TOKEN>" \
    -H "X-Tenant-ID: tenant-123"
done

# A 101ª requisição deve retornar HTTP 429
```

### Testar CORS

```bash
# Preflight request
curl -X OPTIONS http://localhost/api/devices \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Verificar headers CORS na resposta
```

## Monitoramento

### Logs

Os logs são escritos em formato JSON estruturado:

```json
{
  "time_local": "2024-01-15T10:30:45",
  "remote_addr": "192.168.1.100",
  "request_method": "GET",
  "request_uri": "/api/devices",
  "status": 200,
  "body_bytes_sent": 1234,
  "request_time": 0.123,
  "upstream_response_time": "0.098",
  "upstream_addr": "device-service:8000",
  "tenant_id": "tenant-123"
}
```

Visualizar logs:
```bash
# Logs de acesso
docker-compose exec api-gateway tail -f /var/log/nginx/access.log

# Logs de erro
docker-compose exec api-gateway tail -f /var/log/nginx/error.log
```

### Métricas

O gateway expõe métricas através dos logs e health checks:

- **Latência**: `request_time` e `upstream_response_time` nos logs
- **Taxa de erro**: Status codes 4xx e 5xx nos logs
- **Rate limiting**: Requisições com status 429
- **Disponibilidade**: Health checks em `/health/detailed`

## Troubleshooting

### Gateway não inicia

```bash
# Verificar configuração do Nginx
docker-compose exec api-gateway nginx -t

# Verificar logs de erro
docker-compose logs api-gateway
```

### Microserviço não responde

```bash
# Verificar health check detalhado
curl http://localhost/health/detailed | jq

# Verificar conectividade com o serviço
docker-compose exec api-gateway curl http://auth-service:8000/health
```

### Rate limiting não funciona

```bash
# Verificar se X-Tenant-ID está sendo enviado
curl -v http://localhost/api/devices \
  -H "X-Tenant-ID: tenant-123"

# Verificar logs do Nginx
docker-compose logs api-gateway | grep "limiting requests"
```

### CORS bloqueando requisições

```bash
# Verificar origem permitida em nginx.conf
# Adicionar domínio à regex de $cors_origin

# Exemplo para permitir app.example.com:
if ($http_origin ~* (https?://(localhost|app\.example\.com)(:[0-9]+)?$)) {
    set $cors_origin $http_origin;
}
```

## Performance

### Otimizações Implementadas

- **Worker processes**: Auto (baseado em CPUs)
- **Worker connections**: 4096 por worker
- **Keepalive**: Habilitado com timeout de 65s
- **Sendfile**: Habilitado para transferência eficiente
- **TCP optimizations**: `tcp_nopush` e `tcp_nodelay`
- **Gzip compression**: Habilitado para respostas
- **SSL session cache**: 10MB compartilhado
- **Upstream keepalive**: 32 conexões por upstream

### Benchmarks Esperados

Com a configuração atual, o gateway deve suportar:

- **10,000+ requisições/segundo** em hardware moderno
- **Latência < 5ms** para roteamento (sem contar upstream)
- **100,000+ conexões simultâneas** com tuning do kernel

## Segurança

### Checklist de Segurança

- ✅ SSL/TLS com protocolos seguros (TLS 1.2+)
- ✅ Ciphers seguros configurados
- ✅ HSTS habilitado
- ✅ Headers de segurança configurados
- ✅ CORS com whitelist de domínios
- ✅ Rate limiting por tenant
- ✅ Timeouts configurados (30s)
- ✅ Versão do Nginx oculta
- ✅ Logs estruturados para auditoria

### Recomendações Adicionais

1. **Firewall**: Permitir apenas portas 80 e 443
2. **DDoS Protection**: Usar CloudFlare ou similar
3. **WAF**: Considerar ModSecurity para proteção adicional
4. **Certificados**: Renovar automaticamente com certbot
5. **Monitoramento**: Integrar com Prometheus/Grafana

## Requisitos Atendidos

- ✅ **1.1** - Multi-tenancy com isolamento de dados
- ✅ **19.8** - HTTPS, CORS e headers de segurança
- ✅ **22.1** - Escalabilidade horizontal
- ✅ **34.1-34.4** - Rate limiting (100 req/min, 1000 req/hora)
- ✅ **36.1-36.3** - Health checks com status agregado

## Próximos Passos

1. **Task 17**: Implementar WebSocket para real-time updates
2. **Monitoramento**: Integrar com Prometheus para métricas
3. **Logging**: Integrar com ELK Stack para análise de logs
4. **CDN**: Configurar CloudFlare para cache de assets estáticos
5. **Auto-scaling**: Configurar múltiplas instâncias do gateway
