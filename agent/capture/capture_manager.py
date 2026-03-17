# -*- coding: utf-8 -*-
"""
Gerenciador de Captura de Sinais
Coordena a captura de sinais Wi-Fi usando os providers do backend
"""

import asyncio
import sys
import os
from typing import Optional

# Adiciona o diretório backend ao path para importar os providers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.capture.base import SignalProvider, SignalData
from app.capture.provider_factory import ProviderFactory


class CaptureManager:
    """
    Gerenciador de captura de sinais Wi-Fi.
    Reutiliza os providers do backend para captura de RSSI/CSI.
    """
    
    def __init__(self, provider_type: Optional[str] = None):
        """
        Inicializa o gerenciador de captura.
        
        Args:
            provider_type: Tipo de provider ('auto', 'rssi_windows', 'rssi_linux', 'csi', 'mock')
                          Se None ou 'auto', detecta automaticamente
        """
        self.provider_type = provider_type or 'auto'
        self.provider: Optional[SignalProvider] = None
        self._running = False
    
    async def start(self) -> None:
        """
        Inicia o gerenciador de captura.
        Detecta e inicializa o provider apropriado.
        """
        print(f"[CaptureManager] Inicializando provider: {self.provider_type}")
        
        # Cria provider usando a factory do backend
        self.provider = ProviderFactory.create_provider(self.provider_type)
        
        if not self.provider:
            raise RuntimeError("Nenhum provider de captura disponível")
        
        # Inicia o provider
        await self.provider.start()
        self._running = True
        
        print(f"[CaptureManager] Provider iniciado: {type(self.provider).__name__}")
    
    async def stop(self) -> None:
        """Para o gerenciador de captura"""
        self._running = False
        
        if self.provider:
            await self.provider.stop()
            print("[CaptureManager] Provider parado")
    
    async def capture_signal(self) -> SignalData:
        """
        Captura um sinal Wi-Fi.
        
        Returns:
            SignalData: Dados do sinal capturado
        
        Raises:
            RuntimeError: Se o provider não foi iniciado
        """
        if not self.provider or not self._running:
            raise RuntimeError("CaptureManager não foi iniciado")
        
        return await self.provider.get_signal()
    
    def is_running(self) -> bool:
        """Verifica se o gerenciador está rodando"""
        return self._running
    
    def get_provider_name(self) -> str:
        """Retorna o nome do provider atual"""
        if self.provider:
            return type(self.provider).__name__
        return "None"
