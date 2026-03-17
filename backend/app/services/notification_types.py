"""
Sistema de notificações - Tipos e interfaces base.

Define as estruturas de dados e interfaces abstratas para o sistema de notificações:
- NotificationConfig: Configuração de alertas
- NotificationChannel: Interface abstrata para canais de notificação
- Alert: Estrutura de dados para alertas
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class NotificationConfig:
    """Configuração do sistema de notificações."""
    
    # Configurações gerais
    enabled: bool = True
    channels: List[str] = field(default_factory=list)  # ["telegram", "whatsapp", "webhook"]
    min_confidence: float = 0.7
    cooldown_seconds: int = 300
    quiet_hours: List[tuple[int, int]] = field(default_factory=list)  # [(22, 7)] = 22h-7h
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_ids: List[str] = field(default_factory=list)
    
    # WhatsApp (via Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None
    whatsapp_recipients: List[str] = field(default_factory=list)
    
    # Webhook
    webhook_urls: List[str] = field(default_factory=list)
    webhook_secret: Optional[str] = None
    
    def __post_init__(self):
        """Valida configuração após inicialização."""
        if self.min_confidence < 0.0 or self.min_confidence > 1.0:
            raise ValueError("min_confidence deve estar entre 0.0 e 1.0")
        
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds deve ser não-negativo")
        
        # Valida quiet_hours
        for start, end in self.quiet_hours:
            if not (0 <= start < 24 and 0 <= end < 24):
                raise ValueError(f"Horários inválidos em quiet_hours: ({start}, {end})")


@dataclass
class Alert:
    """Estrutura de dados para alertas."""
    
    event_type: str
    confidence: float
    timestamp: float
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Valida dados do alerta após inicialização."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence deve estar entre 0.0 e 1.0")
        
        if self.timestamp < 0:
            raise ValueError("timestamp deve ser não-negativo")
        
        if not self.event_type:
            raise ValueError("event_type não pode ser vazio")
    
    def to_dict(self) -> dict[str, Any]:
        """Converte alerta para dicionário.
        
        Returns:
            Dicionário com todos os campos do alerta
        """
        return {
            "event_type": self.event_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "message": self.message,
            "details": self.details
        }


class NotificationChannel(ABC):
    """Interface abstrata para canais de notificação.
    
    Cada canal de notificação (Telegram, WhatsApp, Webhook, etc.)
    deve implementar esta interface.
    """
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Envia notificação através do canal.
        
        Args:
            alert: Alerta a ser enviado
            
        Returns:
            True se o envio foi bem-sucedido, False caso contrário
        """
        pass
    
    @abstractmethod
    def format_message(self, alert: Alert) -> str:
        """Formata mensagem do alerta para o canal específico.
        
        Args:
            alert: Alerta a ser formatado
            
        Returns:
            Mensagem formatada como string
        """
        pass
