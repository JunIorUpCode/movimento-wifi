# -*- coding: utf-8 -*-
"""
Shared Logging - Sistema de Logging Estruturado
Fornece logging estruturado em JSON para todos os microserviços
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """
    Logger estruturado que emite logs em formato JSON
    Facilita parsing e análise de logs em sistemas de monitoramento
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        """
        Inicializa o logger estruturado
        
        Args:
            name: Nome do logger (geralmente nome do serviço)
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove handlers existentes para evitar duplicação
        self.logger.handlers.clear()
        
        # Configura handler para stdout
        handler = logging.StreamHandler(sys.stdout)
        
        # Formato JSON estruturado
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs):
        """
        Método interno para logging estruturado
        
        Args:
            level: Nível do log
            message: Mensagem principal
            **kwargs: Campos adicionais para incluir no log
        """
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de informação"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self._log("CRITICAL", message, **kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration_ms: float, tenant_id: Optional[str] = None):
        """
        Log específico para requisições HTTP
        
        Args:
            method: Método HTTP (GET, POST, etc)
            path: Caminho da requisição
            status_code: Código de status HTTP
            duration_ms: Duração da requisição em milissegundos
            tenant_id: ID do tenant (se aplicável)
        """
        self.info(
            f"{method} {path} - {status_code}",
            event_type="http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            tenant_id=tenant_id
        )
    
    def log_event(self, event_type: str, tenant_id: str, device_id: str,
                 confidence: float, **kwargs):
        """
        Log específico para eventos detectados
        
        Args:
            event_type: Tipo do evento (presence, movement, fall, etc)
            tenant_id: ID do tenant
            device_id: ID do dispositivo
            confidence: Confiança da detecção (0-1)
            **kwargs: Metadados adicionais
        """
        self.info(
            f"Evento detectado: {event_type}",
            event_type="event_detected",
            detected_event_type=event_type,
            tenant_id=tenant_id,
            device_id=device_id,
            confidence=confidence,
            **kwargs
        )
    
    def log_notification(self, channel: str, tenant_id: str, event_id: str,
                        success: bool, error: Optional[str] = None):
        """
        Log específico para notificações enviadas
        
        Args:
            channel: Canal de notificação (telegram, email, webhook)
            tenant_id: ID do tenant
            event_id: ID do evento
            success: Se a notificação foi enviada com sucesso
            error: Mensagem de erro (se houver)
        """
        level = "info" if success else "error"
        message = f"Notificação {channel} {'enviada' if success else 'falhou'}"
        
        self._log(
            level.upper(),
            message,
            event_type="notification_sent",
            channel=channel,
            tenant_id=tenant_id,
            event_id=event_id,
            success=success,
            error=error
        )


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """
    Factory function para criar loggers estruturados
    
    Args:
        name: Nome do logger
        level: Nível de log
    
    Returns:
        Instância de StructuredLogger
    """
    return StructuredLogger(name, level)
