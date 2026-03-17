"""
Processador de sinal — Normalização, suavização, extração de features.

Mantém janela temporal deslizante e calcula métricas derivadas
do sinal bruto para alimentar a camada de detecção.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from app.capture.base import SignalData


@dataclass
class ProcessedFeatures:
    """Features extraídas do sinal processado."""

    rssi_normalized: float        # RSSI normalizado [0, 1]
    rssi_smoothed: float          # RSSI suavizado
    signal_energy: float          # Energia média do CSI
    signal_variance: float        # Variância do CSI
    rate_of_change: float         # Taxa de variação do RSSI
    instability_score: float      # Score de instabilidade do ambiente [0, 1]
    csi_mean_amplitude: float     # Amplitude média das subportadoras
    csi_std_amplitude: float      # Desvio padrão das amplitudes
    raw_rssi: float               # RSSI bruto original
    timestamp: float              # Timestamp da amostra


class SignalProcessor:
    """Processa sinais brutos e extrai features para detecção."""

    def __init__(
        self,
        window_size: int = 50,
        smoothing_window: int = 5,
        rssi_min: float = -100.0,
        rssi_max: float = -20.0,
    ) -> None:
        self._window_size = window_size
        self._smoothing_window = smoothing_window
        self._rssi_min = rssi_min
        self._rssi_max = rssi_max

        # Buffers de janela temporal
        self._rssi_buffer: deque[float] = deque(maxlen=window_size)
        self._energy_buffer: deque[float] = deque(maxlen=window_size)
        self._csi_buffer: deque[list[float]] = deque(maxlen=window_size)
        self._last_rssi: Optional[float] = None

    def reset(self) -> None:
        """Limpa buffers internos."""
        self._rssi_buffer.clear()
        self._energy_buffer.clear()
        self._csi_buffer.clear()
        self._last_rssi = None

    def process(self, signal: SignalData) -> ProcessedFeatures:
        """Processa um sinal bruto e retorna features extraídas."""
        rssi = signal.rssi
        csi = signal.csi_amplitude

        # Adiciona aos buffers
        self._rssi_buffer.append(rssi)
        self._csi_buffer.append(csi)

        # Normalização min-max do RSSI
        rssi_norm = self._normalize(rssi, self._rssi_min, self._rssi_max)

        # Suavização com média móvel
        rssi_smoothed = self._smooth(list(self._rssi_buffer), self._smoothing_window)

        # Energia do sinal CSI
        energy = self._compute_energy(csi)
        self._energy_buffer.append(energy)

        # Variância do CSI na janela
        variance = self._compute_variance(csi)

        # Taxa de variação do RSSI
        rate = self._rate_of_change(rssi)
        self._last_rssi = rssi

        # Score de instabilidade
        instability = self._instability_score()

        # Estatísticas CSI
        csi_mean = sum(csi) / len(csi) if csi else 0.0
        csi_std = self._std(csi)

        return ProcessedFeatures(
            rssi_normalized=rssi_norm,
            rssi_smoothed=rssi_smoothed,
            signal_energy=energy,
            signal_variance=variance,
            rate_of_change=rate,
            instability_score=instability,
            csi_mean_amplitude=csi_mean,
            csi_std_amplitude=csi_std,
            raw_rssi=rssi,
            timestamp=signal.timestamp,
        )

    # --- Helpers ---

    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Normaliza um valor para o intervalo [0, 1]."""
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    @staticmethod
    def _smooth(values: list[float], window: int) -> float:
        """Média móvel simples dos últimos `window` valores."""
        if not values:
            return 0.0
        recent = values[-window:]
        return sum(recent) / len(recent)

    @staticmethod
    def _compute_energy(csi: list[float]) -> float:
        """Energia do sinal = soma dos quadrados das amplitudes."""
        if not csi:
            return 0.0
        return sum(x * x for x in csi) / len(csi)

    @staticmethod
    def _compute_variance(csi: list[float]) -> float:
        """Variância das amplitudes CSI."""
        if len(csi) < 2:
            return 0.0
        mean = sum(csi) / len(csi)
        return sum((x - mean) ** 2 for x in csi) / len(csi)

    @staticmethod
    def _std(values: list[float]) -> float:
        """Desvio padrão."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(var)

    def _rate_of_change(self, current_rssi: float) -> float:
        """Diferença absoluta entre amostras consecutivas de RSSI."""
        if self._last_rssi is None:
            return 0.0
        return abs(current_rssi - self._last_rssi)

    def _instability_score(self) -> float:
        """
        Score de instabilidade [0, 1] baseado na variância da energia
        na janela temporal. Valores altos indicam ambiente instável.
        """
        if len(self._energy_buffer) < 3:
            return 0.0
        energies = list(self._energy_buffer)
        mean_e = sum(energies) / len(energies)
        if mean_e == 0:
            return 0.0
        var_e = sum((e - mean_e) ** 2 for e in energies) / len(energies)
        # Normaliza — sqrt(var)/mean, clamped a [0, 1]
        cv = math.sqrt(var_e) / mean_e
        return min(1.0, cv)
