# -*- coding: utf-8 -*-
"""
Detector de Hardware
Detecta automaticamente capacidades do hardware (CSI, adaptador Wi-Fi, OS)
"""

import platform
import subprocess
import sys
from typing import Dict, Any


class HardwareDetector:
    """
    Detector de hardware do dispositivo.
    Identifica sistema operacional, adaptador Wi-Fi e capacidades CSI.
    """
    
    @staticmethod
    def detect_hardware() -> Dict[str, Any]:
        """
        Detecta informações do hardware.
        
        Returns:
            Dict com informações do hardware:
                - type: 'raspberry_pi', 'windows', 'linux'
                - os: Nome e versão do sistema operacional
                - csi_capable: True se hardware suporta CSI
                - wifi_adapter: Nome do adaptador Wi-Fi
                - architecture: Arquitetura do processador
        """
        hardware_info = {
            'type': HardwareDetector._detect_device_type(),
            'os': HardwareDetector._detect_os(),
            'csi_capable': HardwareDetector._detect_csi_capability(),
            'wifi_adapter': HardwareDetector._detect_wifi_adapter(),
            'architecture': platform.machine()
        }
        
        return hardware_info
    
    @staticmethod
    def _detect_device_type() -> str:
        """
        Detecta o tipo de dispositivo.
        
        Returns:
            str: 'raspberry_pi', 'windows' ou 'linux'
        """
        system = platform.system().lower()
        
        if system == 'windows':
            return 'windows'
        
        elif system == 'linux':
            # Verifica se é Raspberry Pi
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    if 'raspberry' in cpuinfo or 'bcm' in cpuinfo:
                        return 'raspberry_pi'
            except FileNotFoundError:
                pass
            
            return 'linux'
        
        elif system == 'darwin':
            return 'macos'
        
        else:
            return 'unknown'
    
    @staticmethod
    def _detect_os() -> str:
        """
        Detecta sistema operacional e versão.
        
        Returns:
            str: Nome e versão do OS (ex: "Windows 10", "Ubuntu 22.04")
        """
        system = platform.system()
        release = platform.release()
        version = platform.version()
        
        if system == 'Windows':
            return f"Windows {release}"
        
        elif system == 'Linux':
            try:
                # Tenta ler /etc/os-release
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('PRETTY_NAME='):
                            return line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                pass
            
            return f"Linux {release}"
        
        elif system == 'Darwin':
            return f"macOS {release}"
        
        else:
            return f"{system} {release}"
    
    @staticmethod
    def _detect_csi_capability() -> bool:
        """
        Detecta se o hardware suporta CSI (Channel State Information).
        
        Returns:
            bool: True se suporta CSI
        
        Note:
            CSI requer hardware específico:
            - Intel 5300 NIC
            - Atheros AR9xxx
            - ESP32-S3 com firmware CSI
            - Nexmon CSI (Raspberry Pi com firmware modificado)
        """
        # Por enquanto, retorna False
        # TODO: Implementar detecção real de hardware CSI
        # Isso requer verificar drivers e firmware específicos
        
        system = platform.system().lower()
        
        if system == 'linux':
            # Verifica se tem drivers CSI instalados
            try:
                result = subprocess.run(
                    ['lsmod'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                # Procura por drivers CSI conhecidos
                if 'iwl5300' in result.stdout or 'ath9k' in result.stdout:
                    return True
            
            except Exception:
                pass
        
        return False
    
    @staticmethod
    def _detect_wifi_adapter() -> str:
        """
        Detecta o adaptador Wi-Fi disponível.
        
        Returns:
            str: Nome do adaptador Wi-Fi ou "unknown"
        """
        system = platform.system().lower()
        
        if system == 'windows':
            try:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=2
                )
                
                # Extrai nome da interface
                for line in result.stdout.split('\n'):
                    if 'Nome' in line or 'Name' in line:
                        return line.split(':')[-1].strip()
            
            except Exception:
                pass
            
            return "Wi-Fi"
        
        elif system == 'linux':
            try:
                # Lista interfaces de rede
                result = subprocess.run(
                    ['ls', '/sys/class/net'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                interfaces = result.stdout.strip().split('\n')
                
                # Procura por interfaces Wi-Fi (wlan*, wlp*)
                for iface in interfaces:
                    if iface.startswith('wlan') or iface.startswith('wlp'):
                        return iface
            
            except Exception:
                pass
            
            return "wlan0"
        
        else:
            return "unknown"
    
    @staticmethod
    def print_hardware_info() -> None:
        """Imprime informações do hardware detectado"""
        info = HardwareDetector.detect_hardware()
        
        print("\n" + "="*50)
        print("INFORMAÇÕES DO HARDWARE")
        print("="*50)
        print(f"Tipo de Dispositivo: {info['type']}")
        print(f"Sistema Operacional: {info['os']}")
        print(f"Arquitetura: {info['architecture']}")
        print(f"Adaptador Wi-Fi: {info['wifi_adapter']}")
        print(f"Suporte CSI: {'Sim' if info['csi_capable'] else 'Não'}")
        print("="*50 + "\n")
