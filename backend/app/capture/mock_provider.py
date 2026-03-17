"""
MockSignalProvider — Gerador de sinais sintéticos para simulação.

Suporta múltiplos modos de simulação que replicam cenários reais
de presença, movimento, queda e inatividade.
"""

from __future__ import annotations

import math
import random
import time
from enum import Enum

from app.capture.base import SignalData, SignalProvider


class SimulationMode(str, Enum):
    EMPTY = "empty"
    STILL = "still"
    MOVING = "moving"
    FALL = "fall"
    POST_FALL_INACTIVITY = "post_fall_inactivity"
    RANDOM = "random"


# Número de subportadoras CSI simuladas
NUM_SUBCARRIERS = 30


class MockSignalProvider(SignalProvider):
    """Gera dados sintéticos de Wi-Fi em tempo real."""

    def __init__(self) -> None:
        self._mode: SimulationMode = SimulationMode.EMPTY
        self._running: bool = False
        self._tick: int = 0
        self._fall_phase: int = 0  # controla fase da queda

    # --- Controle ---

    async def start(self) -> None:
        self._running = True
        self._tick = 0

    async def stop(self) -> None:
        self._running = False

    def is_available(self) -> bool:
        return True

    def set_mode(self, mode: SimulationMode) -> None:
        self._mode = mode
        self._tick = 0
        self._fall_phase = 0

    @property
    def mode(self) -> SimulationMode:
        return self._mode

    # --- Geração de sinal ---

    async def get_signal(self) -> SignalData:
        self._tick += 1
        t = self._tick

        effective_mode = self._mode
        if effective_mode == SimulationMode.RANDOM:
            effective_mode = random.choice([
                SimulationMode.EMPTY,
                SimulationMode.STILL,
                SimulationMode.MOVING,
                SimulationMode.FALL,
            ])

        rssi, csi = self._generate(effective_mode, t)

        return SignalData(
            rssi=rssi,
            csi_amplitude=csi,
            timestamp=time.time(),
            provider="mock",
            metadata={"mode": self._mode.value, "tick": t},
        )

    def _generate(self, mode: SimulationMode, t: int) -> tuple[list[float], list[float]]:
        """Retorna (rssi, csi_amplitudes) de acordo com o modo."""

        if mode == SimulationMode.EMPTY:
            return self._empty(t)
        elif mode == SimulationMode.STILL:
            return self._still(t)
        elif mode == SimulationMode.MOVING:
            return self._moving(t)
        elif mode == SimulationMode.FALL:
            return self._fall(t)
        elif mode == SimulationMode.POST_FALL_INACTIVITY:
            return self._post_fall(t)
        return self._empty(t)

    # --- Modos ---

    def _noise(self, scale: float = 1.0) -> float:
        return random.gauss(0, scale)

    def _empty(self, t: int) -> tuple[float, list[float]]:
        """Ambiente vazio — sinal estável com ruído mínimo."""
        rssi = -75.0 + self._noise(0.5)
        csi = [1.0 + self._noise(0.05) for _ in range(NUM_SUBCARRIERS)]
        return rssi, csi

    def _still(self, t: int) -> tuple[float, list[float]]:
        """Pessoa parada — pequenas variações periódicas (respiração)."""
        breath = 0.3 * math.sin(2 * math.pi * t / 40)  # ciclo ~40 amostras
        rssi = -55.0 + breath + self._noise(1.0)
        csi = [
            3.0 + 0.5 * math.sin(2 * math.pi * (t + i) / 40) + self._noise(0.15)
            for i in range(NUM_SUBCARRIERS)
        ]
        return rssi, csi

    def _moving(self, t: int) -> tuple[float, list[float]]:
        """Pessoa em movimento — variações amplas e rápidas."""
        walk = 8.0 * math.sin(2 * math.pi * t / 15)
        rssi = -45.0 + walk + self._noise(3.0)
        csi = [
            5.0
            + 3.0 * math.sin(2 * math.pi * (t + i * 3) / 12)
            + self._noise(0.8)
            for i in range(NUM_SUBCARRIERS)
        ]
        return rssi, csi

    def _fall(self, t: int) -> tuple[float, list[float]]:
        """Queda — pico brusco seguido de estabilização baixa."""
        self._fall_phase += 1
        phase = self._fall_phase

        if phase < 5:
            # Impacto
            rssi = -30.0 + self._noise(5.0)
            csi = [10.0 + self._noise(2.0) for _ in range(NUM_SUBCARRIERS)]
        elif phase < 15:
            # Transição rápida para imobilidade
            decay = max(0, 1.0 - (phase - 5) / 10.0)
            rssi = -30.0 + (-35.0 * (1 - decay)) + self._noise(1.0)
            csi = [10.0 * decay + 2.0 * (1 - decay) + self._noise(0.3) for _ in range(NUM_SUBCARRIERS)]
        else:
            # Imóvel pós-queda
            rssi = -60.0 + self._noise(0.8)
            csi = [2.0 + self._noise(0.1) for _ in range(NUM_SUBCARRIERS)]
        return rssi, csi

    def _post_fall(self, t: int) -> tuple[float, list[float]]:
        """Imobilidade prolongada pós-queda — sinal muito estável e baixo."""
        rssi = -62.0 + self._noise(0.4)
        csi = [1.8 + self._noise(0.08) for _ in range(NUM_SUBCARRIERS)]
        return rssi, csi
