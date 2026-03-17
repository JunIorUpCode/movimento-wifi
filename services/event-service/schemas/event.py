# -*- coding: utf-8 -*-
"""
Event Schemas - Schemas Pydantic para Eventos
Define estruturas de dados para requisições e respostas da API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class DeviceDataSubmit(BaseModel):
    """
    Schema para submissão de dados do dispositivo.
    
    Usado pelo agente local para enviar dados de sinais Wi-Fi
    processados para o backend.
    """
    features: Dict[str, Any] = Field(..., description="Features extraídas dos sinais")
    timestamp: float = Field(..., description="Timestamp Unix da captura")
    data_type: str = Field(..., description="Tipo de dados: rssi ou csi")
    
    @validator("data_type")
    def validate_data_type(cls, v):
        """Valida que data_type é rssi ou csi"""
        if v not in ["rssi", "csi"]:
            raise ValueError("data_type deve ser 'rssi' ou 'csi'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": {
                    "rssi_normalized": 0.75,
                    "signal_variance": 0.45,
                    "rate_of_change": 0.12,
                    "instability_score": 0.68
                },
                "timestamp": 1704067200.0,
                "data_type": "rssi"
            }
        }


class EventCreate(BaseModel):
    """
    Schema para criação de evento.
    
    Usado internamente pelo pipeline de detecção para
    persistir eventos no banco de dados.
    """
    tenant_id: UUID
    device_id: UUID
    event_type: str = Field(..., description="Tipo do evento")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança da detecção")
    timestamp: datetime
    event_metadata: Optional[Dict[str, Any]] = None
    
    @validator("event_type")
    def validate_event_type(cls, v):
        """Valida que event_type é válido"""
        valid_types = ["presence", "movement", "fall_suspected", "prolonged_inactivity", "no_presence"]
        if v not in valid_types:
            raise ValueError(f"event_type deve ser um de: {', '.join(valid_types)}")
        return v


class EventResponse(BaseModel):
    """
    Schema de resposta para um evento.
    
    Retornado em endpoints de consulta de eventos.
    """
    id: UUID
    tenant_id: UUID
    device_id: UUID
    event_type: str
    confidence: float
    timestamp: datetime
    event_metadata: Optional[Dict[str, Any]]
    is_false_positive: bool
    user_notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "device_id": "123e4567-e89b-12d3-a456-426614174002",
                "event_type": "presence",
                "confidence": 0.85,
                "timestamp": "2024-01-01T12:00:00",
                "event_metadata": {"reason": "high_signal_high_variance"},
                "is_false_positive": False,
                "user_notes": None,
                "created_at": "2024-01-01T12:00:00"
            }
        }


class EventListResponse(BaseModel):
    """
    Schema de resposta para listagem paginada de eventos.
    """
    events: List[EventResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        }


class EventStatsResponse(BaseModel):
    """
    Schema de resposta para estatísticas de eventos.
    """
    total_events: int
    events_by_type: Dict[str, int]
    events_by_device: Dict[str, int]
    avg_confidence: float
    false_positives: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_events": 150,
                "events_by_type": {
                    "presence": 80,
                    "movement": 50,
                    "fall_suspected": 10,
                    "prolonged_inactivity": 10
                },
                "events_by_device": {
                    "device-1": 100,
                    "device-2": 50
                },
                "avg_confidence": 0.82,
                "false_positives": 5
            }
        }


class EventFeedback(BaseModel):
    """
    Schema para feedback do usuário sobre um evento.
    
    Permite marcar eventos como falsos positivos e adicionar notas.
    """
    is_false_positive: bool = Field(..., description="Se o evento é um falso positivo")
    user_notes: Optional[str] = Field(None, max_length=500, description="Notas do usuário")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_false_positive": True,
                "user_notes": "Não havia ninguém em casa neste momento"
            }
        }
