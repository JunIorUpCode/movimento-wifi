"""
Models SQLAlchemy para persistência no SQLite.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Event(Base):
    """Evento detectado pelo sistema de monitoramento."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    
    # Novos campos para evolução
    zone_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CalibrationProfile(Base):
    """Perfil de calibração salvo."""
    
    __tablename__ = "calibration_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    baseline_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class BehaviorPattern(Base):
    """Padrões de comportamento aprendidos."""
    
    __tablename__ = "behavior_patterns"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-23
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6
    presence_probability: Mapped[float] = mapped_column(Float, nullable=False)
    avg_movement_level: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('idx_hour_day', 'hour_of_day', 'day_of_week'),
    )


class Zone(Base):
    """Zona de monitoramento."""
    
    __tablename__ = "zones"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rssi_min: Mapped[float] = mapped_column(Float, nullable=False)
    rssi_max: Mapped[float] = mapped_column(Float, nullable=False)
    alert_config_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PerformanceMetric(Base):
    """Métricas de performance do sistema."""
    
    __tablename__ = "performance_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    capture_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    detection_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage_mb: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, nullable=False)


class MLModel(Base):
    """Metadados de modelos ML treinados."""
    
    __tablename__ = "ml_models"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "classifier", "anomaly"
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class NotificationLog(Base):
    """Log de notificações enviadas."""
    
    __tablename__ = "notification_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    recipient: Mapped[str] = mapped_column(String(200), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alert_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
