# -*- coding: utf-8 -*-
"""
Event Model - Modelo de Evento
Define a estrutura de eventos detectados no sistema
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from shared.database import Base


class Event(Base):
    """
    Modelo de Evento detectado pelo sistema.
    
    Representa um evento de presença, movimento, queda ou inatividade
    detectado a partir de sinais Wi-Fi processados.
    
    Attributes:
        id: ID único do evento (UUID)
        tenant_id: ID do tenant proprietário (isolamento multi-tenant)
        device_id: ID do dispositivo que detectou o evento
        event_type: Tipo do evento (presence, movement, fall_suspected, prolonged_inactivity)
        confidence: Nível de confiança da detecção (0.0 a 1.0)
        timestamp: Momento em que o evento foi detectado
        metadata: Dados adicionais do evento (JSON)
        is_false_positive: Flag indicando se foi marcado como falso positivo
        user_notes: Notas do usuário sobre o evento
        created_at: Timestamp de criação do registro
    """
    
    __tablename__ = "events"
    __table_args__ = (
        # Índices para queries eficientes
        Index("idx_events_tenant_id", "tenant_id"),
        Index("idx_events_device_id", "device_id"),
        Index("idx_events_timestamp", "timestamp"),
        Index("idx_events_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_events_tenant_type_time", "tenant_id", "event_type", "timestamp"),
        {"schema": "event_schema"}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # presence, movement, fall_suspected, prolonged_inactivity
    confidence = Column(Float, nullable=False)  # 0.0 a 1.0
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_metadata = Column(JSON, nullable=True)  # Dados adicionais do evento (renomeado de metadata)
    is_false_positive = Column(Boolean, default=False)
    user_notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, confidence={self.confidence})>"
