"""
HeuristicDetector — Detector baseado em regras e limiares.

Classifica eventos usando heurísticas simples sobre as features
processadas. Preparado para ser substituído por modelo ML.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.detection.base import DetectionResult, DetectorBase, EventType
from app.processing.signal_processor import ProcessedFeatures


@dataclass
class ThresholdConfig:
    """Limiares configuráveis para o detector heurístico."""

    # Presença vs ausência
    presence_energy_min: float = 2.0  # Reduzido de 4.0 para detectar presença mais facilmente
    presence_rssi_norm_min: float = 0.25  # Reduzido de 0.35

    # Movimento (ajustado para Wi-Fi real - variações são menores)
    movement_variance_min: float = 0.5  # Reduzido de 2.0 - Wi-Fi real tem variância menor
    movement_rate_min: float = 1.0  # Reduzido de 3.0 - mudanças de RSSI são mais sutis

    # Queda (ajustado para facilitar testes)
    fall_rate_spike: float = 8.0  # Reduzido de 12.0 para detectar quedas mais facilmente
    fall_energy_spike: float = 20.0  # Reduzido de 25.0

    # Inatividade prolongada (segundos)
    inactivity_timeout: float = 30.0
    inactivity_variance_max: float = 0.5


class HeuristicDetector(DetectorBase):
    """Detector baseado em regras heurísticas."""

    def __init__(self, config: ThresholdConfig | None = None) -> None:
        self._config = config or ThresholdConfig()
        self._still_since: float | None = None
        self._last_event: EventType = EventType.NO_PRESENCE

    def reset(self) -> None:
        self._still_since = None
        self._last_event = EventType.NO_PRESENCE

    def update_config(self, config: ThresholdConfig) -> None:
        self._config = config

    def detect(self, features: ProcessedFeatures) -> DetectionResult:
        cfg = self._config
        now = time.time()

        # 1. Verifica queda — pico brusco de energia + taxa de variação
        if (
            features.rate_of_change >= cfg.fall_rate_spike
            or features.signal_energy >= cfg.fall_energy_spike
        ):
            self._still_since = now
            self._last_event = EventType.FALL_SUSPECTED
            return DetectionResult(
                event_type=EventType.FALL_SUSPECTED,
                confidence=min(1.0, features.instability_score + 0.5),
                details={
                    "rate_of_change": round(features.rate_of_change, 3),
                    "energy": round(features.signal_energy, 3),
                },
            )

        # 2. Verifica presença
        has_presence = (
            features.signal_energy >= cfg.presence_energy_min
            or features.rssi_normalized >= cfg.presence_rssi_norm_min
        )

        if not has_presence:
            self._still_since = None
            self._last_event = EventType.NO_PRESENCE
            return DetectionResult(
                event_type=EventType.NO_PRESENCE,
                confidence=0.85,
                details={"energy": round(features.signal_energy, 3)},
            )

        # 3. Presença detectada — verifica movimento
        is_moving = (
            features.signal_variance >= cfg.movement_variance_min
            or features.rate_of_change >= cfg.movement_rate_min
        )

        if is_moving:
            self._still_since = None
            self._last_event = EventType.PRESENCE_MOVING
            return DetectionResult(
                event_type=EventType.PRESENCE_MOVING,
                confidence=min(1.0, 0.6 + features.instability_score * 0.4),
                details={
                    "variance": round(features.signal_variance, 3),
                    "rate": round(features.rate_of_change, 3),
                },
            )

        # 4. Presença parada — verifica inatividade prolongada
        if self._still_since is None:
            self._still_since = now

        still_duration = now - self._still_since

        if still_duration >= cfg.inactivity_timeout:
            self._last_event = EventType.PROLONGED_INACTIVITY
            return DetectionResult(
                event_type=EventType.PROLONGED_INACTIVITY,
                confidence=min(1.0, 0.5 + still_duration / 120.0),
                details={"still_seconds": round(still_duration, 1)},
            )

        # 5. Presença parada normal
        self._last_event = EventType.PRESENCE_STILL
        return DetectionResult(
            event_type=EventType.PRESENCE_STILL,
            confidence=0.75,
            details={"still_seconds": round(still_duration, 1)},
        )
