#!/bin/bash
# WiFiSense SaaS Multi-Tenant Platform
# Script de início rápido

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   WiFiSense SaaS Multi-Tenant Platform - QuickStart   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker encontrado${NC}"
echo -e "${GREEN}✓ Docker Compose encontrado${NC}"
echo ""

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Criando arquivo .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠️  Configure as variáveis em .env antes de continuar em produção${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Arquivo .env já existe${NC}"
    echo ""
fi

# Parar containers existentes
echo -e "${YELLOW}🛑 Parando containers existentes...${NC}"
docker-compose down 2>/dev/null || true
echo ""

# Iniciar infraestrutura
echo -e "${GREEN}🚀 Iniciando infraestrutura (PostgreSQL, Redis, RabbitMQ)...${NC}"
docker-compose up -d postgres redis rabbitmq

# Aguardar serviços ficarem saudáveis
echo -e "${YELLOW}⏳ Aguardando serviços ficarem prontos (30 segundos)...${NC}"
sleep 30

# Verificar se PostgreSQL está pronto
echo -e "${YELLOW}🔍 Verificando PostgreSQL...${NC}"
until docker exec wifisense-postgres pg_isready -U wifisense &>/dev/null; do
    echo -e "${YELLOW}   Aguardando PostgreSQL...${NC}"
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL pronto${NC}"

# Verificar se Redis está pronto
echo -e "${YELLOW}🔍 Verificando Redis...${NC}"
until docker exec wifisense-redis redis-cli -a wifisense_redis_password ping &>/dev/null; do
    echo -e "${YELLOW}   Aguardando Redis...${NC}"
    sleep 2
done
echo -e "${GREEN}✓ Redis pronto${NC}"

# Verificar se RabbitMQ está pronto
echo -e "${YELLOW}🔍 Verificando RabbitMQ...${NC}"
until docker exec wifisense-rabbitmq rabbitmq-diagnostics ping &>/dev/null; do
    echo -e "${YELLOW}   Aguardando RabbitMQ...${NC}"
    sleep 2
done
echo -e "${GREEN}✓ RabbitMQ pronto${NC}"
echo ""

# Verificar schemas PostgreSQL
echo -e "${YELLOW}🔍 Verificando schemas PostgreSQL...${NC}"
SCHEMAS=$(docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -t -c "\dn" | grep -E "auth_schema|tenant_schema|device_schema|license_schema|event_schema|notification_schema|billing_schema" | wc -l)

if [ "$SCHEMAS" -eq 7 ]; then
    echo -e "${GREEN}✓ Todos os 7 schemas criados com sucesso${NC}"
else
    echo -e "${RED}❌ Apenas $SCHEMAS schemas encontrados (esperado: 7)${NC}"
    echo -e "${YELLOW}   Executando script de inicialização...${NC}"
    docker exec -i wifisense-postgres psql -U wifisense -d wifisense_saas < scripts/init-schemas.sql
    echo -e "${GREEN}✓ Schemas criados${NC}"
fi
echo ""

# Iniciar microserviços
echo -e "${GREEN}🚀 Iniciando microserviços...${NC}"
docker-compose up -d

# Aguardar microserviços iniciarem
echo -e "${YELLOW}⏳ Aguardando microserviços iniciarem (15 segundos)...${NC}"
sleep 15
echo ""

# Verificar health de cada serviço
echo -e "${GREEN}🏥 Verificando health dos serviços...${NC}"
echo ""

services=(
    "8001:Auth Service"
    "8002:Tenant Service"
    "8003:Device Service"
    "8004:License Service"
    "8005:Event Service"
    "8006:Notification Service"
    "8007:Billing Service"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    echo -n "   $name (port $port): "
    
    if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Not responding${NC}"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✓ Todos os serviços estão OK!            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  Alguns serviços não estão respondendo ainda      ║${NC}"
    echo -e "${YELLOW}║     Aguarde mais alguns segundos e tente novamente    ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo -e "${GREEN}📊 Informações de Acesso:${NC}"
echo ""
echo -e "  ${YELLOW}Microserviços:${NC}"
echo -e "    • Auth Service:         http://localhost:8001"
echo -e "    • Tenant Service:       http://localhost:8002"
echo -e "    • Device Service:       http://localhost:8003"
echo -e "    • License Service:      http://localhost:8004"
echo -e "    • Event Service:        http://localhost:8005"
echo -e "    • Notification Service: http://localhost:8006"
echo -e "    • Billing Service:      http://localhost:8007"
echo ""
echo -e "  ${YELLOW}Infraestrutura:${NC}"
echo -e "    • PostgreSQL:  localhost:5432 (user: wifisense, db: wifisense_saas)"
echo -e "    • Redis:       localhost:6379 (password: wifisense_redis_password)"
echo -e "    • RabbitMQ UI: http://localhost:15672 (user: wifisense, pass: wifisense_password)"
echo ""
echo -e "${GREEN}📚 Comandos úteis:${NC}"
echo -e "    • Ver logs:           ${YELLOW}docker-compose logs -f${NC}"
echo -e "    • Parar serviços:     ${YELLOW}docker-compose down${NC}"
echo -e "    • Reiniciar:          ${YELLOW}docker-compose restart${NC}"
echo -e "    • Ver status:         ${YELLOW}docker-compose ps${NC}"
echo -e "    • Usar Makefile:      ${YELLOW}make help${NC}"
echo ""
echo -e "${GREEN}✨ Setup concluído com sucesso!${NC}"
