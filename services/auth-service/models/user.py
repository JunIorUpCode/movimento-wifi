# -*- coding: utf-8 -*-
"""
User Model - Modelo de usuário para autenticação
Armazena informações de tenants no auth_schema
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
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


class User(Base):
    """
    Modelo de usuário/tenant para autenticação
    Armazena credenciais e informações básicas do tenant
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth_schema"}
    
    # Identificador único do tenant
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Credenciais de autenticação
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Informações do tenant
    name = Column(String(255), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False, default=PlanType.BASIC)
    status = Column(SQLEnum(TenantStatus), nullable=False, default=TenantStatus.TRIAL)
    
    # Timestamps
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, plan={self.plan_type}, status={self.status})>"
