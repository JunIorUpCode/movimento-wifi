# -*- coding: utf-8 -*-
"""
Audit Log Model - Modelo para logs de auditoria
Registra todas tentativas de autenticação e ações administrativas
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from shared.database import Base


class AuditLog(Base):
    """
    Modelo de log de auditoria
    Registra ações de autenticação para compliance e troubleshooting
    """
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "auth_schema"}
    
    # Identificador único do log
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificadores de contexto
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    admin_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Informações da ação
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Estados antes/depois (para mudanças)
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    
    # Informações de rede
    ip_address = Column(String(45), nullable=True)  # Suporta IPv6
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, timestamp={self.timestamp})>"
