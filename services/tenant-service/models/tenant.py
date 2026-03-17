# -*- coding: utf-8 -*-
"""
Tenant Model - Modelo de tenant para gerenciamento
Armazena informações completas de tenants no tenant_schema
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from shared.database import Base


class PlanType(str, enum.Enum):
    """Tipos de plano disponíveis"""
    BASIC = "basic"
    PREMIUM = "premium"


class TenantStatus(str, enum.Enum):
    """Status possíveis de um tenant"""
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class Tenant(Base):
    """
    Modelo de tenant para gerenciamento completo
    Armazena todas as informações do tenant incluindo configurações e metadados
    
    Requisitos: 2.1, 37.2
    """
    __tablename__ = "tenants"
    __table_args__ = {"schema": "tenant_schema"}
    
    # Identificador único do tenant
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Informações básicas
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Plano e status
    plan_type = Column(SQLEnum(PlanType), nullable=False, default=PlanType.BASIC)
    status = Column(SQLEnum(TenantStatus), nullable=False, default=TenantStatus.TRIAL, index=True)
    
    # Período de trial
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Idioma preferido
    language = Column(String(10), nullable=False, default="pt-BR")
    
    # Metadados adicionais (JSON)
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, email={self.email}, plan={self.plan_type}, status={self.status})>"
    
    def to_dict(self):
        """Converte tenant para dicionário"""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "plan_type": self.plan_type.value,
            "status": self.status.value,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "language": self.language,
            "metadata": self.extra_metadata
        }
