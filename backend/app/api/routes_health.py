"""
Rotas REST — Health checks e métricas Prometheus.

Implementa Tarefa 26 | Requisitos: Fase 4
Endpoints:
  GET /api/health/ready  — readiness check (DB + monitor)
  GET /metrics           — métricas no formato Prometheus text (registrado na raiz)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.monitor_service import monitor_service

router = APIRouter(tags=["health"])

# Rota registrada em /api/health/ready (prefixo /api vem do main.py)
health_router = APIRouter(prefix="/health", tags=["health"])

# Rota registrada na raiz /metrics (sem prefixo /api)
metrics_router = APIRouter(tags=["metrics"])


@health_router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Verifica se o sistema está pronto para receber requisições.

    Testa:
    - Conectividade com banco de dados
    - Status do MonitorService

    Retorna HTTP 200 se tudo estiver pronto, HTTP 503 caso contrário.
    """
    checks: dict[str, str] = {}
    all_ok = True

    # Verifica banco de dados
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        all_ok = False

    # Verifica MonitorService
    try:
        checks["monitor"] = "running" if monitor_service.is_running else "stopped"
        # Parado não é falha — o usuário pode iniciar manualmente
    except Exception as exc:
        checks["monitor"] = f"error: {exc}"
        all_ok = False

    from fastapi import HTTPException

    if not all_ok:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}


@metrics_router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Expõe métricas no formato Prometheus text exposition format.

    Métricas disponíveis:
    - ``wifisense_uptime_seconds`` — tempo de atividade do backend
    - ``wifisense_monitor_running`` — 1 se monitoramento ativo, 0 caso contrário
    - ``wifisense_current_confidence`` — confiança da última detecção
    - ``wifisense_simulation_mode`` — 1 se em modo simulação, 0 caso contrário
    """
    lines: list[str] = []

    def gauge(name: str, value: float, help_text: str, labels: str = "") -> None:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        label_str = f"{{{labels}}}" if labels else ""
        lines.append(f"{name}{label_str} {value}")

    # Uptime
    gauge(
        "wifisense_uptime_seconds",
        round(monitor_service.uptime, 1),
        "Tempo de atividade do backend WiFiSense em segundos",
    )

    # Monitor running
    gauge(
        "wifisense_monitor_running",
        1.0 if monitor_service.is_running else 0.0,
        "1 se o MonitorService está em execução, 0 caso contrário",
    )

    # Confidence
    result = monitor_service.current_result
    confidence = round(result.confidence, 4) if result else 0.0
    event_type = result.event_type.value if result else "no_presence"
    gauge(
        "wifisense_current_confidence",
        confidence,
        "Confiança da última detecção de evento",
        f'event_type="{event_type}"',
    )

    # Simulation mode
    is_sim = monitor_service.simulation_mode not in ("", None, "real")
    gauge(
        "wifisense_simulation_mode",
        1.0 if is_sim else 0.0,
        "1 se o sistema está em modo simulação, 0 se usando hardware real",
    )

    return "\n".join(lines) + "\n"
