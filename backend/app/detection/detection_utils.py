"""
detection_utils.py — Tarefa 47: Utilidades de detecção melhorada.

Funções auxiliares que complementam o HeuristicDetector:
- detect_fall_enhanced: detecção de queda com múltiplos critérios e histórico
- estimate_occupancy: estimativa de ocupação baseada em janela temporal
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from app.detection.base import DetectionResult, EventType
from app.processing.signal_processor import ProcessedFeatures


@dataclass
class FallEnhancedResult:
    """Resultado estendido de detecção de queda."""

    is_fall: bool
    confidence: float                    # [0.0, 1.0]
    method: str                          # "rate_spike" | "energy_spike" | "combined" | "none"
    rate_of_change: float
    signal_energy: float
    instability_score: float
    details: dict = field(default_factory=dict)


@dataclass
class OccupancyEstimate:
    """Estimativa de ocupação do ambiente."""

    occupancy_probability: float         # [0.0, 1.0]
    is_likely_occupied: bool             # True se P >= 0.5
    average_energy: float
    movement_fraction: float             # Fração de amostras com movimento
    still_fraction: float                # Fração de amostras paradas
    empty_fraction: float                # Fração de amostras sem presença
    sample_count: int
    window_seconds: float


class FallDetectorEnhanced:
    """
    Detector de queda melhorado com múltiplos critérios e análise de histórico.

    Combina:
    1. Spike na taxa de variação do RSSI (critério original)
    2. Spike de energia + instabilidade alta (novo critério)
    3. Padrão sequencial: alta energia → queda súbita para baixa energia
    """

    def __init__(
        self,
        rate_spike_threshold: float = 8.0,
        energy_spike_threshold: float = 20.0,
        instability_threshold: float = 0.7,
        history_window: int = 10,
    ) -> None:
        self._rate_threshold = rate_spike_threshold
        self._energy_threshold = energy_spike_threshold
        self._instability_threshold = instability_threshold
        self._history: deque[ProcessedFeatures] = deque(maxlen=history_window)

    def reset(self) -> None:
        """Limpa o histórico interno."""
        self._history.clear()

    def detect_fall_enhanced(self, features: ProcessedFeatures) -> FallEnhancedResult:
        """
        Analisa features com múltiplos critérios para detectar queda.

        Critérios (em ordem de prioridade):
        1. Taxa de variação >= rate_spike_threshold → queda por rate spike
        2. Energia >= energy_spike_threshold E instabilidade alta → queda por energy spike
        3. Padrão sequencial: energia alta → energia muito baixa (imóvel pós-queda)

        Returns:
            FallEnhancedResult com método de detecção e confiança.
        """
        self._history.append(features)

        rate = features.rate_of_change
        energy = features.signal_energy
        instability = features.instability_score

        # Critério 1: Spike de taxa de variação
        if rate >= self._rate_threshold:
            confidence = min(1.0, 0.5 + (rate - self._rate_threshold) / self._rate_threshold * 0.5)
            return FallEnhancedResult(
                is_fall=True,
                confidence=confidence,
                method="rate_spike",
                rate_of_change=rate,
                signal_energy=energy,
                instability_score=instability,
                details={"rate_of_change": round(rate, 3), "threshold": self._rate_threshold},
            )

        # Critério 2: Spike de energia + alta instabilidade
        if energy >= self._energy_threshold and instability >= self._instability_threshold:
            confidence = min(1.0, 0.5 + instability * 0.5)
            return FallEnhancedResult(
                is_fall=True,
                confidence=confidence,
                method="energy_spike",
                rate_of_change=rate,
                signal_energy=energy,
                instability_score=instability,
                details={
                    "energy": round(energy, 3),
                    "instability": round(instability, 3),
                    "energy_threshold": self._energy_threshold,
                },
            )

        # Critério 3: Padrão sequencial (requer histórico suficiente)
        if len(self._history) >= 5:
            sequential_conf = self._detect_sequential_fall_pattern()
            if sequential_conf > 0.6:
                return FallEnhancedResult(
                    is_fall=True,
                    confidence=sequential_conf,
                    method="combined",
                    rate_of_change=rate,
                    signal_energy=energy,
                    instability_score=instability,
                    details={"pattern": "high_energy→sudden_stillness"},
                )

        return FallEnhancedResult(
            is_fall=False,
            confidence=0.0,
            method="none",
            rate_of_change=rate,
            signal_energy=energy,
            instability_score=instability,
        )

    def _detect_sequential_fall_pattern(self) -> float:
        """
        Detecta padrão: alta energia nas primeiras amostras → baixa energia recente.

        Retorna confiança [0.0, 1.0] do padrão detectado.
        """
        history = list(self._history)
        n = len(history)
        mid = n // 2

        early_energies = [f.signal_energy for f in history[:mid]]
        recent_energies = [f.signal_energy for f in history[mid:]]

        if not early_energies or not recent_energies:
            return 0.0

        avg_early = sum(early_energies) / len(early_energies)
        avg_recent = sum(recent_energies) / len(recent_energies)

        # Padrão de queda: energia alta no início, baixa no final
        if avg_early > self._energy_threshold * 0.5 and avg_recent < avg_early * 0.4:
            # Calcula confiança baseada na razão de queda
            ratio = avg_recent / avg_early if avg_early > 0 else 1.0
            confidence = min(1.0, 0.5 + (1.0 - ratio) * 0.5)
            return confidence

        return 0.0


class OccupancyEstimator:
    """
    Estima probabilidade de ocupação baseada em janela de detecções.

    Mantém histórico de resultados de detecção e calcula estatísticas
    de ocupação sobre a janela temporal.
    """

    def __init__(self, window_seconds: float = 60.0) -> None:
        self._window_seconds = window_seconds
        self._history: deque[tuple[float, EventType]] = deque()

    def reset(self) -> None:
        """Limpa o histórico."""
        self._history.clear()

    def update(self, result: DetectionResult) -> None:
        """
        Adiciona uma detecção ao histórico.

        Automaticamente remove entradas mais antigas que window_seconds.
        """
        now = time.time()
        self._history.append((now, result.event_type))
        # Remove entradas fora da janela
        cutoff = now - self._window_seconds
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

    def estimate_occupancy(self) -> OccupancyEstimate:
        """
        Calcula estimativa de ocupação baseada no histórico atual.

        Returns:
            OccupancyEstimate com probabilidade e frações por tipo de evento.
        """
        if not self._history:
            return OccupancyEstimate(
                occupancy_probability=0.0,
                is_likely_occupied=False,
                average_energy=0.0,
                movement_fraction=0.0,
                still_fraction=0.0,
                empty_fraction=1.0,
                sample_count=0,
                window_seconds=self._window_seconds,
            )

        total = len(self._history)
        events = [e for _, e in self._history]

        presence_types = {EventType.PRESENCE_STILL, EventType.PRESENCE_MOVING, EventType.PROLONGED_INACTIVITY, EventType.FALL_SUSPECTED}
        movement_types = {EventType.PRESENCE_MOVING, EventType.FALL_SUSPECTED}

        movement_count = sum(1 for e in events if e in movement_types)
        still_count = sum(1 for e in events if e in {EventType.PRESENCE_STILL, EventType.PROLONGED_INACTIVITY})
        empty_count = sum(1 for e in events if e == EventType.NO_PRESENCE)
        presence_count = sum(1 for e in events if e in presence_types)

        movement_fraction = movement_count / total
        still_fraction = still_count / total
        empty_fraction = empty_count / total
        occupancy_probability = presence_count / total

        return OccupancyEstimate(
            occupancy_probability=occupancy_probability,
            is_likely_occupied=occupancy_probability >= 0.5,
            average_energy=0.0,  # Não disponível sem acesso às features
            movement_fraction=movement_fraction,
            still_fraction=still_fraction,
            empty_fraction=empty_fraction,
            sample_count=total,
            window_seconds=self._window_seconds,
        )

    def estimate_occupancy_with_features(
        self,
        results_and_features: list[tuple[DetectionResult, ProcessedFeatures]],
    ) -> OccupancyEstimate:
        """
        Variante que recebe pares (DetectionResult, ProcessedFeatures) para
        calcular também a energia média.

        Args:
            results_and_features: Lista de (resultado, features) recentes.

        Returns:
            OccupancyEstimate com average_energy preenchido.
        """
        if not results_and_features:
            return self.estimate_occupancy()

        # Popula histórico temporariamente
        now = time.time()
        for result, _ in results_and_features:
            self._history.append((now, result.event_type))

        estimate = self.estimate_occupancy()

        # Calcula energia média
        energies = [f.signal_energy for _, f in results_and_features]
        estimate.average_energy = sum(energies) / len(energies) if energies else 0.0

        return estimate
