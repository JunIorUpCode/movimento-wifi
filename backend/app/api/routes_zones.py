"""
Rotas REST — Zonas de monitoramento.

Implementa Tarefa 23 | Requisitos: Fase 4
Endpoints:
  GET    /api/zones         — lista todas as zonas
  POST   /api/zones         — cria nova zona
  GET    /api/zones/current — zona atual com base no RSSI corrente
  GET    /api/zones/{id}    — obtém zona por ID
  PUT    /api/zones/{id}    — atualiza zona
  DELETE /api/zones/{id}    — remove zona
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Zone
from app.schemas.schemas import ZoneIn, ZoneOut
from app.services.monitor_service import monitor_service

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
async def list_zones(db: AsyncSession = Depends(get_db)):
    """Lista todas as zonas de monitoramento."""
    result = await db.execute(select(Zone).order_by(Zone.id))
    return result.scalars().all()


@router.post("", response_model=ZoneOut, status_code=201)
async def create_zone(data: ZoneIn, db: AsyncSession = Depends(get_db)):
    """
    Cria uma nova zona de monitoramento.

    Uma zona define uma faixa de RSSI (dBm) associada a uma área física.
    """
    if data.rssi_min >= data.rssi_max:
        raise HTTPException(
            status_code=422,
            detail="rssi_min deve ser menor que rssi_max.",
        )

    zone = Zone(
        name=data.name,
        rssi_min=data.rssi_min,
        rssi_max=data.rssi_max,
        alert_config_json=data.alert_config_json,
    )
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.get("/current")
async def get_current_zone(db: AsyncSession = Depends(get_db)):
    """
    Retorna a zona que corresponde ao RSSI do sinal atual.

    Compara o RSSI capturado mais recentemente contra as faixas definidas.
    Retorna ``null`` se nenhuma zona corresponder ao sinal atual.
    """
    signal = monitor_service.current_signal
    if signal is None:
        return {"current_zone": None, "rssi": None, "message": "Nenhum sinal capturado ainda."}

    rssi = signal.get("rssi") if isinstance(signal, dict) else getattr(signal, "rssi", None)
    if rssi is None:
        return {"current_zone": None, "rssi": None, "message": "RSSI não disponível."}

    result = await db.execute(select(Zone).order_by(Zone.id))
    zones = result.scalars().all()

    matched = next(
        (z for z in zones if z.rssi_min <= rssi <= z.rssi_max),
        None,
    )

    return {
        "current_zone": ZoneOut.model_validate(matched) if matched else None,
        "rssi": rssi,
        "message": f"Zona '{matched.name}' correspondente ao RSSI {rssi:.1f} dBm." if matched else "Nenhuma zona corresponde ao RSSI atual.",
    }


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    """Obtém zona pelo ID."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zona {zone_id} não encontrada.")
    return zone


@router.put("/{zone_id}", response_model=ZoneOut)
async def update_zone(zone_id: int, data: ZoneIn, db: AsyncSession = Depends(get_db)):
    """Atualiza zona existente."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zona {zone_id} não encontrada.")

    if data.rssi_min >= data.rssi_max:
        raise HTTPException(
            status_code=422,
            detail="rssi_min deve ser menor que rssi_max.",
        )

    zone.name = data.name
    zone.rssi_min = data.rssi_min
    zone.rssi_max = data.rssi_max
    zone.alert_config_json = data.alert_config_json

    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=204)
async def delete_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    """Remove zona pelo ID."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zona {zone_id} não encontrada.")

    await db.delete(zone)
    await db.commit()
