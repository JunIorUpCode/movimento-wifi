#!/usr/bin/env python3
"""
============================================================================
WiFiSense SaaS - Health Check Service
============================================================================
Serviço que verifica conectividade com todos os microserviços
e retorna status agregado do sistema.

Requisitos: 36.1-36.3
============================================================================
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List

import aiohttp
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ============================================================================
# Configuração de Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Enums e Constantes
# ============================================================================

class ServiceStatus(str, Enum):
    """Status possíveis de um serviço"""
    OPERATIONAL = "operational"  # Serviço funcionando normalmente
    DEGRADED = "degraded"        # Serviço com problemas mas funcional
    OUTAGE = "outage"            # Serviço indisponível

class SystemStatus(str, Enum):
    """Status agregado do sistema"""
    OPERATIONAL = "operational"  # Todos os serviços operacionais
    DEGRADED = "degraded"        # Alguns serviços com problemas
    OUTAGE = "outage"            # Sistema indisponível

# Configuração dos microserviços
SERVICES = {
    "auth": {
        "name": "Auth Service",
        "url": "http://auth-service:8000/health",
        "critical": True  # Serviço crítico
    },
    "tenant": {
        "name": "Tenant Service",
        "url": "http://tenant-service:8000/health",
        "critical": True
    },
    "device": {
        "name": "Device Service",
        "url": "http://device-service:8000/health",
        "critical": True
    },
    "license": {
        "name": "License Service",
        "url": "http://license-service:8000/health",
        "critical": True
    },
    "event": {
        "name": "Event Service",
        "url": "http://event-service:8000/health",
        "critical": True
    },
    "notification": {
        "name": "Notification Service",
        "url": "http://notification-service:8000/health",
        "critical": False  # Não crítico
    },
    "billing": {
        "name": "Billing Service",
        "url": "http://billing-service:8000/health",
        "critical": False  # Não crítico
    }
}

# Timeout para health checks (segundos)
HEALTH_CHECK_TIMEOUT = 5

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="WiFiSense API Gateway Health Check",
    description="Serviço de health check para verificar status de todos os microserviços",
    version="1.0.0"
)

# ============================================================================
# Health Check Functions
# ============================================================================

async def check_service_health(
    session: aiohttp.ClientSession,
    service_id: str,
    service_config: Dict
) -> Dict:
    """
    Verifica o health de um serviço específico.
    
    Args:
        session: Sessão aiohttp para fazer requisições
        service_id: ID do serviço
        service_config: Configuração do serviço
        
    Returns:
        Dict com status do serviço
    """
    start_time = time.time()
    
    try:
        async with session.get(
            service_config["url"],
            timeout=aiohttp.ClientTimeout(total=HEALTH_CHECK_TIMEOUT)
        ) as response:
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status == 200:
                status = ServiceStatus.OPERATIONAL
            elif response.status in [503, 504]:
                status = ServiceStatus.OUTAGE
            else:
                status = ServiceStatus.DEGRADED
                
            return {
                "service_id": service_id,
                "name": service_config["name"],
                "status": status,
                "response_time_ms": round(response_time, 2),
                "critical": service_config["critical"],
                "error": None
            }
            
    except asyncio.TimeoutError:
        logger.warning(f"Timeout ao verificar {service_id}")
        return {
            "service_id": service_id,
            "name": service_config["name"],
            "status": ServiceStatus.OUTAGE,
            "response_time_ms": HEALTH_CHECK_TIMEOUT * 1000,
            "critical": service_config["critical"],
            "error": "Timeout"
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar {service_id}: {str(e)}")
        return {
            "service_id": service_id,
            "name": service_config["name"],
            "status": ServiceStatus.OUTAGE,
            "response_time_ms": None,
            "critical": service_config["critical"],
            "error": str(e)
        }

async def check_all_services() -> Dict:
    """
    Verifica o health de todos os serviços em paralelo.
    
    Returns:
        Dict com status agregado do sistema
    """
    async with aiohttp.ClientSession() as session:
        # Executar health checks em paralelo
        tasks = [
            check_service_health(session, service_id, config)
            for service_id, config in SERVICES.items()
        ]
        
        service_results = await asyncio.gather(*tasks)
    
    # Calcular status agregado do sistema
    system_status = calculate_system_status(service_results)
    
    return {
        "status": system_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": service_results
    }

def calculate_system_status(service_results: List[Dict]) -> SystemStatus:
    """
    Calcula o status agregado do sistema baseado nos status dos serviços.
    
    Regras:
    - OUTAGE: Se algum serviço crítico está em OUTAGE
    - DEGRADED: Se algum serviço está em DEGRADED ou OUTAGE (não crítico)
    - OPERATIONAL: Todos os serviços operacionais
    
    Args:
        service_results: Lista com resultados dos health checks
        
    Returns:
        Status agregado do sistema
    """
    critical_outages = 0
    degraded_services = 0
    
    for result in service_results:
        if result["status"] == ServiceStatus.OUTAGE:
            if result["critical"]:
                critical_outages += 1
            else:
                degraded_services += 1
        elif result["status"] == ServiceStatus.DEGRADED:
            degraded_services += 1
    
    # Se há serviços críticos em outage, sistema está em outage
    if critical_outages > 0:
        return SystemStatus.OUTAGE
    
    # Se há serviços degradados ou não-críticos em outage, sistema está degraded
    if degraded_services > 0:
        return SystemStatus.DEGRADED
    
    # Todos os serviços operacionais
    return SystemStatus.OPERATIONAL

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check_simple():
    """
    Health check simples que retorna apenas o status do gateway.
    
    Requisito: 36.1
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/health/detailed")
async def health_check_detailed():
    """
    Health check detalhado que verifica conectividade com todos os microserviços.
    
    Requisitos: 36.2, 36.3
    
    Returns:
        Status agregado do sistema e status individual de cada serviço
    """
    result = await check_all_services()
    
    # Determinar HTTP status code baseado no status do sistema
    if result["status"] == SystemStatus.OPERATIONAL:
        status_code = 200
    elif result["status"] == SystemStatus.DEGRADED:
        status_code = 200  # Ainda funcional, mas com problemas
    else:  # OUTAGE
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=result
    )

@app.get("/health/services/{service_id}")
async def health_check_service(service_id: str):
    """
    Health check de um serviço específico.
    
    Args:
        service_id: ID do serviço (auth, tenant, device, etc.)
        
    Returns:
        Status do serviço específico
    """
    if service_id not in SERVICES:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Service not found",
                "message": f"Serviço '{service_id}' não encontrado"
            }
        )
    
    async with aiohttp.ClientSession() as session:
        result = await check_service_health(
            session,
            service_id,
            SERVICES[service_id]
        )
    
    # Determinar HTTP status code
    if result["status"] == ServiceStatus.OPERATIONAL:
        status_code = 200
    elif result["status"] == ServiceStatus.DEGRADED:
        status_code = 200
    else:  # OUTAGE
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=result
    )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
