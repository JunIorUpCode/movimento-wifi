"""
WiFiSense Local — Ponto de entrada da aplicação FastAPI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.websocket import ws_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup e shutdown do aplicativo."""
    # Startup
    import os
    await init_db()
    print("[OK] WiFiSense Local - Backend iniciado")
    
    # Detectar tipo de banco
    db_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_url:
        db_name = db_url.split("/")[-1] if "/" in db_url else "PostgreSQL"
        print(f"[OK] Banco de dados PostgreSQL conectado: {db_name}")
    else:
        print("[OK] Banco de dados SQLite inicializado")
    
    yield
    # Shutdown
    from app.services.monitor_service import monitor_service
    if monitor_service.is_running:
        await monitor_service.stop()
    print("[STOP] WiFiSense Local - Backend encerrado")


app = FastAPI(
    title="WiFiSense Local",
    description="Sistema de monitoramento de presença e movimento via sinais Wi-Fi",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(ws_router)
