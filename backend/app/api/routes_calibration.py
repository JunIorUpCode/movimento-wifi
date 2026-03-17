"""
Rotas REST — Calibração do ambiente.

Implementa Tarefa 20 | Requisitos: Fase 4
Endpoints:
  POST /api/calibration/start          — inicia calibração em background
  GET  /api/calibration/progress       — status atual da calibração
  POST /api/calibration/stop           — cancela calibração em andamento
  GET  /api/calibration/profiles       — lista perfis salvos
  GET  /api/calibration/profiles/{name} — obtém perfil pelo nome
  POST /api/calibration/profiles/{name}/activate — ativa perfil
  DELETE /api/calibration/profiles/{name} — remove perfil
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import CalibrationProfile
from app.schemas.schemas import CalibrationProfileOut, CalibrationStartIn
from app.services.monitor_service import monitor_service

router = APIRouter(prefix="/calibration", tags=["calibration"])

# ─── estado global da calibração ─────────────────────────────────────────────

_calibration_task: Optional[asyncio.Task] = None
_calibration_status: dict = {
    "running": False,
    "profile_name": None,
    "duration_seconds": 0,
    "started_at": None,
    "error": None,
    "result": None,
}


def _get_calibration_service():
    """Retorna instância do CalibrationService usando o provider do monitor."""
    from app.services.calibration_service import CalibrationService

    return CalibrationService(provider=monitor_service._provider)


async def _run_calibration(duration_seconds: int, profile_name: str) -> None:
    """Executa calibração em background, atualizando status e broadcasts WebSocket."""
    import time as _time

    global _calibration_status
    _calibration_status["error"] = None
    _calibration_status["result"] = None

    try:
        svc = _get_calibration_service()

        # Inicia calibração intercalando broadcasts de progresso a cada 5 s
        svc._is_calibrating = True
        svc._calibration_samples.clear()
        start_time = _time.time()

        async def _progress_broadcaster():
            while _calibration_status["running"] and svc.is_calibrating:
                elapsed = _time.time() - start_time
                await monitor_service.broadcast_calibration_progress(
                    profile_name=profile_name,
                    elapsed_seconds=elapsed,
                    duration_seconds=duration_seconds,
                    phase="collecting",
                )
                await asyncio.sleep(5.0)

        broadcaster = asyncio.create_task(_progress_broadcaster())

        try:
            baseline = await svc.start_calibration(
                duration_seconds=duration_seconds,
                profile_name=profile_name,
            )
        finally:
            broadcaster.cancel()

        # Broadcast fase de cálculo
        await monitor_service.broadcast_calibration_progress(
            profile_name=profile_name,
            elapsed_seconds=duration_seconds,
            duration_seconds=duration_seconds,
            phase="calculating",
        )

        await svc.save_baseline(profile_name)

        _calibration_status["result"] = {
            "mean_rssi": round(baseline.mean_rssi, 3),
            "std_rssi": round(baseline.std_rssi, 3),
            "mean_variance": round(baseline.mean_variance, 3),
            "noise_floor": round(baseline.noise_floor, 3),
            "samples_count": baseline.samples_count,
        }

        # Broadcast conclusão
        await monitor_service.broadcast_calibration_progress(
            profile_name=profile_name,
            elapsed_seconds=duration_seconds,
            duration_seconds=duration_seconds,
            phase="done",
        )

    except asyncio.CancelledError:
        _calibration_status["error"] = "Calibração cancelada pelo usuário."
        await monitor_service.broadcast_calibration_progress(
            profile_name=profile_name,
            elapsed_seconds=0,
            duration_seconds=duration_seconds,
            phase="error",
        )
    except Exception as exc:
        _calibration_status["error"] = str(exc)
        await monitor_service.broadcast_calibration_progress(
            profile_name=profile_name,
            elapsed_seconds=0,
            duration_seconds=duration_seconds,
            phase="error",
        )
    finally:
        _calibration_status["running"] = False


# ─── endpoints ────────────────────────────────────────────────────────────────


@router.post("/start", status_code=202)
async def start_calibration(data: CalibrationStartIn):
    """
    Inicia calibração do ambiente em background.

    O ambiente deve estar **vazio** (sem pessoas) durante a calibração.
    Retorna imediatamente com status 202; consulte GET /progress para acompanhar.
    """
    global _calibration_task, _calibration_status

    if _calibration_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Calibração já está em andamento. Use POST /stop para cancelar.",
        )

    import time

    _calibration_status.update(
        {
            "running": True,
            "profile_name": data.profile_name,
            "duration_seconds": data.duration_seconds,
            "started_at": time.time(),
            "error": None,
            "result": None,
        }
    )

    _calibration_task = asyncio.create_task(
        _run_calibration(data.duration_seconds, data.profile_name)
    )

    return {
        "status": "started",
        "profile_name": data.profile_name,
        "duration_seconds": data.duration_seconds,
        "message": f"Calibração iniciada. Mantenha o ambiente vazio por {data.duration_seconds}s.",
    }


@router.get("/progress")
async def get_calibration_progress():
    """Retorna status atual da calibração (em andamento, concluída ou com erro)."""
    import time

    elapsed = None
    if _calibration_status["running"] and _calibration_status["started_at"]:
        elapsed = round(time.time() - _calibration_status["started_at"], 1)

    return {
        "running": _calibration_status["running"],
        "profile_name": _calibration_status["profile_name"],
        "duration_seconds": _calibration_status["duration_seconds"],
        "elapsed_seconds": elapsed,
        "error": _calibration_status["error"],
        "result": _calibration_status["result"],
    }


@router.post("/stop")
async def stop_calibration():
    """Cancela calibração em andamento."""
    global _calibration_task, _calibration_status

    if not _calibration_status["running"]:
        raise HTTPException(status_code=400, detail="Nenhuma calibração em andamento.")

    if _calibration_task and not _calibration_task.done():
        _calibration_task.cancel()

    _calibration_status["running"] = False
    return {"status": "stopped", "message": "Calibração cancelada."}


@router.get("/profiles", response_model=list[CalibrationProfileOut])
async def list_calibration_profiles(db: AsyncSession = Depends(get_db)):
    """Lista todos os perfis de calibração salvos."""
    result = await db.execute(
        select(CalibrationProfile).order_by(CalibrationProfile.created_at.desc())
    )
    return result.scalars().all()


@router.get("/profiles/{name}", response_model=CalibrationProfileOut)
async def get_calibration_profile(name: str, db: AsyncSession = Depends(get_db)):
    """Obtém perfil de calibração pelo nome."""
    result = await db.execute(
        select(CalibrationProfile).where(CalibrationProfile.name == name)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Perfil '{name}' não encontrado.")
    return profile


@router.post("/profiles/{name}/activate")
async def activate_calibration_profile(name: str, db: AsyncSession = Depends(get_db)):
    """
    Ativa um perfil de calibração.

    Desativa todos os outros perfis e carrega o baseline selecionado
    no CalibrationService em memória.
    """
    result = await db.execute(
        select(CalibrationProfile).where(CalibrationProfile.name == name)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Perfil '{name}' não encontrado.")

    # Desativa todos os perfis
    await db.execute(update(CalibrationProfile).values(is_active=False))
    # Ativa o selecionado
    profile.is_active = True
    await db.commit()

    # Carrega baseline em memória
    try:
        from app.services.calibration_service import BaselineData

        baseline_dict = json.loads(profile.baseline_json)
        svc = _get_calibration_service()
        svc.set_baseline(BaselineData(**baseline_dict))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Perfil ativado no banco mas não carregado em memória: {exc}",
        )

    return {"status": "activated", "profile_name": name}


@router.delete("/profiles/{name}", status_code=204)
async def delete_calibration_profile(name: str, db: AsyncSession = Depends(get_db)):
    """Remove perfil de calibração pelo nome."""
    result = await db.execute(
        select(CalibrationProfile).where(CalibrationProfile.name == name)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Perfil '{name}' não encontrado.")

    await db.delete(profile)
    await db.commit()
