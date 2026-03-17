# -*- coding: utf-8 -*-
"""
Billing Service - Serviço de Faturamento
Responsável por gerenciar cobranças, faturas e integração com Stripe

Funcionalidades:
- Cálculo de cobrança mensal com descontos por volume
- Geração automática de faturas (cron job)
- Integração com Stripe para pagamentos
- Tratamento de falhas de pagamento com retry
- Endpoints de billing para clientes

Requisitos: 5.7, 11.6, 17.1-17.5
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from routes.billing import router as billing_router
from shared.database import get_billing_db
from shared.logging import get_logger
from shared.config import settings

logger = get_logger(__name__)

# Gerenciador de banco de dados
db_manager = get_billing_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    Inicializa e fecha recursos (banco de dados, etc)
    """
    # Startup
    logger.info("Iniciando Billing Service")
    
    try:
        # Inicializa conexão com banco de dados
        await db_manager.initialize()
        logger.info("Conexão com banco de dados inicializada")
        
        # Cria schema e tabelas se não existirem
        await db_manager.create_schema()
        await db_manager.create_tables()
        logger.info("Schema e tabelas verificados/criados")
        
        # Verifica health do banco
        db_healthy = await db_manager.health_check()
        if not db_healthy:
            logger.error("Banco de dados não está saudável!")
        else:
            logger.info("Banco de dados está saudável")
        
        logger.info("Billing Service iniciado com sucesso")
    
    except Exception as e:
        logger.error(f"Erro ao inicializar Billing Service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Encerrando Billing Service")
    await db_manager.close()
    logger.info("Billing Service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Billing Service",
    description="Serviço de faturamento e pagamentos com integração Stripe",
    version="1.0.0",
    lifespan=lifespan
)

# Registra routers
app.include_router(billing_router)

logger.info("Routers registrados")


@app.get("/health")
async def health_check():
    """
    Endpoint de health check
    
    Verifica se o serviço está operacional e se o banco está acessível.
    
    Returns:
        dict: Status do serviço e componentes
    """
    # Verifica saúde do banco de dados
    db_healthy = await db_manager.health_check()
    
    overall_status = "healthy" if db_healthy else "unhealthy"
    
    return {
        "status": overall_status,
        "service": "billing-service",
        "version": "1.0.0",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "stripe": "configured" if settings.STRIPE_API_KEY else "not_configured"
        }
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "billing-service",
        "version": "1.0.0",
        "description": "Serviço de faturamento e pagamentos",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "billing": "/api/billing/*"
        }
    }
