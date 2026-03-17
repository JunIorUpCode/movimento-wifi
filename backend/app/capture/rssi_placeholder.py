"""
RssiProviderPlaceholder — Placeholder para futuro provider RSSI real.

Este módulo será substituído por integração com hardware real
(ex: adaptador Wi-Fi em modo monitor, ESP32, etc).
"""

from __future__ import annotations

from app.capture.base import SignalData, SignalProvider


class RssiProviderPlaceholder(SignalProvider):
    """Placeholder para captura real de RSSI."""

    async def get_signal(self) -> SignalData:
        raise NotImplementedError(
            "RssiProvider ainda não implementado. "
            "Conecte um adaptador Wi-Fi em modo monitor e implemente este provider."
        )

    async def start(self) -> None:
        raise NotImplementedError("RssiProvider: hardware não conectado.")

    async def stop(self) -> None:
        pass

    def is_available(self) -> bool:
        return False
