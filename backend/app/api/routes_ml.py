"""
Rotas REST — Machine Learning (coleta de dados e treinamento).

Implementa Tarefa 21 | Requisitos: Fase 4
Endpoints (além de /ml/models já existente em routes.py):
  POST GET  /api/ml/data-collection/start  — ativa modo de coleta
  POST      /api/ml/data-collection/stop   — desativa modo de coleta
  GET       /api/ml/data-collection/status — status e estatísticas da coleta
  POST      /api/ml/label                  — rotula evento (janela de tempo)
  GET       /api/ml/export                 — baixa dataset como CSV
  POST      /api/ml/train                  — dispara treinamento do modelo
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.schemas import MLCollectionStatusOut, MLLabelIn
from app.services.ml_service import ml_service

router = APIRouter(prefix="/ml", tags=["ml"])


# ─── coleta de dados ──────────────────────────────────────────────────────────


@router.post("/data-collection/start")
async def start_data_collection():
    """
    Ativa o modo de coleta de dados para treinamento ML.

    Enquanto ativo, todas as features processadas são armazenadas em buffer
    para posterior rotulação via POST /ml/label.
    """
    if ml_service.is_collecting:
        raise HTTPException(
            status_code=409,
            detail="Coleta já está ativa. Use POST /data-collection/stop para parar.",
        )
    ml_service.start_data_collection()
    return {"status": "started", "message": "Coleta de dados ML ativada."}


@router.post("/data-collection/stop")
async def stop_data_collection():
    """
    Desativa o modo de coleta de dados.

    As amostras já coletadas permanecem disponíveis para exportação.
    """
    if not ml_service.is_collecting:
        raise HTTPException(status_code=400, detail="Coleta não está ativa.")
    ml_service.stop_data_collection()
    return {
        "status": "stopped",
        "samples_collected": ml_service.samples_count,
        "message": "Coleta de dados ML desativada.",
    }


@router.get("/data-collection/status", response_model=MLCollectionStatusOut)
async def get_data_collection_status():
    """Retorna status e estatísticas da coleta de dados ML."""
    stats = ml_service.get_collection_stats()
    return MLCollectionStatusOut(
        is_collecting=stats["is_collecting"],
        total_samples=stats["total_samples"],
        pending_features=stats["pending_features"],
        label_distribution=stats["label_distribution"],
        models_dir=stats["models_dir"],
    )


# ─── rotulação ────────────────────────────────────────────────────────────────


@router.post("/label")
async def label_event(data: MLLabelIn):
    """
    Rotula as features dos últimos N segundos com o rótulo fornecido.

    Rótulos válidos:
    - ``no_presence`` — ambiente vazio
    - ``presence_still`` — presença parada
    - ``presence_moving`` — presença em movimento
    - ``fall_suspected`` — queda suspeita
    - ``prolonged_inactivity`` — inatividade prolongada

    Requer que a coleta esteja ativa (POST /data-collection/start).
    """
    if not ml_service.is_collecting:
        raise HTTPException(
            status_code=409,
            detail="Coleta não está ativa. Inicie com POST /data-collection/start.",
        )

    count = ml_service.label_event(
        label=data.label,
        window_seconds=data.window_seconds,
    )

    if count == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Rótulo inválido '{data.label}' ou nenhuma feature disponível na janela. "
                "Rótulos válidos: no_presence, presence_still, presence_moving, "
                "fall_suspected, prolonged_inactivity."
            ),
        )

    return {
        "status": "labeled",
        "label": data.label,
        "samples_labeled": count,
        "total_samples": ml_service.samples_count,
    }


# ─── exportação ──────────────────────────────────────────────────────────────


@router.get("/export")
async def export_dataset(filename: str = "training_data", include_metadata: bool = True):
    """
    Exporta o dataset coletado como arquivo CSV para download.

    Parâmetros:
    - ``filename``: nome do arquivo (sem extensão)
    - ``include_metadata``: inclui colunas de metadados (padrão: True)
    """
    if ml_service.samples_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma amostra coletada. Inicie a coleta e rotule eventos primeiro.",
        )

    # Valida nome do arquivo (previne path traversal)
    import re

    if not re.match(r"^[a-zA-Z0-9_\-]+$", filename):
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    try:
        output_path = await ml_service.export_dataset(
            filename=filename,
            include_metadata=include_metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return FileResponse(
        path=str(output_path),
        media_type="text/csv",
        filename=f"{filename}.csv",
    )


# ─── treinamento ─────────────────────────────────────────────────────────────


_train_task: dict = {"running": False, "error": None, "result": None}


@router.post("/train", status_code=202)
async def trigger_training(csv_path: str = "models/training_data.csv"):
    """
    Dispara o script de treinamento do modelo ML em background.

    Requer que o arquivo CSV exista em ``csv_path`` (relativo à raiz do backend).
    O script ``train_model.py`` gera o arquivo ``classifier.pkl`` em ``models/``.
    """
    global _train_task

    if _train_task["running"]:
        raise HTTPException(
            status_code=409,
            detail="Treinamento já está em andamento.",
        )

    # Valida path (previne traversal)
    backend_root = Path(__file__).resolve().parent.parent.parent
    csv_resolved = (backend_root / csv_path).resolve()
    if not str(csv_resolved).startswith(str(backend_root)):
        raise HTTPException(status_code=400, detail="Caminho de CSV inválido.")

    if not csv_resolved.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo CSV não encontrado: {csv_path}",
        )

    train_script = backend_root / "train_model.py"
    if not train_script.exists():
        raise HTTPException(status_code=500, detail="Script train_model.py não encontrado.")

    async def _run():
        global _train_task
        _train_task.update({"running": True, "error": None, "result": None})
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(train_script),
                "--csv",
                str(csv_resolved),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(backend_root),
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                _train_task["result"] = "Treinamento concluído com sucesso."
            else:
                _train_task["error"] = stderr.decode(errors="replace")
        except Exception as exc:
            _train_task["error"] = str(exc)
        finally:
            _train_task["running"] = False

    asyncio.create_task(_run())

    return {
        "status": "started",
        "csv_path": str(csv_resolved),
        "message": "Treinamento iniciado em background. Consulte GET /ml/train/status.",
    }


@router.get("/train/status")
async def get_training_status():
    """Retorna status do último treinamento iniciado via POST /ml/train."""
    return {
        "running": _train_task["running"],
        "error": _train_task["error"],
        "result": _train_task["result"],
    }
