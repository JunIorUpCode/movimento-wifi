"""
Camada de detecção — classes base.

Define a interface DetectorBase, o enum EventType e o dataclass
DetectionResult que todos os detectores devem seguir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.processing.signal_processor import ProcessedFeatures


class EventType(str, Enum):
    NO_PRESENCE = "no_presence"
    PRESENCE_STILL = "presence_still"
    PRESENCE_MOVING = "presence_moving"
    FALL_SUSPECTED = "fall_suspected"
    PROLONGED_INACTIVITY = "prolonged_inactivity"


@dataclass
class DetectionResult:
    """Resultado de uma detecção."""

    event_type: EventType
    confidence: float  # [0.0, 1.0]
    details: dict[str, Any] = field(default_factory=dict)


class DetectorBase(ABC):
    """Interface abstrata para detectores de eventos.

    Pode ser substituído por modelos de machine learning
    sem alterar o restante da arquitetura.
    """

    @abstractmethod
    def detect(self, features: ProcessedFeatures) -> DetectionResult:
        """Classifica o estado atual com base nas features processadas."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reseta estado interno do detector."""
        ...
