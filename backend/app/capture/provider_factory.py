"""
ProviderFactory — Auto-detecção inteligente de providers de captura.

Este módulo detecta automaticamente qual hardware/sistema está disponível
e retorna o melhor provider possível, seguindo esta ordem de prioridade:

1. CSI (melhor qualidade, requer hardware específico)
2. RSSI Windows (Windows com qualquer placa Wi-Fi)
3. RSSI Linux (Linux/Raspberry Pi com qualquer placa Wi-Fi)
4. Mock (fallback para testes/desenvolvimento)
"""

from __future__ import annotations

import platform
import sys
from typing import Optional

from app.capture.base import SignalProvider
from app.capture.csi_placeholder import CsiProviderPlaceholder
from app.capture.mock_provider import MockSignalProvider
from app.capture.rssi_linux import RssiLinuxProvider
from app.capture.rssi_windows import RssiWindowsProvider


class ProviderFactory:
    """
    Factory para criar o provider de captura mais adequado.
    
    Detecta automaticamente o sistema operacional e hardware disponível,
    retornando o melhor provider possível.
    """

    @staticmethod
    def create_provider(
        force_provider: Optional[str] = None,
        force_mock: bool = False
    ) -> SignalProvider:
        """
        Cria e retorna o provider de captura mais adequado.
        
        Args:
            force_provider: Força um provider específico ('csi', 'rssi_windows', 
                          'rssi_linux', 'mock'). Se None, detecta automaticamente.
            force_mock: Se True, força o uso do MockProvider (útil para testes).
        
        Returns:
            SignalProvider: O provider mais adequado para o sistema atual.
        
        Exemplos:
            >>> # Auto-detecção (recomendado para produção)
            >>> provider = ProviderFactory.create_provider()
            
            >>> # Forçar mock para testes
            >>> provider = ProviderFactory.create_provider(force_mock=True)
            
            >>> # Forçar provider específico
            >>> provider = ProviderFactory.create_provider(force_provider='rssi_windows')
        """
        
        # Modo de teste/desenvolvimento
        if force_mock:
            print("[ProviderFactory] Modo MOCK forçado")
            return MockSignalProvider()
        
        # Provider específico forçado
        if force_provider:
            return ProviderFactory._create_forced_provider(force_provider)
        
        # Auto-detecção inteligente
        return ProviderFactory._auto_detect_provider()

    @staticmethod
    def _create_forced_provider(provider_type: str) -> SignalProvider:
        """Cria um provider específico forçado pelo usuário."""
        provider_type = provider_type.lower()
        
        if provider_type == 'csi':
            print("[ProviderFactory] Provider CSI forçado")
            return CsiProviderPlaceholder()
        
        elif provider_type == 'rssi_windows':
            print("[ProviderFactory] Provider RSSI Windows forçado")
            return RssiWindowsProvider()
        
        elif provider_type == 'rssi_linux':
            print("[ProviderFactory] Provider RSSI Linux forçado")
            return RssiLinuxProvider()
        
        elif provider_type == 'mock':
            print("[ProviderFactory] Provider Mock forçado")
            return MockSignalProvider()
        
        else:
            print(f"[ProviderFactory] Provider '{provider_type}' desconhecido, usando auto-detecção")
            return ProviderFactory._auto_detect_provider()

    @staticmethod
    def _auto_detect_provider() -> SignalProvider:
        """
        Detecta automaticamente o melhor provider disponível.
        
        Ordem de prioridade:
        1. CSI (melhor qualidade)
        2. RSSI específico do OS (Windows ou Linux)
        3. Mock (fallback)
        """
        
        print("[ProviderFactory] Iniciando auto-detecção de provider...")
        
        # 1. Tenta CSI primeiro (melhor qualidade)
        csi_provider = CsiProviderPlaceholder()
        if csi_provider.is_available():
            print("[ProviderFactory] ✓ CSI Provider detectado (melhor qualidade)")
            return csi_provider
        
        # 2. Detecta sistema operacional
        system = platform.system().lower()
        print(f"[ProviderFactory] Sistema operacional: {system}")
        
        # 3. Windows: usa RSSI Windows
        if system == 'windows':
            rssi_provider = RssiWindowsProvider()
            if rssi_provider.is_available():
                print("[ProviderFactory] ✓ RSSI Windows Provider detectado")
                return rssi_provider
        
        # 4. Linux: usa RSSI Linux (inclui Raspberry Pi)
        elif system == 'linux':
            rssi_provider = RssiLinuxProvider()
            if rssi_provider.is_available():
                print("[ProviderFactory] ✓ RSSI Linux Provider detectado")
                return rssi_provider
        
        # 5. Fallback: Mock Provider
        print("[ProviderFactory] ⚠ Nenhum hardware real detectado, usando Mock Provider")
        print("[ProviderFactory] Para captura real, instale:")
        print("  - Windows: Nenhuma instalação necessária")
        print("  - Linux: sudo apt-get install wireless-tools iw")
        print("  - CSI: Hardware específico (Intel 5300, ESP32-S3, etc)")
        
        return MockSignalProvider()

    @staticmethod
    def get_available_providers() -> dict[str, bool]:
        """
        Retorna um dicionário com todos os providers e sua disponibilidade.
        
        Útil para diagnóstico e interface administrativa.
        
        Returns:
            dict: {'provider_name': is_available}
        
        Exemplo:
            >>> ProviderFactory.get_available_providers()
            {
                'csi': False,
                'rssi_windows': True,
                'rssi_linux': False,
                'mock': True
            }
        """
        return {
            'csi': CsiProviderPlaceholder().is_available(),
            'rssi_windows': RssiWindowsProvider().is_available(),
            'rssi_linux': RssiLinuxProvider().is_available(),
            'mock': True  # Mock sempre disponível
        }

    @staticmethod
    def get_provider_info() -> dict[str, str]:
        """
        Retorna informações sobre o provider atual e sistema.
        
        Útil para logs, diagnóstico e suporte ao cliente.
        
        Returns:
            dict: Informações do sistema e provider detectado
        """
        system = platform.system()
        available = ProviderFactory.get_available_providers()
        
        # Detecta qual seria usado
        if available['csi']:
            detected = 'CSI (melhor qualidade)'
        elif system == 'Windows' and available['rssi_windows']:
            detected = 'RSSI Windows'
        elif system == 'Linux' and available['rssi_linux']:
            detected = 'RSSI Linux'
        else:
            detected = 'Mock (nenhum hardware detectado)'
        
        return {
            'system': system,
            'python_version': sys.version,
            'detected_provider': detected,
            'available_providers': str(available),
            'recommendation': ProviderFactory._get_recommendation(system, available)
        }

    @staticmethod
    def _get_recommendation(system: str, available: dict[str, bool]) -> str:
        """Retorna recomendação de configuração baseada no sistema."""
        if available['csi']:
            return "Sistema configurado com CSI - melhor qualidade possível"
        
        if system == 'Windows' and available['rssi_windows']:
            return "Sistema Windows OK - usando RSSI nativo"
        
        if system == 'Linux' and available['rssi_linux']:
            return "Sistema Linux OK - usando RSSI nativo"
        
        if system == 'Linux' and not available['rssi_linux']:
            return "Instale: sudo apt-get install wireless-tools iw"
        
        return "Nenhum hardware detectado - usando modo simulação"


# Função de conveniência para uso direto
def create_auto_provider() -> SignalProvider:
    """
    Atalho para criar provider com auto-detecção.
    
    Uso:
        from app.capture.provider_factory import create_auto_provider
        provider = create_auto_provider()
    """
    return ProviderFactory.create_provider()
