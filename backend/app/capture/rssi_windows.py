"""
RssiWindowsProvider — Captura RSSI real usando netsh no Windows.

Este provider usa o comando nativo do Windows para ler sinais Wi-Fi reais.
Não requer hardware especial, funciona com qualquer adaptador Wi-Fi.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import time
from typing import Optional

from app.capture.base import SignalData, SignalProvider


class RssiWindowsProvider(SignalProvider):
    """
    Captura RSSI de redes Wi-Fi visíveis no Windows usando netsh.
    
    IMPORTANTE:
    - Funciona com qualquer adaptador Wi-Fi no Windows
    - Não requer modo monitor
    - Captura sinais de todas as redes visíveis
    - Usa a rede conectada ou a mais forte como referência
    """

    def __init__(self, target_ssid: Optional[str] = None):
        """
        Args:
            target_ssid: SSID da rede para monitorar. Se None, usa a rede conectada.
        """
        self.target_ssid = target_ssid
        self._running = False
        self._last_rssi = -70.0
        self._interface_name: Optional[str] = None

    async def start(self) -> None:
        """Inicia o provider e detecta interface Wi-Fi."""
        self._running = True
        
        # Detecta interface Wi-Fi ativa
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Extrai nome da interface
            for line in result.stdout.split('\n'):
                if 'Nome' in line or 'Name' in line:
                    self._interface_name = line.split(':')[-1].strip()
                    break
            
            print(f"[RssiWindowsProvider] Interface detectada: {self._interface_name}")
            
            # Se não especificou SSID, usa a rede conectada
            if not self.target_ssid:
                for line in result.stdout.split('\n'):
                    if 'SSID' in line and 'BSSID' not in line:
                        self.target_ssid = line.split(':')[-1].strip()
                        break
                
                print(f"[RssiWindowsProvider] Monitorando rede: {self.target_ssid}")
        
        except Exception as e:
            print(f"[RssiWindowsProvider] Erro ao detectar interface: {e}")

    async def stop(self) -> None:
        """Para o provider."""
        self._running = False

    def is_available(self) -> bool:
        """Verifica se o provider está disponível (sempre True no Windows)."""
        return True

    async def get_signal(self) -> SignalData:
        """
        Captura RSSI atual da rede Wi-Fi.
        
        Usa o comando: netsh wlan show networks mode=bssid
        """
        try:
            # Executa comando netsh para listar redes
            result = await asyncio.to_thread(
                subprocess.run,
                ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=2
            )
            
            # Parse do output
            rssi = self._parse_netsh_output(result.stdout)
            
            if rssi is not None:
                self._last_rssi = rssi
            
        except subprocess.TimeoutExpired:
            print("[RssiWindowsProvider] Timeout ao executar netsh")
        except Exception as e:
            print(f"[RssiWindowsProvider] Erro ao capturar sinal: {e}")
        
        # Retorna dados
        return SignalData(
            rssi=self._last_rssi,
            csi_amplitude=[],  # RSSI não tem CSI
            timestamp=time.time(),
            provider="rssi_windows",
            metadata={
                "interface": self._interface_name,
                "target_ssid": self.target_ssid,
                "method": "netsh"
            }
        )

    def _parse_netsh_output(self, output: str) -> Optional[float]:
        """
        Faz parse do output do netsh para extrair RSSI.
        
        Formato do output:
        SSID 1 : MinhaRede
            Network type            : Infrastructure
            Authentication          : WPA2-Personal
            Encryption              : CCMP
            BSSID 1                 : aa:bb:cc:dd:ee:ff
                 Signal             : 85%
                 Radio type         : 802.11n
                 Channel            : 6
        """
        lines = output.split('\n')
        current_ssid = None
        
        for i, line in enumerate(lines):
            # Detecta SSID
            if line.strip().startswith('SSID'):
                parts = line.split(':')
                if len(parts) >= 2:
                    current_ssid = parts[-1].strip()
            
            # Se encontrou a rede alvo, procura o sinal
            if current_ssid == self.target_ssid or (not self.target_ssid and current_ssid):
                # Procura linha de Signal nas próximas 10 linhas
                for j in range(i, min(i + 10, len(lines))):
                    if 'Signal' in lines[j] or 'Sinal' in lines[j]:
                        # Extrai porcentagem: "Signal : 85%"
                        match = re.search(r'(\d+)%', lines[j])
                        if match:
                            percentage = int(match.group(1))
                            # Converte porcentagem para dBm (aproximação)
                            # 100% ≈ -30 dBm, 0% ≈ -100 dBm
                            rssi = -100 + (percentage * 0.7)
                            return rssi
        
        return None


# Alias para compatibilidade
WindowsRssiProvider = RssiWindowsProvider
