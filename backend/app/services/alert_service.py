"""
AlertService — Sistema de alertas locais.

Gera alertas visuais para eventos críticos como quedas e inatividade.
Estrutura preparada para futura integração com WhatsApp, SMS ou push.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.detection.base import EventType


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Representa um alerta gerado pelo sistema."""

    level: AlertLevel
    message: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class AlertService:
    """Gerencia alertas do sistema."""

    def __init__(self) -> None:
        self._active_alerts: list[Alert] = []
        self._alert_history: list[Alert] = []

    def evaluate(self, event_type: EventType, confidence: float) -> Optional[Alert]:
        """Avalia se o evento deve gerar um alerta."""
        alert: Optional[Alert] = None

        if event_type == EventType.FALL_SUSPECTED:
            alert = Alert(
                level=AlertLevel.CRITICAL,
                message=f"Possível queda detectada com {confidence:.0%} de confiança",
                event_type=event_type.value,
            )
        elif event_type == EventType.PROLONGED_INACTIVITY:
            alert = Alert(
                level=AlertLevel.WARNING,
                message=f"Sem movimento detectado há mais de 30 segundos",
                event_type=event_type.value,
            )
        elif event_type == EventType.PRESENCE_MOVING:
            # MODO TESTE: Alerta para qualquer movimento
            # Útil para segurança (casa vazia) ou testes
            alert = Alert(
                level=AlertLevel.INFO,
                message=f"Atividade detectada no ambiente",
                event_type=event_type.value,
            )
        elif event_type == EventType.PRESENCE_STILL:
            # Alerta quando detecta presença parada (alguém está no local)
            alert = Alert(
                level=AlertLevel.INFO,
                message=f"Pessoa presente no ambiente",
                event_type=event_type.value,
            )

        if alert:
            self._active_alerts.append(alert)
            self._alert_history.append(alert)
            # Limita histórico em memória
            if len(self._alert_history) > 200:
                self._alert_history = self._alert_history[-100:]

        return alert

    @property
    def active_alerts(self) -> list[Alert]:
        return [a for a in self._active_alerts if not a.acknowledged]

    def acknowledge_all(self) -> None:
        """Marca todos os alertas ativos como reconhecidos."""
        for a in self._active_alerts:
            a.acknowledged = True

    def clear(self) -> None:
        self._active_alerts.clear()


# Instância global
alert_service = AlertService()
