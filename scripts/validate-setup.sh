#!/bin/bash
# WiFiSense SaaS Multi-Tenant Platform
# Script de validação da configuração

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     WiFiSense SaaS - Validação de Configuração        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Função para verificar
check() {
    local name=$1
    local command=$2
    local error_msg=$3
    
    echo -n "  Verificando $name... "
    
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        if [ -n "$error_msg" ]; then
            echo -e "    ${RED}$error_msg${NC}"
        fi
        ((ERRORS++))
        return 1
    fi
}

# Função para avisos
warn() {
    local name=$1
    local command=$2
    local warn_msg=$3
    
    echo -n "  Verificando $name... "
    
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠${NC}"
        if [ -n "$warn_msg" ]; then
            echo -e "    ${YELLOW}$warn_msg${NC}"
        fi
        ((WARNINGS++))
        return 1
    fi
}

echo -e "${BLUE}1. Verificando Pré-requisitos${NC}"
check "Docker" "command -v docker" "Docker não está instalado"
check "Docker Compose" "command -v docker-compose" "Docker Compose não está instalado"
warn "jq (JSON parser)" "command -v jq" "Instale jq para melhor visualização: apt-get install jq"
echo ""

echo -e "${BLUE}2. Verificando Estrutura de Arquivos${NC}"
check "docker-compose.yml" "test -f docker-compose.yml" "Arquivo docker-compose.yml não encontrado"
check ".env" "test -f .env" "Arquivo .env não encontrado. Execute: cp .env.example .env"
check "scripts/init-schemas.sql" "test -f scripts/init-schemas.sql" "Script de inicialização não encontrado"
check "shared/config.py" "test -f shared/config.py" "Módulo shared não encontrado"
check "shared/database.py" "test -f shared/database.py" "Módulo shared/database.py não encontrado"
check "shared/logging.py" "test -f shared/logging.py" "Módulo shared/logging.py não encontrado"
echo ""

echo -e "${BLUE}3. Verificando Estrutura de Microserviços${NC}"
for service in auth tenant device license event notification billing; do
    check "$service-service/main.py" "test -f services/$service-service/main.py" "Serviço $service não encontrado"
    check "$service-service/Dockerfile" "test -f services/$service-service/Dockerfile" "Dockerfile do $service não encontrado"
    check "$service-service/requirements.txt" "test -f services/$service-service/requirements.txt" "Requirements do $service não encontrado"
done
echo ""

echo -e "${BLUE}4. Verificando Containers Docker${NC}"
check "PostgreSQL container" "docker ps | grep wifisense-postgres" "Container PostgreSQL não está rodando"
check "Redis container" "docker ps | grep wifisense-redis" "Container Redis não está rodando"
check "RabbitMQ container" "docker ps | grep wifisense-rabbitmq" "Container RabbitMQ não está rodando"
echo ""

echo -e "${BLUE}5. Verificando Conectividade de Infraestrutura${NC}"
check "PostgreSQL conectividade" "docker exec wifisense-postgres pg_isready -U wifisense" "PostgreSQL não está aceitando conexões"
check "Redis conectividade" "docker exec wifisense-redis redis-cli -a wifisense_redis_password ping" "Redis não está respondendo"
check "RabbitMQ conectividade" "docker exec wifisense-rabbitmq rabbitmq-diagnostics ping" "RabbitMQ não está respondendo"
echo ""

echo -e "${BLUE}6. Verificando Schemas PostgreSQL${NC}"
SCHEMA_COUNT=$(docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -t -c "\dn" 2>/dev/null | grep -E "auth_schema|tenant_schema|device_schema|license_schema|event_schema|notification_schema|billing_schema" | wc -l)

if [ "$SCHEMA_COUNT" -eq 7 ]; then
    echo -e "  Schemas PostgreSQL... ${GREEN}✓ (7/7)${NC}"
else
    echo -e "  Schemas PostgreSQL... ${RED}✗ ($SCHEMA_COUNT/7)${NC}"
    echo -e "    ${RED}Execute: docker exec -i wifisense-postgres psql -U wifisense -d wifisense_saas < scripts/init-schemas.sql${NC}"
    ((ERRORS++))
fi

# Listar schemas encontrados
echo -e "  ${BLUE}Schemas encontrados:${NC}"
docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -t -c "\dn" 2>/dev/null | grep -E "auth_schema|tenant_schema|device_schema|license_schema|event_schema|notification_schema|billing_schema" | while read -r line; do
    schema=$(echo "$line" | awk '{print $1}')
    echo -e "    • $schema"
done
echo ""

echo -e "${BLUE}7. Verificando Extensões PostgreSQL${NC}"
check "uuid-ossp extension" "docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -t -c 'SELECT 1 FROM pg_extension WHERE extname = '\''uuid-ossp'\''' | grep -q 1" "Extensão uuid-ossp não instalada"
check "pgcrypto extension" "docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -t -c 'SELECT 1 FROM pg_extension WHERE extname = '\''pgcrypto'\''' | grep -q 1" "Extensão pgcrypto não instalada"
echo ""

echo -e "${BLUE}8. Verificando Microserviços${NC}"
services=(
    "8001:auth-service"
    "8002:tenant-service"
    "8003:device-service"
    "8004:license-service"
    "8005:event-service"
    "8006:notification-service"
    "8007:billing-service"
)

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    
    # Verificar se container está rodando
    if docker ps | grep "wifisense-$name" &>/dev/null; then
        # Verificar health endpoint
        if curl -s -f http://localhost:$port/health &>/dev/null; then
            echo -e "  $name (port $port)... ${GREEN}✓${NC}"
        else
            echo -e "  $name (port $port)... ${YELLOW}⚠ Container rodando mas não responde${NC}"
            ((WARNINGS++))
        fi
    else
        echo -e "  $name (port $port)... ${RED}✗ Container não está rodando${NC}"
        ((ERRORS++))
    fi
done
echo ""

echo -e "${BLUE}9. Verificando Variáveis de Ambiente Críticas${NC}"
if [ -f .env ]; then
    warn "DATABASE_PASSWORD" "grep -q '^DATABASE_PASSWORD=.*[^example]' .env" "Use senha forte em produção"
    warn "REDIS_PASSWORD" "grep -q '^REDIS_PASSWORD=.*[^example]' .env" "Use senha forte em produção"
    warn "JWT_SECRET_KEY" "grep -q '^JWT_SECRET_KEY=.*[^change-me]' .env" "Use chave secreta forte em produção"
    warn "ENCRYPTION_KEY" "grep -q '^ENCRYPTION_KEY=' .env" "Configure ENCRYPTION_KEY para encriptação de dados sensíveis"
else
    echo -e "  ${RED}✗ Arquivo .env não encontrado${NC}"
    ((ERRORS++))
fi
echo ""

echo -e "${BLUE}10. Verificando Portas Disponíveis${NC}"
ports=(5432 6379 5672 15672 8001 8002 8003 8004 8005 8006 8007)
for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "  Porta $port... ${GREEN}✓ Em uso${NC}"
    else
        echo -e "  Porta $port... ${YELLOW}⚠ Não está em uso${NC}"
        ((WARNINGS++))
    fi
done
echo ""

# Resumo
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RESUMO DA VALIDAÇÃO                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Configuração perfeita! Todos os testes passaram.${NC}"
    echo ""
    echo -e "${GREEN}🚀 Sistema pronto para uso!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Configuração OK com $WARNINGS avisos.${NC}"
    echo ""
    echo -e "${YELLOW}Sistema funcional, mas revise os avisos acima.${NC}"
    exit 0
else
    echo -e "${RED}✗ Encontrados $ERRORS erros e $WARNINGS avisos.${NC}"
    echo ""
    echo -e "${RED}Corrija os erros antes de continuar.${NC}"
    echo ""
    echo -e "${YELLOW}Comandos úteis:${NC}"
    echo -e "  • Iniciar infraestrutura: ${BLUE}docker-compose up -d postgres redis rabbitmq${NC}"
    echo -e "  • Iniciar serviços:       ${BLUE}docker-compose up -d${NC}"
    echo -e "  • Ver logs:               ${BLUE}docker-compose logs -f${NC}"
    echo -e "  • Criar schemas:          ${BLUE}docker exec -i wifisense-postgres psql -U wifisense -d wifisense_saas < scripts/init-schemas.sql${NC}"
    exit 1
fi
