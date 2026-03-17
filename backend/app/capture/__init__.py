"""
Módulo de captura de sinais Wi-Fi.

Exporta providers e factory para auto-detecção de hardware.
"""

from app.capture.base import SignalData, SignalProvider
from app.capture.csi_placeholder import CsiProviderPlaceholder
from app.capture.mock_provider import MockSignalProvider, SimulationMode
from app.capture.provider_factory import ProviderFactory, create_auto_provider
from app.capture.rssi_linux import RssiLinuxProvider
from app.capture.rssi_windows import RssiWindowsProvider

__all__ = [
    # Base
    "SignalData",
    "SignalProvider",
    # Providers
    "CsiProviderPlaceholder",
    "MockSignalProvider",
    "RssiLinuxProvider",
    "RssiWindowsProvider",
    # Factory
    "ProviderFactory",
    "create_auto_provider",
    # Enums
    "SimulationMode",
]
