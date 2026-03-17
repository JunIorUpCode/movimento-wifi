# -*- coding: utf-8 -*-
"""
License Model - Modelo de licença para gerenciamento
Armazena informações de licenças no license_schema
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from shared.database import Base


class PlanType(str, enum.Enum):
    """Tipos de plano disponíveis"""
    BASIC = "basic"
    PREMIUM = "premium"


class LicenseStatus(str, enum.Enum):
    """Status possíveis de uma licença"""
    PENDING = "pending"  # Licença criada mas não ativada
    ACTIVATED = "activated"  # Licença ativada e em uso
    REVOKED = "revoked"  # Licença revogada pelo admin
    EXPIRED = "expired"  # Licença expirada


class License(Base):
    """
    Modelo de licença para gerenciamento de ativações
    Armazena chaves de ativação e controla limites de dispositivos
    
    Requisitos: 4.3, 37.3
    """
    __tablename__ = "licenses"
    __table_args__ = {"schema": "license_schema"}
    
    # Identificador único da licença
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant proprietário da licença
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Chave de ativação (formato: XXXX-XXXX-XXXX-XXXX)
    # Armazenamos o hash SHA256 para segurança
    activation_key_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Chave de ativação em texto claro (apenas para exibição ao admin)
    # NOTA: Em produção, considere não armazenar isso e apenas mostrar uma vez
    activation_key = Column(String(19), unique=True, nullable=False, index=True)
    
    # Tipo de plano da licença
    plan_type = Column(SQLEnum(PlanType), nullable=False, default=PlanType.BASIC)
    
    # Limite de dispositivos que podem usar esta licença
    device_limit = Column(Integer, nullable=False, default=1)
    
    # Data de expiração da licença
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Data de ativação (quando o primeiro dispositivo usou a licença)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    
    # ID do dispositivo que ativou esta licença (se ativada)
    device_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Status da licença
    status = Column(SQLEnum(LicenseStatus), nullable=False, default=LicenseStatus.PENDING, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<License(id={self.id}, tenant_id={self.tenant_id}, plan={self.plan_type}, status={self.status})>"
    
    def to_dict(self, include_key: bool = False):
        """
        Converte licença para dicionário
        
        Args:
            include_key: Se True, inclui a chave de ativação (apenas para admin)
        """
        result = {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "plan_type": self.plan_type.value,
            "device_limit": self.device_limit,
            "expires_at": self.expires_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "device_id": str(self.device_id) if self.device_id else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        # Inclui chave de ativação apenas se solicitado (admin)
        if include_key:
            result["activation_key"] = self.activation_key
        
        return result
