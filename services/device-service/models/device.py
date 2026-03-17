# -*- coding: utf-8 -*-
"""
Device Model - Modelo de dispositivo para gerenciamento
Armazena informações de dispositivos no device_schema
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from shared.database import Base


class HardwareType(str, enum.Enum):
    """Tipos de hardware disponíveis"""
    RASPBERRY_PI = "raspberry_pi"
    WINDOWS = "windows"
    LINUX = "linux"


class DeviceStatus(str, enum.Enum):
    """Status possíveis de um dispositivo"""
    ONLINE = "online"  # Dispositivo ativo e enviando heartbeat
    OFFLINE = "offline"  # Dispositivo não envia heartbeat há mais de 3 minutos
    ERROR = "error"  # Dispositivo com erro de configuração ou hardware


class Device(Base):
    """
    Modelo de dispositivo para gerenciamento de hardware
    Armazena informações de dispositivos registrados e seu status
    
    Requisitos: 3.4, 37.2
    """
    __tablename__ = "devices"
    __table_args__ = {"schema": "device_schema"}
    
    # Identificador único do dispositivo
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant proprietário do dispositivo
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Nome amigável do dispositivo (ex: "Sala de Estar", "Quarto")
    name = Column(String(100), nullable=False)
    
    # Tipo de hardware do dispositivo
    hardware_type = Column(SQLEnum(HardwareType), nullable=False)
    
    # Status atual do dispositivo
    status = Column(SQLEnum(DeviceStatus), nullable=False, default=DeviceStatus.ONLINE, index=True)
    
    # Última vez que o dispositivo enviou heartbeat
    last_seen = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Data de registro do dispositivo
    registered_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Informações detalhadas do hardware (JSON)
    # Exemplo: {"csi_capable": true, "wifi_adapter": "Intel 5300", "os": "Linux", "cpu": "ARM Cortex-A72"}
    hardware_info = Column(JSON, nullable=False, default=dict)
    
    # Configuração do dispositivo (JSON)
    # Exemplo: {"sampling_interval": 1, "detection_thresholds": {...}}
    config = Column(JSON, nullable=False, default=dict)
    
    # Hash do JWT token do dispositivo (para validação)
    jwt_token_hash = Column(String(64), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, tenant_id={self.tenant_id}, status={self.status})>"
    
    def to_dict(self):
        """Converte dispositivo para dicionário"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "hardware_type": self.hardware_type.value,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
            "registered_at": self.registered_at.isoformat(),
            "hardware_info": self.hardware_info,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
