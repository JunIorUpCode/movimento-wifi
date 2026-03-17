"""
WiFiSense Local — Ponto de entrada da aplicação FastAPI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.routes_calibration import router as calibration_router
from app.api.routes_export import router as export_router
from app.api.routes_health import health_router, metrics_router
from app.api.routes_ml import router as ml_router
from app.api.routes_stats import router as stats_router
from app.api.routes_zones import router as zones_router
from app.api.websocket import ws_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup e shutdown do aplicativo."""
    import os
    from app.services.monitor_service import monitor_service

    # Inicializa banco de dados
    await init_db()
    print("[OK] WiFiSense Local - Backend iniciado")

    # Detectar tipo de banco
    db_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_url:
        db_name = db_url.split("/")[-1] if "/" in db_url else "PostgreSQL"
        print(f"[OK] Banco de dados PostgreSQL conectado: {db_name}")
    else:
        print("[OK] Banco de dados SQLite inicializado")

    # Conecta RabbitMQ ao MonitorService (opcional — modo standalone funciona sem ele)
    try:
        import sys
        from pathlib import Path as _Path

        # Resolve o caminho do projeto de forma segura e portável
        _project_root = _Path(__file__).resolve().parent.parent.parent
        _shared_dir = _project_root / "shared"

        if _shared_dir.exists() and str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))

        from shared.rabbitmq import get_rabbitmq_client
        rabbitmq_client = await get_rabbitmq_client()
        await monitor_service.initialize_rabbitmq(rabbitmq_client)
        print("[OK] RabbitMQ conectado — eventos serão publicados na fila 'event_processing'")
    except Exception as e:
        print(f"[WARN] RabbitMQ não disponível: {e}. Modo standalone (sem publicação de eventos).")

    yield

    # Shutdown
    if monitor_service.is_running:
        await monitor_service.stop()
    print("[STOP] WiFiSense Local - Backend encerrado")


app = FastAPI(
    title="WiFiSense Local",
    description=(
        "## WiFiSense Local — API de Monitoramento de Presença via Wi-Fi\n\n"
        "Sistema de detecção de presença, movimento e quedas usando análise de sinais Wi-Fi "
        "(RSSI/CSI) — **sem câmeras**.\n\n"
        "### Grupos de Endpoints\n"
        "| Grupo | Prefixo | Descrição |\n"
        "|-------|---------|-----------|\n"
        "| **Monitor** | `/api/signal` | Captura de sinal, modo de operação, configuração |\n"
        "| **Calibração** | `/api/calibration` | Iniciar/parar calibração, perfis |\n"
        "| **ML** | `/api/ml` | Coleta de dados, rotulação, treino, modelos |\n"
        "| **Zonas** | `/api/zones` | Gerenciamento de zonas RSSI |\n"
        "| **Notificações** | `/api/notifications` | Configuração e logs de alertas |\n"
        "| **Estatísticas** | `/api/stats` | Agregações, padrões, anomalias, performance |\n"
        "| **Exportação** | `/api/export` | CSV, JSON, backup ZIP |\n"
        "| **Saúde** | `/api/health` | Readiness probe, status do sistema |\n"
        "| **Métricas** | `/metrics` | Métricas Prometheus |\n"
        "| **WebSocket** | `/ws` | Stream em tempo real de eventos |\n\n"
        "### Autenticação\n"
        "API local — sem autenticação. Acesso restrito à rede local.\n\n"
        "### WebSocket\n"
        "Conecte em `ws://localhost:8000/ws` para receber eventos em tempo real:\n"
        "- `live_update` — atualização de sinal/detecção\n"
        "- `calibration_progress` — progresso de calibração\n"
        "- `anomaly_detected` — anomalia crítica (queda, inatividade)\n"
        "- `notification_sent` — notificação enviada por canal\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "WiFiSense",
        "url": "http://localhost:5173",
    },
    license_info={
        "name": "Proprietário",
    },
)

# CORS — permite frontend na porta 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(router, prefix="/api")
app.include_router(calibration_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(zones_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router)       # /metrics na raiz (Prometheus)
app.include_router(ws_router)
