# -*- coding: utf-8 -*-
"""
Configuração do Agente Local
Gerencia configurações locais e remotas do agente
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet


@dataclass
class AgentConfig:
    """Configuração do agente local"""
    
    # Identificação do dispositivo
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    activation_key: Optional[str] = None
    
    # Credenciais (armazenadas criptografadas)
    jwt_token: Optional[str] = None
    
    # Configuração do backend
    backend_url: str = "https://api.wifisense.com"
    websocket_url: str = "wss://api.wifisense.com/ws"
    
    # Configuração de captura
    sampling_interval: int = 1  # segundos
    provider_type: Optional[str] = None  # 'auto', 'rssi_windows', 'rssi_linux', 'csi', 'mock'
    
    # Configuração de buffer offline
    buffer_max_size_mb: int = 100
    buffer_db_path: str = "agent_buffer.db"
    
    # Configuração de heartbeat
    heartbeat_interval: int = 60  # segundos
    
    # Configuração de detecção
    presence_threshold: float = 0.7
    movement_threshold: float = 0.8
    fall_threshold: float = 0.85
    
    # Configuração de retry
    retry_max_attempts: int = 3
    retry_backoff_base: float = 2.0  # exponential backoff
    retry_initial_delay: float = 1.0  # segundos


class ConfigManager:
    """
    Gerenciador de configuração do agente.
    Armazena configurações localmente de forma segura.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            config_dir: Diretório para armazenar configurações.
                       Se None, usa ~/.wifisense_agent/
        """
        if config_dir is None:
            config_dir = Path.home() / ".wifisense_agent"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "encryption.key"
        
        # Inicializa chave de criptografia
        self._init_encryption_key()
    
    def _init_encryption_key(self) -> None:
        """Inicializa ou carrega chave de criptografia para dados sensíveis"""
        if not self.key_file.exists():
            # Gera nova chave
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Protege o arquivo (apenas leitura pelo dono)
            os.chmod(self.key_file, 0o600)
        
        self._cipher = Fernet(self.key_file.read_bytes())
    
    def _encrypt(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        if not data:
            return ""
        return self._cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis"""
        if not encrypted_data:
            return ""
        return self._cipher.decrypt(encrypted_data.encode()).decode()
    
    def load_config(self) -> AgentConfig:
        """
        Carrega configuração do arquivo local.
        
        Returns:
            AgentConfig: Configuração carregada ou padrão se não existir
        """
        if not self.config_file.exists():
            return AgentConfig()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Descriptografa campos sensíveis
            if data.get('jwt_token'):
                data['jwt_token'] = self._decrypt(data['jwt_token'])
            if data.get('activation_key'):
                data['activation_key'] = self._decrypt(data['activation_key'])
            
            return AgentConfig(**data)
        
        except Exception as e:
            print(f"[ConfigManager] Erro ao carregar configuração: {e}")
            return AgentConfig()
    
    def save_config(self, config: AgentConfig) -> None:
        """
        Salva configuração no arquivo local.
        
        Args:
            config: Configuração a ser salva
        """
        try:
            data = asdict(config)
            
            # Criptografa campos sensíveis antes de salvar
            if data.get('jwt_token'):
                data['jwt_token'] = self._encrypt(data['jwt_token'])
            if data.get('activation_key'):
                data['activation_key'] = self._encrypt(data['activation_key'])
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Protege o arquivo (apenas leitura/escrita pelo dono)
            os.chmod(self.config_file, 0o600)
        
        except Exception as e:
            print(f"[ConfigManager] Erro ao salvar configuração: {e}")
            raise
    
    def update_config(self, **kwargs) -> AgentConfig:
        """
        Atualiza campos específicos da configuração.
        
        Args:
            **kwargs: Campos a serem atualizados
        
        Returns:
            AgentConfig: Configuração atualizada
        """
        config = self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config(config)
        return config
    
    def is_activated(self) -> bool:
        """
        Verifica se o agente já foi ativado.
        
        Returns:
            bool: True se device_id e jwt_token estão configurados
        """
        config = self.load_config()
        return bool(config.device_id and config.jwt_token)
    
    def clear_credentials(self) -> None:
        """Remove credenciais (útil para desativar dispositivo)"""
        config = self.load_config()
        config.device_id = None
        config.jwt_token = None
        self.save_config(config)
