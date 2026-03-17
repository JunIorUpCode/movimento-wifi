"""
RssiLinuxProvider — Captura RSSI real usando iwconfig/iw no Linux.

Este provider funciona em sistemas Linux (incluindo Raspberry Pi)
e captura sinais Wi-Fi reais usando ferramentas nativas.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import time
from typing import Optional

from app.capture.base import SignalData, SignalProvider


class RssiLinuxProvider(SignalProvider):
    """
    Captura RSSI de redes Wi-Fi no Linux usando iwconfig ou iw.
    
    IMPORTANTE:
    - Funciona com qualquer adaptador Wi-Fi no Linux
    - Não requer modo monitor
    - Usa iwconfig (deprecated mas amplamente disponível) ou iw (moderno)
    - Ideal para Raspberry Pi
    """

    def __init__(self, interface: Optional[str] = None):
        """
        Args:
            interface: Nome da interface Wi-Fi (ex: wlan0). Se None, detecta automaticamente.
        """
        self.interface = interface
        self._running = False
        self._last_rssi = -70.0
        self._use_iw = False  # True se usar 'iw', False se usar 'iwconfig'

    async def start(self) -> None:
        """Inicia o provider e detecta interface Wi-Fi."""
        self._running = True
        
        # Detecta interface Wi-Fi se não especificada
        if not self.interface:
            self.interface = await self._detect_wifi_interface()
        
        # Verifica qual comando usar (iw é mais moderno, iwconfig é legacy)
        self._use_iw = await self._check_iw_available()
        
        cmd_type = "iw" if self._use_iw else "iwconfig"
        print(f"[RssiLinuxProvider] Interface: {self.interface}, Comando: {cmd_type}")

    async def stop(self) -> None:
        """Para o provider."""
        self._running = False

    def is_available(self) -> bool:
        """Verifica se o provider está disponível no sistema."""
        try:
            # Tenta executar iwconfig ou iw
            result = subprocess.run(
                ['which', 'iwconfig'],
                capture_output=True,
                timeout=1
            )
            if result.returncode == 0:
                return True
            
            result = subprocess.run(
                ['which', 'iw'],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except Exception:
            return False

    async def get_signal(self) -> SignalData:
        """
        Captura RSSI atual da interface Wi-Fi.
        
        Usa iwconfig ou iw dependendo da disponibilidade.
        """
        try:
            if self._use_iw:
                rssi = await self._get_signal_iw()
            else:
                rssi = await self._get_signal_iwconfig()
            
            if rssi is not None:
                self._last_rssi = rssi
        
        except Exception as e:
            print(f"[RssiLinuxProvider] Erro ao capturar sinal: {e}")
        
        return SignalData(
            rssi=self._last_rssi,
            csi_amplitude=[],  # RSSI não tem CSI
            timestamp=time.time(),
            provider="rssi_linux",
            metadata={
                "interface": self.interface,
                "method": "iw" if self._use_iw else "iwconfig"
            }
        )

    async def _detect_wifi_interface(self) -> str:
        """Detecta automaticamente a interface Wi-Fi ativa."""
        try:
            # Lista interfaces de rede
            result = await asyncio.to_thread(
                subprocess.run,
                ['ls', '/sys/class/net'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            interfaces = result.stdout.strip().split('\n')
            
            # Procura por wlan0, wlan1, wlp*, etc
            for iface in interfaces:
                if iface.startswith('wlan') or iface.startswith('wlp'):
                    return iface
            
            # Fallback para wlan0
            return 'wlan0'
        
        except Exception as e:
            print(f"[RssiLinuxProvider] Erro ao detectar interface: {e}")
            return 'wlan0'

    async def _check_iw_available(self) -> bool:
        """Verifica se o comando 'iw' está disponível."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['which', 'iw'],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _get_signal_iwconfig(self) -> Optional[float]:
        """
        Captura RSSI usando iwconfig (legacy).
        
        Exemplo de output:
        wlan0     IEEE 802.11  ESSID:"MinhaRede"
                  Mode:Managed  Frequency:2.437 GHz  Access Point: AA:BB:CC:DD:EE:FF
                  Link Quality=70/70  Signal level=-40 dBm
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['iwconfig', self.interface],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Procura por "Signal level=-XX dBm"
            match = re.search(r'Signal level[=:](-?\d+)\s*dBm', result.stdout)
            if match:
                return float(match.group(1))
            
            return None
        
        except Exception as e:
            print(f"[RssiLinuxProvider] Erro no iwconfig: {e}")
            return None

    async def _get_signal_iw(self) -> Optional[float]:
        """
        Captura RSSI usando iw (moderno).
        
        Exemplo de output:
        Connected to aa:bb:cc:dd:ee:ff (on wlan0)
            SSID: MinhaRede
            freq: 2437
            signal: -40 dBm
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['iw', 'dev', self.interface, 'link'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Procura por "signal: -XX dBm"
            match = re.search(r'signal:\s*(-?\d+)\s*dBm', result.stdout)
            if match:
                return float(match.group(1))
            
            return None
        
        except Exception as e:
            print(f"[RssiLinuxProvider] Erro no iw: {e}")
            return None


# Alias para compatibilidade
LinuxRssiProvider = RssiLinuxProvider
