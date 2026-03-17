#!/bin/bash
# ============================================================================
# WiFiSense SaaS - Validação de Configuração do API Gateway
# ============================================================================
# Script para validar a configuração do Nginx antes de fazer deploy
# ============================================================================

set -e

echo "============================================================================"
echo "Validando configuração do API Gateway"
echo "============================================================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Função para imprimir aviso
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Verificar se os arquivos necessários existem
echo "1. Verificando arquivos necessários..."
files=(
    "nginx.conf"
    "proxy_params.conf"
    "Dockerfile"
    "Dockerfile.healthcheck"
    "health_check.py"
    "requirements.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file existe"
    else
        print_error "$file não encontrado"
        exit 1
    fi
done
echo ""

# 2. Verificar sintaxe do nginx.conf
echo "2. Verificando sintaxe do nginx.conf..."
if docker run --rm -v "$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro" \
    -v "$(pwd)/proxy_params.conf:/etc/nginx/proxy_params.conf:ro" \
    nginx:1.25-alpine nginx -t 2>&1 | grep -q "successful"; then
    print_success "Sintaxe do nginx.conf está correta"
else
    print_error "Erro na sintaxe do nginx.conf"
    docker run --rm -v "$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro" \
        -v "$(pwd)/proxy_params.conf:/etc/nginx/proxy_params.conf:ro" \
        nginx:1.25-alpine nginx -t
    exit 1
fi
echo ""

# 3. Verificar sintaxe do Python
echo "3. Verificando sintaxe do health_check.py..."
if python3 -m py_compile health_check.py 2>/dev/null; then
    print_success "Sintaxe do health_check.py está correta"
else
    print_error "Erro na sintaxe do health_check.py"
    python3 -m py_compile health_check.py
    exit 1
fi
echo ""

# 4. Verificar configurações críticas
echo "4. Verificando configurações críticas..."

# Rate limiting
if grep -q "limit_req_zone.*rate=100r/m" nginx.conf; then
    print_success "Rate limiting de 100 req/min configurado"
else
    print_warning "Rate limiting de 100 req/min não encontrado"
fi

if grep -q "limit_req_zone.*rate=1000r/h" nginx.conf; then
    print_success "Rate limiting de 1000 req/hora configurado"
else
    print_warning "Rate limiting de 1000 req/hora não encontrado"
fi

# SSL/TLS
if grep -q "ssl_protocols TLSv1.2 TLSv1.3" nginx.conf; then
    print_success "Protocolos SSL seguros configurados (TLS 1.2/1.3)"
else
    print_warning "Protocolos SSL não configurados corretamente"
fi

# Headers de segurança
security_headers=(
    "Strict-Transport-Security"
    "X-Frame-Options"
    "X-Content-Type-Options"
    "X-XSS-Protection"
    "Referrer-Policy"
    "Content-Security-Policy"
)

for header in "${security_headers[@]}"; do
    if grep -q "$header" nginx.conf; then
        print_success "Header de segurança '$header' configurado"
    else
        print_warning "Header de segurança '$header' não encontrado"
    fi
done

# CORS
if grep -q "Access-Control-Allow-Origin" nginx.conf; then
    print_success "CORS configurado"
else
    print_warning "CORS não configurado"
fi

# Timeouts
if grep -q "proxy_connect_timeout 30s" proxy_params.conf && \
   grep -q "proxy_send_timeout 30s" proxy_params.conf && \
   grep -q "proxy_read_timeout 30s" proxy_params.conf; then
    print_success "Timeouts de 30 segundos configurados"
else
    print_warning "Timeouts não configurados corretamente"
fi

echo ""

# 5. Verificar upstreams
echo "5. Verificando upstreams dos microserviços..."
upstreams=(
    "auth_service"
    "tenant_service"
    "device_service"
    "license_service"
    "event_service"
    "notification_service"
    "billing_service"
)

for upstream in "${upstreams[@]}"; do
    if grep -q "upstream $upstream" nginx.conf; then
        print_success "Upstream '$upstream' configurado"
    else
        print_error "Upstream '$upstream' não encontrado"
        exit 1
    fi
done
echo ""

# 6. Verificar rotas
echo "6. Verificando rotas dos microserviços..."
routes=(
    "/api/auth/"
    "/api/admin/tenants"
    "/api/devices"
    "/api/licenses"
    "/api/events"
    "/api/notifications"
    "/api/billing"
    "/ws"
)

for route in "${routes[@]}"; do
    if grep -q "location $route" nginx.conf; then
        print_success "Rota '$route' configurada"
    else
        print_warning "Rota '$route' não encontrada"
    fi
done
echo ""

# 7. Verificar health checks
echo "7. Verificando configuração de health checks..."
if grep -q "location /health" nginx.conf; then
    print_success "Endpoint /health configurado"
else
    print_error "Endpoint /health não encontrado"
    exit 1
fi

if grep -q "location /health/detailed" nginx.conf; then
    print_success "Endpoint /health/detailed configurado"
else
    print_warning "Endpoint /health/detailed não encontrado"
fi
echo ""

# 8. Verificar Dockerfiles
echo "8. Verificando Dockerfiles..."
if grep -q "FROM nginx:1.25-alpine" Dockerfile; then
    print_success "Dockerfile usa imagem nginx:1.25-alpine"
else
    print_warning "Dockerfile não usa imagem recomendada"
fi

if grep -q "FROM python:3.11-slim" Dockerfile.healthcheck; then
    print_success "Dockerfile.healthcheck usa imagem python:3.11-slim"
else
    print_warning "Dockerfile.healthcheck não usa imagem recomendada"
fi
echo ""

# Resumo
echo "============================================================================"
echo "Validação concluída!"
echo "============================================================================"
echo ""
print_success "Configuração do API Gateway está válida e pronta para uso"
echo ""
echo "Próximos passos:"
echo "  1. docker-compose build api-gateway"
echo "  2. docker-compose up -d api-gateway"
echo "  3. curl http://localhost/health"
echo ""
