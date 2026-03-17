"""Structured logging implementation with JSON format and log rotation."""

import logging
import json
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
import re


class SensitiveDataSanitizer:
    """Sanitizes sensitive data from log messages and context."""
    
    # Patterns for sensitive data
    PATTERNS = {
        'password': re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
        'token': re.compile(r'(token|api_key|secret)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    }
    
    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """Sanitize sensitive data from various data types."""
        if isinstance(data, str):
            return cls._sanitize_string(data)
        elif isinstance(data, dict):
            return cls._sanitize_dict(data)
        elif isinstance(data, list):
            return [cls.sanitize(item) for item in data]
        else:
            return data
    
    @classmethod
    def _sanitize_string(cls, text: str) -> str:
        """Sanitize sensitive data from string."""
        result = text
        for pattern_name, pattern in cls.PATTERNS.items():
            if pattern_name in ['password', 'token']:
                # Replace the value part only
                result = pattern.sub(r'\1=***REDACTED***', result)
            else:
                # Replace entire match
                result = pattern.sub('***REDACTED***', result)
        return result
    
    @classmethod
    def _sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from dictionary."""
        sanitized = {}
        sensitive_keys = {'password', 'passwd', 'pwd', 'token', 'api_key', 'secret', 
                         'auth_token', 'access_token', 'refresh_token', 'private_key'}
        
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, str):
                sanitized[key] = cls._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize(item) for item in value]
            else:
                sanitized[key] = value
        
        return sanitized


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', None),
        }
        
        # Add context data if present
        if hasattr(record, 'context') and record.context:
            # Sanitize context data
            sanitized_context = SensitiveDataSanitizer.sanitize(record.context)
            log_data["context"] = sanitized_context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add file location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        return json.dumps(log_data)


class StructuredLogger:
    """Logger with structured JSON format, rotation, and sanitization."""
    
    def __init__(self, name: str, log_dir: str = "logs", 
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 10):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically module name)
            log_dir: Directory for log files
            max_bytes: Maximum size per log file (default: 10MB)
            backup_count: Number of backup files to keep (default: 10)
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)
        self._correlation_id: Optional[str] = None
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Configure rotating file handler
        log_file = log_path / "wifisense.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(JSONFormatter())
        
        # Add console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        
        # Clear existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        # Add handlers
        self._logger.addHandler(handler)
        self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """
        Set correlation ID for tracking related events.
        
        Args:
            correlation_id: Optional correlation ID. If None, generates a new UUID.
            
        Returns:
            The correlation ID that was set.
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        self._correlation_id = correlation_id
        return correlation_id
    
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        self._correlation_id = None
    
    def _log(self, level: int, message: str, **context: Any) -> None:
        """Internal logging method with context and correlation ID."""
        extra = {
            'correlation_id': self._correlation_id,
            'context': context if context else None
        }
        self._logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **context)
    
    def error(self, message: str, **context: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **context)
    
    def exception(self, message: str, **context: Any) -> None:
        """Log exception with traceback."""
        extra = {
            'correlation_id': self._correlation_id,
            'context': context if context else None
        }
        self._logger.exception(message, extra=extra)
    
    def set_level(self, level: str) -> None:
        """
        Set logging level.
        
        Args:
            level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self._logger.setLevel(level_map[level.upper()])
        else:
            raise ValueError(f"Invalid log level: {level}")
    
    def close(self) -> None:
        """Close all handlers and release file locks."""
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)


# Global logger registry
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, **kwargs: Any) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (typically __name__)
        **kwargs: Additional arguments for StructuredLogger
        
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, **kwargs)
    return _loggers[name]


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Setup global logging configuration.
    
    Args:
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    """
    # Create logs directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add rotating file handler
    log_file = Path(log_dir) / "wifisense.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    root_logger.addHandler(console_handler)
