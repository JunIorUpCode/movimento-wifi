# -*- coding: utf-8 -*-
"""
Shared Logging - Sistema de Logging Estruturado com JSON centralizado.

Melhorias sobre a versão anterior:
- correlation_id injetado automaticamente via contextvars
- Sanitização de PII (e-mails, tokens, senhas, cartões, telefones)
- Rotação de arquivo: 10 MB por arquivo, 5 backups
- Helper set_correlation_id / get_correlation_id
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

from pythonjsonlogger import jsonlogger

# ── Contexto de correlation_id ───────────────────────────────────────────────

_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Define o correlation_id para o contexto atual (request/task).

    Args:
        correlation_id: ID a usar. Se None, gera um UUID v4 aleatório.

    Returns:
        O correlation_id definido.
    """
    cid = correlation_id or str(uuid.uuid4())
    _correlation_id_var.set(cid)
    return cid


def get_correlation_id() -> str:
    """Retorna o correlation_id do contexto atual ('' se não definido)."""
    return _correlation_id_var.get()


def clear_correlation_id() -> None:
    """Remove o correlation_id do contexto atual."""
    _correlation_id_var.set("")


# ── Sanitização de PII ───────────────────────────────────────────────────────

# Padrões de PII ordenados do mais específico para o mais genérico
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # JWT (header.payload.signature)
    (re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "[JWT_REDACTED]"),
    # Cartão de crédito (13-19 dígitos, com ou sem separadores)
    (re.compile(r"\b(?:\d[\s\-]?){13,19}\b"), "[CARD_REDACTED]"),
    # E-mail
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Telefone (formatos BR e internacional)
    (re.compile(r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\s\-]?\d{4}\b"), "[PHONE_REDACTED]"),
    # CPF (XXX.XXX.XXX-XX ou XXXXXXXXXXX)
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[\-]?\d{2}\b"), "[CPF_REDACTED]"),
    # Chaves de API / tokens genéricos (palavras longas com prefixos comuns)
    (re.compile(r"\b(?:sk|pk|api|tok|key|secret|token)_[A-Za-z0-9_\-]{16,}\b", re.IGNORECASE), "[TOKEN_REDACTED]"),
]

# Campos sensíveis cujo VALOR deve ser redactado (keys case-insensitive)
_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "senha", "secret", "token", "access_token", "refresh_token",
    "id_token", "api_key", "apikey", "encryption_key", "jwt_secret",
    "stripe_api_key", "credit_card", "card_number", "cvv", "cpf",
    "authorization",
})


def sanitize(value: Any) -> Any:
    """
    Sanitiza recursivamente um valor, redactando PII.

    - Strings: aplica regexes de PII
    - Dicts: redacta valores cujos keys sejam sensíveis; sanitiza os demais
    - Lists/tuples: sanitiza cada elemento
    - Outros tipos: retorna sem alteração
    """
    if isinstance(value, str):
        for pattern, replacement in _PII_PATTERNS:
            value = pattern.sub(replacement, value)
        return value

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS:
                result[k] = "[REDACTED]"
            else:
                result[k] = sanitize(v)
        return result

    if isinstance(value, (list, tuple)):
        sanitized = [sanitize(item) for item in value]
        return type(value)(sanitized)

    return value


# ── Filtro que injeta correlation_id e sanitiza mensagens ───────────────────

class _CorrelationFilter(logging.Filter):
    """Filtro que injeta correlation_id e sanitiza o message de cada LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        # Sanitiza a mensagem
        if isinstance(record.msg, str):
            record.msg = sanitize(record.msg)
        # Sanitiza args (usados na interpolação "%-style")
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize(a) for a in record.args)
        return True


# ── Logger estruturado ───────────────────────────────────────────────────────

_LOG_DIR = os.environ.get("LOG_DIR", "logs")
_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_LOG_BACKUP_COUNT = 5


class StructuredLogger:
    """
    Logger estruturado que emite logs em formato JSON.

    Saídas:
    - stdout (sempre)
    - arquivo rotativo logs/<name>.log (10 MB, 5 backups) se LOG_DIR existir
      ou LOG_DIR puder ser criado.

    correlation_id é injetado automaticamente via contextvars; defina-o com
    set_correlation_id() no início de cada requisição/task.
    """

    def __init__(self, name: str, level: str = "INFO") -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.handlers.clear()
        self.logger.propagate = False

        fmt = "%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s"
        datefmt = "%Y-%m-%dT%H:%M:%S"

        correlation_filter = _CorrelationFilter()

        # Handler stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(jsonlogger.JsonFormatter(fmt=fmt, datefmt=datefmt))
        stdout_handler.addFilter(correlation_filter)
        self.logger.addHandler(stdout_handler)

        # Handler arquivo rotativo (opcional — ignora falhas de permissão)
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            log_path = os.path.join(_LOG_DIR, f"{name}.log")
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=_LOG_MAX_BYTES,
                backupCount=_LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setFormatter(jsonlogger.JsonFormatter(fmt=fmt, datefmt=datefmt))
            file_handler.addFilter(correlation_filter)
            self.logger.addHandler(file_handler)
        except OSError:
            pass  # sem permissão para criar diretório/arquivo — apenas stdout

    # ── Métodos de log ────────────────────────────────────────────────────────

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        extra = {k: sanitize(v) for k, v in kwargs.items()}
        getattr(self.logger, level.lower())(message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log("CRITICAL", message, **kwargs)

    # ── Helpers de domínio ────────────────────────────────────────────────────

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Log estruturado de requisição HTTP."""
        self.info(
            f"{method} {path} - {status_code}",
            event_type="http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            tenant_id=tenant_id,
        )

    def log_event(
        self,
        event_type: str,
        tenant_id: str,
        device_id: str,
        confidence: float,
        **kwargs: Any,
    ) -> None:
        """Log estruturado de evento detectado."""
        self.info(
            f"Evento detectado: {event_type}",
            event_type="event_detected",
            detected_event_type=event_type,
            tenant_id=tenant_id,
            device_id=device_id,
            confidence=confidence,
            **kwargs,
        )

    def log_notification(
        self,
        channel: str,
        tenant_id: str,
        event_id: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log estruturado de notificação enviada."""
        level = "INFO" if success else "ERROR"
        self._log(
            level,
            f"Notificação {channel} {'enviada' if success else 'falhou'}",
            event_type="notification_sent",
            channel=channel,
            tenant_id=tenant_id,
            event_id=event_id,
            success=success,
            error=error,
        )


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """
    Factory para criar loggers estruturados.

    Args:
        name: Nome do logger (geralmente nome do serviço).
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        StructuredLogger configurado com JSON + correlation_id + sanitização.
    """
    return StructuredLogger(name, level)
