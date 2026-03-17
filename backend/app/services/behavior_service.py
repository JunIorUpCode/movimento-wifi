"""
Serviço de detecção de padrões de comportamento.

Aprende padrões de rotina do usuário e detecta comportamentos anormais.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.detection.base import EventType
from app.models.models import BehaviorPattern, Event


class BehaviorService:
    """Serviço de análise de padrões de comportamento."""

    _instance: Optional[BehaviorService] = None

    def __new__(cls) -> BehaviorService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._patterns_cache: List[BehaviorPattern] = []
        self._last_cache_update: Optional[datetime] = None

    async def learn_behavior_patterns(
        self, min_days: int = 7
    ) -> List[BehaviorPattern]:
        """
        Aprende padrões de comportamento a partir do histórico de eventos.

        Args:
            min_days: Mínimo de dias de dados necessários

        Returns:
            Lista de BehaviorPattern (até 168 padrões = 24h x 7 dias)

        Raises:
            ValueError: Se não houver dados suficientes
        """
        async with async_session() as db:
            # Busca eventos históricos
            result = await db.execute(
                select(Event).order_by(Event.timestamp.asc())
            )
            events = result.scalars().all()

            if not events:
                raise ValueError("No events found in database")

            # Verifica se há dados suficientes
            date_range = events[-1].timestamp - events[0].timestamp
            if date_range < timedelta(days=min_days):
                raise ValueError(
                    f"Need at least {min_days} days of data, "
                    f"but only have {date_range.days} days"
                )

            # Agrupa por (hora, dia_da_semana)
            patterns_data = {}
            for hour in range(24):
                for day in range(7):
                    patterns_data[(hour, day)] = {
                        "presence_count": 0,
                        "total_count": 0,
                        "movement_levels": [],
                    }

            # Processa eventos
            for event in events:
                dt = event.timestamp
                hour = dt.hour
                day = dt.weekday()

                key = (hour, day)
                patterns_data[key]["total_count"] += 1

                # Conta presença
                if event.event_type in ["presence_still", "presence_moving"]:
                    patterns_data[key]["presence_count"] += 1

                    # Estima nível de movimento
                    if event.event_type == "presence_moving":
                        movement_level = 1.0
                    else:
                        movement_level = 0.2
                    patterns_data[key]["movement_levels"].append(movement_level)

            # Calcula estatísticas e cria padrões
            behavior_patterns = []
            for (hour, day), data in patterns_data.items():
                # Requer pelo menos 1 amostra (ajustável para produção)
                if data["total_count"] < 1:
                    continue

                presence_prob = data["presence_count"] / data["total_count"]
                avg_movement = (
                    float(np.mean(data["movement_levels"]))
                    if data["movement_levels"]
                    else 0.0
                )

                pattern = BehaviorPattern(
                    hour_of_day=hour,
                    day_of_week=day,
                    presence_probability=presence_prob,
                    avg_movement_level=avg_movement,
                    sample_count=data["total_count"],
                    last_updated=datetime.utcnow(),
                )
                behavior_patterns.append(pattern)

            # Persiste padrões no banco
            await self._persist_patterns(db, behavior_patterns)

            # Atualiza cache
            self._patterns_cache = behavior_patterns
            self._last_cache_update = datetime.utcnow()

            return behavior_patterns

    async def _persist_patterns(
        self, db: AsyncSession, patterns: List[BehaviorPattern]
    ) -> None:
        """
        Persiste padrões no banco de dados.

        Remove padrões antigos e insere novos.
        """
        # Remove padrões existentes
        await db.execute(BehaviorPattern.__table__.delete())

        # Adiciona novos padrões
        for pattern in patterns:
            db.add(pattern)

        await db.commit()

    async def detect_anomalous_behavior(
        self, current_event: EventType, current_time: datetime
    ) -> Tuple[bool, float, str]:
        """
        Detecta comportamento anômalo comparando com padrões aprendidos.

        Args:
            current_event: Tipo de evento atual
            current_time: Timestamp atual

        Returns:
            Tupla (is_anomaly, score, description)
            - is_anomaly: True se comportamento é anômalo
            - score: Score de anomalia [0.0-1.0]
            - description: Descrição textual da anomalia
        """
        # Carrega padrões (usa cache se disponível)
        patterns = await self._get_patterns()

        if not patterns:
            return False, 0.0, "No patterns learned yet"

        hour = current_time.hour
        day = current_time.weekday()

        # Busca padrão correspondente
        pattern = next(
            (
                p
                for p in patterns
                if p.hour_of_day == hour and p.day_of_week == day
            ),
            None,
        )

        if not pattern or pattern.sample_count < 1:
            return False, 0.0, "Insufficient data for this time slot"

        # Calcula desvio
        is_present = current_event in [
            EventType.PRESENCE_STILL,
            EventType.PRESENCE_MOVING,
        ]
        expected_presence = pattern.presence_probability

        # Anomalia se divergência > 2 desvios padrão
        # Assumindo distribuição binomial: std = sqrt(p * (1-p) / n)
        std = np.sqrt(
            expected_presence * (1 - expected_presence) / pattern.sample_count
        )

        if is_present:
            deviation = (1.0 - expected_presence) / max(std, 0.1)
        else:
            deviation = expected_presence / max(std, 0.1)

        is_anomaly = abs(deviation) > 2.0
        anomaly_score = min(abs(deviation) / 3.0, 1.0)  # Normaliza para 0-1

        # Descrição
        day_names = [
            "segunda",
            "terça",
            "quarta",
            "quinta",
            "sexta",
            "sábado",
            "domingo",
        ]
        if is_present and expected_presence < 0.3:
            description = (
                f"Presença incomum para {day_names[day]} às {hour}h "
                f"(esperado: {expected_presence:.0%})"
            )
        elif not is_present and expected_presence > 0.7:
            description = (
                f"Ausência incomum para {day_names[day]} às {hour}h "
                f"(esperado: {expected_presence:.0%})"
            )
        else:
            description = "Comportamento dentro do esperado"

        return is_anomaly, anomaly_score, description

    async def _get_patterns(self) -> List[BehaviorPattern]:
        """
        Obtém padrões do cache ou banco de dados.

        Atualiza cache se estiver desatualizado (>1 hora).
        """
        # Usa cache se disponível e recente
        if (
            self._patterns_cache
            and self._last_cache_update
            and (datetime.utcnow() - self._last_cache_update)
            < timedelta(hours=1)
        ):
            return self._patterns_cache

        # Carrega do banco
        async with async_session() as db:
            result = await db.execute(select(BehaviorPattern))
            patterns = list(result.scalars().all())

            self._patterns_cache = patterns
            self._last_cache_update = datetime.utcnow()

            return patterns

    async def get_pattern_for_time(
        self, hour: int, day: int
    ) -> Optional[BehaviorPattern]:
        """
        Obtém padrão para hora e dia específicos.

        Args:
            hour: Hora do dia (0-23)
            day: Dia da semana (0-6, 0=segunda)

        Returns:
            BehaviorPattern ou None se não encontrado
        """
        patterns = await self._get_patterns()
        return next(
            (
                p
                for p in patterns
                if p.hour_of_day == hour and p.day_of_week == day
            ),
            None,
        )

    def clear_cache(self) -> None:
        """Limpa cache de padrões."""
        self._patterns_cache = []
        self._last_cache_update = None


# Instância global
behavior_service = BehaviorService()
