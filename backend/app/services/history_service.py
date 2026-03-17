"""
HistoryService — Persistência de eventos no SQLite.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Event
from app.schemas.schemas import EventOut


class HistoryService:
    """CRUD de eventos no banco de dados."""

    @staticmethod
    async def save_event(
        db: AsyncSession,
        event_type: str,
        confidence: float,
        provider: str = "mock",
        metadata: dict | None = None,
    ) -> Event:
        """Salva um evento no banco."""
        event = Event(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            confidence=confidence,
            provider=provider,
            metadata_json=json.dumps(metadata or {}),
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_events(
        db: AsyncSession,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> list[EventOut]:
        """Retorna eventos do histórico, mais recentes primeiro."""
        query = select(Event).order_by(desc(Event.timestamp)).limit(limit)
        if event_type:
            query = query.where(Event.event_type == event_type)
        result = await db.execute(query)
        events = result.scalars().all()
        return [EventOut.model_validate(e) for e in events]

    @staticmethod
    async def get_event_count(db: AsyncSession) -> int:
        """Retorna contagem total de eventos."""
        from sqlalchemy import func
        result = await db.execute(select(func.count(Event.id)))
        return result.scalar() or 0
