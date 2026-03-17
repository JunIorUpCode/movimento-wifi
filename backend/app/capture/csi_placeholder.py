"""
CsiProviderPlaceholder — Placeholder para futuro provider CSI real.

Este módulo será substituído por integração com hardware que
suporte Channel State Information (ex: Intel 5300, Atheros, ESP32-S3).
"""

from __future__ import annotations

from app.capture.base import SignalData, SignalProvider


class CsiProviderPlaceholder(SignalProvider):
    """Placeholder para captura real de CSI."""

    async def get_signal(self) -> SignalData:
        raise NotImplementedError(
            "CsiProvider ainda não implementado. "
            "Conecte hardware com suporte a CSI e implemente este provider."
        )

    async def start(self) -> None:
        raise NotImplementedError("CsiProvider: hardware não conectado.")

    async def stop(self) -> None:
        pass

    def is_available(self) -> bool:
        return False
