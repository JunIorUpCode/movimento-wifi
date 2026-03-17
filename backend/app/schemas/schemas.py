"""
Schemas Pydantic para validação e serialização de dados na API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Eventos ---

class EventOut(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    confidence: float
    provider: str
    metadata_json: str

    model_config = {"from_attributes": True}


# --- Status do sistema ---

class StatusOut(BaseModel):
    is_monitoring: bool = False
    current_event: str = "no_presence"
    confidence: float = 0.0
    simulation_mode: str = "empty"
    provider: str = "mock"
    uptime_seconds: float = 0.0
    total_events: int = 0
    signal_data: Optional[dict[str, Any]] = None
    features: Optional[dict[str, Any]] = None


# --- Configuração ---

class ConfigOut(BaseModel):
    movement_sensitivity: float = Field(default=0.5, description="Limiar de variância para detectar movimento (ajustado para Wi-Fi real)")
    fall_threshold: float = Field(default=12.0, description="Limiar de taxa de variação para detectar queda")
    inactivity_timeout: float = Field(default=30.0, description="Segundos para considerar inatividade prolongada")
    active_provider: str = Field(default="mock", description="Provider ativo")
    sampling_interval: float = Field(default=1.0, description="Intervalo de amostragem em segundos")


class ConfigIn(BaseModel):
    movement_sensitivity: Optional[float] = None
    fall_threshold: Optional[float] = None
    inactivity_timeout: Optional[float] = None
    active_provider: Optional[str] = None
    sampling_interval: Optional[float] = None


# --- Simulação ---

class SimulationModeIn(BaseModel):
    mode: str = Field(..., description="Modo: empty, still, moving, fall, post_fall_inactivity, random")


# --- Health ---

class HealthOut(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0


# --- WebSocket payload ---

class LiveUpdate(BaseModel):
    event_type: str
    confidence: float
    timestamp: float
    signal: dict[str, Any] = {}
    features: dict[str, Any] = {}
    alert: Optional[str] = None


# --- ML Models ---

class ModelInfoResponse(BaseModel):
    """Informações de um modelo ML."""
    id: int
    name: str
    model_type: str
    file_path: str
    accuracy: Optional[float]
    training_samples: int
    created_at: datetime
    is_active: bool
    metadata_json: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ModelActivateRequest(BaseModel):
    """Request para ativar um modelo."""
    name: str = Field(..., min_length=1, max_length=100)


# --- Notification Logs ---

class NotificationLogResponse(BaseModel):
    """Log de notificação enviada."""
    id: int
    timestamp: datetime
    channel: str
    event_type: str
    confidence: float
    recipient: str
    success: bool
    error_message: Optional[str]
    alert_data: str

    model_config = {"from_attributes": True}


# --- Notification Configuration ---

class NotificationConfigRequest(BaseModel):
    """Configuração de notificações."""
    enabled: bool = True
    channels: list[str] = Field(default_factory=list, description="Canais ativos: telegram, whatsapp, webhook")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confiança mínima para enviar alerta")
    cooldown_seconds: int = Field(default=300, ge=0, description="Tempo mínimo entre alertas do mesmo tipo")
    quiet_hours: list[tuple[int, int]] = Field(default_factory=list, description="Horários de silêncio [(start, end)]")
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(None, description="Token do bot Telegram")
    telegram_chat_ids: list[str] = Field(default_factory=list, description="IDs dos chats Telegram")
    
    # WhatsApp (via Twilio)
    twilio_account_sid: Optional[str] = Field(None, description="Twilio Account SID")
    twilio_auth_token: Optional[str] = Field(None, description="Twilio Auth Token")
    twilio_whatsapp_from: Optional[str] = Field(None, description="Número WhatsApp de origem")
    whatsapp_recipients: list[str] = Field(default_factory=list, description="Números WhatsApp destinatários")
    
    # Webhook
    webhook_urls: list[str] = Field(default_factory=list, description="URLs de webhook")
    webhook_secret: Optional[str] = Field(None, description="Secret para assinatura HMAC")


class NotificationConfigResponse(BaseModel):
    """Resposta com configuração de notificações."""
    enabled: bool
    channels: list[str]
    min_confidence: float
    cooldown_seconds: int
    quiet_hours: list[tuple[int, int]]
    
    # Telegram (sem expor token)
    telegram_configured: bool
    telegram_chat_count: int
    
    # WhatsApp (sem expor credenciais)
    whatsapp_configured: bool
    whatsapp_recipient_count: int
    
    # Webhook (sem expor secret)
    webhook_configured: bool
    webhook_url_count: int


class NotificationTestRequest(BaseModel):
    """Request para testar notificações."""
    channel: str = Field(..., description="Canal a testar: telegram, whatsapp, webhook")
    message: str = Field(default="Teste de notificação WiFiSense", description="Mensagem de teste")


# --- Calibração ---

class CalibrationStartIn(BaseModel):
    """Request para iniciar calibração."""
    duration_seconds: int = Field(default=60, ge=10, le=300, description="Duração da calibração em segundos")
    profile_name: str = Field(default="default", min_length=1, max_length=100, description="Nome do perfil de calibração")


class CalibrationProfileOut(BaseModel):
    """Perfil de calibração salvo."""
    id: int
    name: str
    baseline_json: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}


# --- Zonas ---

class ZoneIn(BaseModel):
    """Request para criar/atualizar zona."""
    name: str = Field(..., min_length=1, max_length=100, description="Nome da zona")
    rssi_min: float = Field(..., description="RSSI mínimo da zona (dBm)")
    rssi_max: float = Field(..., description="RSSI máximo da zona (dBm)")
    alert_config_json: str = Field(default="{}", description="Configuração de alertas em JSON")


class ZoneOut(BaseModel):
    """Zona de monitoramento."""
    id: int
    name: str
    rssi_min: float
    rssi_max: float
    alert_config_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Estatísticas ---

class EventStatsOut(BaseModel):
    """Estatísticas agregadas de eventos."""
    total_events: int
    by_type: dict[str, int]
    avg_confidence: float
    period_hours: int


class BehaviorPatternOut(BaseModel):
    """Padrão comportamental aprendido."""
    id: int
    hour_of_day: int
    day_of_week: int
    presence_probability: float
    avg_movement_level: float
    sample_count: int
    last_updated: datetime

    model_config = {"from_attributes": True}


class PerformanceStatsOut(BaseModel):
    """Estatísticas de performance do sistema."""
    avg_total_latency_ms: float
    avg_capture_time_ms: float
    avg_processing_time_ms: float
    avg_detection_time_ms: float
    avg_memory_usage_mb: float
    avg_cpu_usage_percent: float
    samples_count: int


# --- Coleta ML ---

class MLCollectionStatusOut(BaseModel):
    """Status da coleta de dados ML."""
    is_collecting: bool
    total_samples: int
    pending_features: int
    label_distribution: dict[str, int]
    models_dir: str


class MLLabelIn(BaseModel):
    """Request para rotular evento."""
    label: str = Field(
        ...,
        description="Rótulo: no_presence, presence_still, presence_moving, fall_suspected, prolonged_inactivity",
    )
    window_seconds: int = Field(default=10, ge=1, le=60, description="Janela de tempo em segundos para rotular")
