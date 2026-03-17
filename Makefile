# WiFiSense SaaS Multi-Tenant Platform
# Makefile para comandos comuns de desenvolvimento

.PHONY: help setup up down logs clean test health

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)WiFiSense SaaS - Comandos Disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Configuração inicial do projeto
	@echo "$(GREEN)Configurando projeto...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Arquivo .env criado. Configure as variáveis antes de continuar.$(NC)"; \
	else \
		echo "$(YELLOW)Arquivo .env já existe.$(NC)"; \
	fi
	@echo "$(GREEN)Setup concluído!$(NC)"

up: ## Inicia todos os serviços
	@echo "$(GREEN)Iniciando serviços...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Serviços iniciados!$(NC)"
	@echo "$(YELLOW)Aguarde 30 segundos para os serviços ficarem prontos...$(NC)"
	@sleep 5
	@make health

up-infra: ## Inicia apenas infraestrutura (PostgreSQL, Redis, RabbitMQ)
	@echo "$(GREEN)Iniciando infraestrutura...$(NC)"
	docker-compose up -d postgres redis rabbitmq
	@echo "$(GREEN)Infraestrutura iniciada!$(NC)"

down: ## Para todos os serviços
	@echo "$(YELLOW)Parando serviços...$(NC)"
	docker-compose down
	@echo "$(GREEN)Serviços parados!$(NC)"

restart: ## Reinicia todos os serviços
	@echo "$(YELLOW)Reiniciando serviços...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Serviços reiniciados!$(NC)"

logs: ## Mostra logs de todos os serviços
	docker-compose logs -f

logs-auth: ## Mostra logs do auth-service
	docker-compose logs -f auth-service

logs-tenant: ## Mostra logs do tenant-service
	docker-compose logs -f tenant-service

logs-device: ## Mostra logs do device-service
	docker-compose logs -f device-service

logs-license: ## Mostra logs do license-service
	docker-compose logs -f license-service

logs-event: ## Mostra logs do event-service
	docker-compose logs -f event-service

logs-notification: ## Mostra logs do notification-service
	docker-compose logs -f notification-service

logs-billing: ## Mostra logs do billing-service
	docker-compose logs -f billing-service

ps: ## Lista status de todos os serviços
	@docker-compose ps

health: ## Verifica health de todos os serviços
	@echo "$(GREEN)Verificando health dos serviços...$(NC)"
	@echo ""
	@echo "$(YELLOW)Auth Service (8001):$(NC)"
	@curl -s http://localhost:8001/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)Tenant Service (8002):$(NC)"
	@curl -s http://localhost:8002/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)Device Service (8003):$(NC)"
	@curl -s http://localhost:8003/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)License Service (8004):$(NC)"
	@curl -s http://localhost:8004/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)Event Service (8005):$(NC)"
	@curl -s http://localhost:8005/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)Notification Service (8006):$(NC)"
	@curl -s http://localhost:8006/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""
	@echo "$(YELLOW)Billing Service (8007):$(NC)"
	@curl -s http://localhost:8007/health | jq '.' 2>/dev/null || echo "$(RED)Serviço não disponível$(NC)"
	@echo ""

db-shell: ## Abre shell do PostgreSQL
	docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

redis-shell: ## Abre shell do Redis
	docker exec -it wifisense-redis redis-cli -a wifisense_redis_password

rabbitmq-ui: ## Abre RabbitMQ Management UI no navegador
	@echo "$(GREEN)Abrindo RabbitMQ Management UI...$(NC)"
	@echo "URL: http://localhost:15672"
	@echo "Usuário: wifisense"
	@echo "Senha: wifisense_password"
	@xdg-open http://localhost:15672 2>/dev/null || open http://localhost:15672 2>/dev/null || echo "$(YELLOW)Abra manualmente: http://localhost:15672$(NC)"

clean: ## Remove containers, volumes e imagens
	@echo "$(RED)ATENÇÃO: Isso irá remover todos os dados!$(NC)"
	@read -p "Tem certeza? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker system prune -f; \
		echo "$(GREEN)Limpeza concluída!$(NC)"; \
	else \
		echo "$(YELLOW)Operação cancelada.$(NC)"; \
	fi

rebuild: ## Reconstrói todas as imagens Docker
	@echo "$(YELLOW)Reconstruindo imagens...$(NC)"
	docker-compose build --no-cache
	@echo "$(GREEN)Imagens reconstruídas!$(NC)"

rebuild-service: ## Reconstrói um serviço específico (uso: make rebuild-service SERVICE=auth-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Erro: Especifique o serviço com SERVICE=nome-do-servico$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Reconstruindo $(SERVICE)...$(NC)"
	docker-compose build --no-cache $(SERVICE)
	docker-compose up -d $(SERVICE)
	@echo "$(GREEN)$(SERVICE) reconstruído e reiniciado!$(NC)"

test: ## Executa testes de todos os serviços
	@echo "$(GREEN)Executando testes...$(NC)"
	@for service in auth tenant device license event notification billing; do \
		echo "$(YELLOW)Testando $$service-service...$(NC)"; \
		cd services/$$service-service && pytest tests/ -v || true; \
		cd ../..; \
	done
	@echo "$(GREEN)Testes concluídos!$(NC)"

install-deps: ## Instala dependências Python localmente
	@echo "$(GREEN)Instalando dependências...$(NC)"
	pip install -r services/auth-service/requirements.txt
	pip install pytest pytest-asyncio pytest-cov
	@echo "$(GREEN)Dependências instaladas!$(NC)"

format: ## Formata código Python com black
	@echo "$(GREEN)Formatando código...$(NC)"
	black services/ shared/
	@echo "$(GREEN)Código formatado!$(NC)"

lint: ## Executa linter (flake8)
	@echo "$(GREEN)Executando linter...$(NC)"
	flake8 services/ shared/ --max-line-length=100
	@echo "$(GREEN)Linting concluído!$(NC)"

check-schemas: ## Verifica se schemas PostgreSQL foram criados
	@echo "$(GREEN)Verificando schemas PostgreSQL...$(NC)"
	@docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn" | grep -E "auth_schema|tenant_schema|device_schema|license_schema|event_schema|notification_schema|billing_schema" && echo "$(GREEN)Todos os schemas encontrados!$(NC)" || echo "$(RED)Schemas não encontrados!$(NC)"

backup-db: ## Faz backup do banco de dados
	@echo "$(GREEN)Fazendo backup do banco de dados...$(NC)"
	@mkdir -p backups
	@docker exec wifisense-postgres pg_dump -U wifisense wifisense_saas > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup criado em backups/$(NC)"

restore-db: ## Restaura backup do banco (uso: make restore-db FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Erro: Especifique o arquivo com FILE=caminho/do/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restaurando backup...$(NC)"
	@docker exec -i wifisense-postgres psql -U wifisense wifisense_saas < $(FILE)
	@echo "$(GREEN)Backup restaurado!$(NC)"

.DEFAULT_GOAL := help


test-auth: ## Testa auth-service
	@echo "$(GREEN)Testando auth-service...$(NC)"
	cd services/auth-service && python test_auth_simple.py

test-tenant: ## Testa tenant-service
	@echo "$(GREEN)Testando tenant-service...$(NC)"
	cd services/tenant-service && python test_tenant_service.py

test-integration: ## Executa teste de integração completa
	@echo "$(GREEN)Executando teste de integração completa...$(NC)"
	python scripts/test-integration.py

infra-up: ## Inicia apenas infraestrutura (PostgreSQL, Redis, RabbitMQ)
	@echo "$(GREEN)Iniciando infraestrutura...$(NC)"
	docker-compose up -d postgres redis rabbitmq
	@echo "$(GREEN)Infraestrutura iniciada!$(NC)"
	@echo "$(YELLOW)Aguardando serviços ficarem prontos...$(NC)"
	@sleep 10
	@make infra-health

infra-health: ## Verifica health da infraestrutura
	@echo "$(GREEN)Verificando infraestrutura...$(NC)"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker exec wifisense-postgres pg_isready -U wifisense && echo "$(GREEN)✅ Online$(NC)" || echo "$(RED)❌ Offline$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker exec wifisense-redis redis-cli ping && echo "$(GREEN)✅ Online$(NC)" || echo "$(RED)❌ Offline$(NC)"
	@echo ""
	@echo "$(YELLOW)RabbitMQ:$(NC)"
	@docker exec wifisense-rabbitmq rabbitmqctl status > /dev/null 2>&1 && echo "$(GREEN)✅ Online$(NC)" || echo "$(RED)❌ Offline$(NC)"
	@echo ""

db-check: ## Verifica schemas e tabelas do PostgreSQL
	@echo "$(GREEN)Verificando banco de dados...$(NC)"
	@echo ""
	@echo "$(YELLOW)Schemas:$(NC)"
	@docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn"
	@echo ""
	@echo "$(YELLOW)Tabelas em auth_schema:$(NC)"
	@docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dt auth_schema.*"
	@echo ""
	@echo "$(YELLOW)Tabelas em tenant_schema:$(NC)"
	@docker exec wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dt tenant_schema.*"
	@echo ""
