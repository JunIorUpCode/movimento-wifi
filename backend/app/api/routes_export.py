"""
Rotas REST — Exportação de dados.

Implementa Tarefa 25 | Requisitos: Fase 4
Endpoints:
  GET /api/export/events.csv  — exporta eventos em CSV
  GET /api/export/events.json — exporta eventos em JSON
  GET /api/export/backup      — backup completo (ZIP com CSV + JSON + perfis)
"""

from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import CalibrationProfile, Event, Zone

router = APIRouter(prefix="/export", tags=["export"])


# ─── helpers ─────────────────────────────────────────────────────────────────


async def _fetch_events(
    db: AsyncSession,
    period_hours: int,
    limit: int,
) -> list[Event]:
    since = datetime.utcnow() - timedelta(hours=period_hours)
    result = await db.execute(
        select(Event)
        .where(Event.timestamp >= since)
        .order_by(Event.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


def _event_to_dict(e: Event) -> dict:
    return {
        "id": e.id,
        "timestamp": e.timestamp.isoformat(),
        "event_type": e.event_type,
        "confidence": e.confidence,
        "provider": e.provider,
        "metadata_json": e.metadata_json,
    }


# ─── CSV ─────────────────────────────────────────────────────────────────────


@router.get("/events.csv")
async def export_events_csv(
    period_hours: int = Query(default=24, ge=1, le=720, description="Período em horas"),
    limit: int = Query(default=10000, ge=1, le=100000, description="Limite de registros"),
    db: AsyncSession = Depends(get_db),
):
    """
    Exporta histórico de eventos como CSV para download.

    Colunas: id, timestamp, event_type, confidence, provider, metadata_json
    """
    events = await _fetch_events(db, period_hours, limit)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "timestamp", "event_type", "confidence", "provider", "metadata_json"],
    )
    writer.writeheader()
    for e in events:
        writer.writerow(_event_to_dict(e))

    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── JSON ────────────────────────────────────────────────────────────────────


@router.get("/events.json")
async def export_events_json(
    period_hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=10000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
):
    """
    Exporta histórico de eventos como JSON para download.
    """
    events = await _fetch_events(db, period_hours, limit)

    payload = {
        "exported_at": datetime.utcnow().isoformat(),
        "period_hours": period_hours,
        "total": len(events),
        "events": [_event_to_dict(e) for e in events],
    }

    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Backup ZIP ──────────────────────────────────────────────────────────────


@router.get("/backup")
async def export_backup(
    period_hours: int = Query(default=168, ge=1, le=720, description="Período em horas (padrão: 7 dias)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera backup completo em ZIP contendo:
    - ``events.csv`` — histórico de eventos
    - ``events.json`` — histórico de eventos (JSON)
    - ``calibration_profiles.json`` — perfis de calibração
    - ``zones.json`` — zonas de monitoramento
    - ``manifest.json`` — metadados do backup
    """
    events = await _fetch_events(db, period_hours, limit=100000)

    # Perfis de calibração
    profiles_result = await db.execute(select(CalibrationProfile))
    profiles = [
        {
            "id": p.id,
            "name": p.name,
            "baseline_json": p.baseline_json,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "is_active": p.is_active,
        }
        for p in profiles_result.scalars().all()
    ]

    # Zonas
    zones_result = await db.execute(select(Zone))
    zones = [
        {
            "id": z.id,
            "name": z.name,
            "rssi_min": z.rssi_min,
            "rssi_max": z.rssi_max,
            "alert_config_json": z.alert_config_json,
            "created_at": z.created_at.isoformat(),
        }
        for z in zones_result.scalars().all()
    ]

    exported_at = datetime.utcnow().isoformat()
    events_list = [_event_to_dict(e) for e in events]

    # Cria ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # events.csv
        csv_io = io.StringIO()
        writer = csv.DictWriter(
            csv_io,
            fieldnames=["id", "timestamp", "event_type", "confidence", "provider", "metadata_json"],
        )
        writer.writeheader()
        for row in events_list:
            writer.writerow(row)
        zf.writestr("events.csv", csv_io.getvalue())

        # events.json
        zf.writestr(
            "events.json",
            json.dumps(
                {"exported_at": exported_at, "total": len(events_list), "events": events_list},
                ensure_ascii=False,
                indent=2,
            ),
        )

        # calibration_profiles.json
        zf.writestr(
            "calibration_profiles.json",
            json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2),
        )

        # zones.json
        zf.writestr(
            "zones.json",
            json.dumps({"zones": zones}, ensure_ascii=False, indent=2),
        )

        # manifest.json
        manifest = {
            "exported_at": exported_at,
            "period_hours": period_hours,
            "events_count": len(events_list),
            "profiles_count": len(profiles),
            "zones_count": len(zones),
            "version": "1.0.0",
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    zip_bytes = zip_buffer.getvalue()
    filename = f"wifisense_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
