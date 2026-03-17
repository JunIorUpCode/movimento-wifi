"""
Camada de captura — classes base.

Define a interface abstrata SignalProvider e o dataclass SignalData
que todos os providers de captura devem implementar.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SignalData:
    """Representa uma amostra de sinal capturada."""

    rssi: float  # dBm, tipicamente entre -100 e 0
    csi_amplitude: list[float]  # amplitudes CSI por subportadora
    timestamp: float = field(default_factory=time.time)
    provider: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


class SignalProvider(ABC):
    """Interface abstrata para providers de captura de sinal Wi-Fi."""

    @abstractmethod
    async def get_signal(self) -> SignalData:
        """Retorna uma amostra de sinal."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Inicializa o provider."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Encerra o provider."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Retorna True se o provider está pronto para uso."""
        ...
