"""
exceptions.py — Hierarquia de exceções do WiFiSense Local.

Define exceções tipadas para cada domínio do sistema, permitindo
tratamento granular de erros nas rotas e serviços.
"""

from __future__ import annotations


# ══════════════════════════════════════════════════════
# Base
# ══════════════════════════════════════════════════════

class WiFiSenseError(Exception):
    """Base para todas as exceções do WiFiSense."""

    def __init__(self, message: str, code: str = "internal_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"error": self.code, "detail": self.message}


# ══════════════════════════════════════════════════════
# Detecção
# ══════════════════════════════════════════════════════

class DetectionError(WiFiSenseError):
    """Erro na camada de detecção."""


class ModelNotLoadedError(DetectionError):
    """Modelo ML não foi carregado."""

    def __init__(self, model_path: str = "") -> None:
        super().__init__(
            f"Modelo ML não carregado: {model_path}" if model_path else "Modelo ML não carregado.",
            code="model_not_loaded",
        )


class DetectorNotReadyError(DetectionError):
    """Detector não está pronto para classificar."""

    def __init__(self) -> None:
        super().__init__("Detector não está pronto (buffer insuficiente).", code="detector_not_ready")


# ══════════════════════════════════════════════════════
# Captura
# ══════════════════════════════════════════════════════

class CaptureError(WiFiSenseError):
    """Erro na camada de captura de sinal."""


class ProviderUnavailableError(CaptureError):
    """Provider de sinal não está disponível."""

    def __init__(self, provider: str = "") -> None:
        super().__init__(
            f"Provider '{provider}' não disponível." if provider else "Provider não disponível.",
            code="provider_unavailable",
        )


class SignalTimeoutError(CaptureError):
    """Timeout ao aguardar sinal do provider."""

    def __init__(self, timeout_seconds: float = 0.0) -> None:
        super().__init__(
            f"Timeout após {timeout_seconds:.1f}s aguardando sinal.",
            code="signal_timeout",
        )


# ══════════════════════════════════════════════════════
# Calibração
# ══════════════════════════════════════════════════════

class CalibrationError(WiFiSenseError):
    """Erro durante processo de calibração."""

    def __init__(self, message: str = "Erro de calibração.") -> None:
        super().__init__(message, code="calibration_error")


class CalibrationMovementError(CalibrationError):
    """Movimento detectado durante calibração."""

    def __init__(self) -> None:
        super().__init__("Movimento detectado durante calibração. Repita em ambiente vazio.")
        self.code = "calibration_movement_detected"


class CalibrationAlreadyRunningError(CalibrationError):
    """Tentativa de iniciar calibração quando já está em andamento."""

    def __init__(self) -> None:
        super().__init__("Calibração já está em andamento.")
        self.code = "calibration_already_running"


class CalibrationProfileNotFoundError(CalibrationError):
    """Perfil de calibração não encontrado."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Perfil de calibração '{name}' não encontrado.")
        self.code = "calibration_profile_not_found"


# ══════════════════════════════════════════════════════
# ML
# ══════════════════════════════════════════════════════

class MLError(WiFiSenseError):
    """Erro na camada de Machine Learning."""


class MLCollectionNotActiveError(MLError):
    """Tentativa de rotular sem coleta ativa."""

    def __init__(self) -> None:
        super().__init__("Coleta de dados ML não está ativa.", code="ml_collection_not_active")


class MLInvalidLabelError(MLError):
    """Rótulo ML inválido."""

    def __init__(self, label: str, valid_labels: list[str]) -> None:
        super().__init__(
            f"Rótulo '{label}' inválido. Válidos: {valid_labels}",
            code="ml_invalid_label",
        )


class MLTrainingError(MLError):
    """Erro durante treinamento do modelo."""

    def __init__(self, detail: str = "") -> None:
        super().__init__(
            f"Erro no treinamento: {detail}" if detail else "Erro durante treinamento.",
            code="ml_training_error",
        )


class MLInsufficientDataError(MLError):
    """Dados insuficientes para treinamento."""

    def __init__(self, count: int, minimum: int) -> None:
        super().__init__(
            f"Dados insuficientes: {count} amostras (mínimo: {minimum}).",
            code="ml_insufficient_data",
        )


# ══════════════════════════════════════════════════════
# Configuração
# ══════════════════════════════════════════════════════

class ConfigError(WiFiSenseError):
    """Erro de configuração."""


class ConfigProfileNotFoundError(ConfigError):
    """Perfil de configuração não encontrado."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Perfil de configuração '{name}' não encontrado.", code="config_profile_not_found")


class ConfigValidationError(ConfigError):
    """Configuração inválida."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Configuração inválida: {detail}", code="config_validation_error")


# ══════════════════════════════════════════════════════
# Zonas
# ══════════════════════════════════════════════════════

class ZoneError(WiFiSenseError):
    """Erro relacionado a zonas RSSI."""


class ZoneNotFoundError(ZoneError):
    """Zona não encontrada."""

    def __init__(self, zone_id: int) -> None:
        super().__init__(f"Zona {zone_id} não encontrada.", code="zone_not_found")


class ZoneOverlapError(ZoneError):
    """Zona com faixa RSSI sobreposição."""

    def __init__(self) -> None:
        super().__init__("Faixa RSSI sobrepõe zona existente.", code="zone_overlap")


# ══════════════════════════════════════════════════════
# Notificações
# ══════════════════════════════════════════════════════

class NotificationError(WiFiSenseError):
    """Erro ao enviar notificação."""


class NotificationChannelError(NotificationError):
    """Erro em canal de notificação específico."""

    def __init__(self, channel: str, detail: str = "") -> None:
        super().__init__(
            f"Erro no canal '{channel}': {detail}" if detail else f"Erro no canal '{channel}'.",
            code="notification_channel_error",
        )


class NotificationRateLimitError(NotificationError):
    """Notificação bloqueada por cooldown."""

    def __init__(self, seconds_remaining: float) -> None:
        super().__init__(
            f"Cooldown ativo: aguarde {seconds_remaining:.0f}s.",
            code="notification_rate_limit",
        )


# ══════════════════════════════════════════════════════
# Monitor
# ══════════════════════════════════════════════════════

class MonitorError(WiFiSenseError):
    """Erro no serviço de monitoramento."""


class MonitorNotRunningError(MonitorError):
    """Tentativa de operação com monitor parado."""

    def __init__(self) -> None:
        super().__init__("Monitor não está em execução.", code="monitor_not_running")


class MonitorAlreadyRunningError(MonitorError):
    """Tentativa de iniciar monitor já em execução."""

    def __init__(self) -> None:
        super().__init__("Monitor já está em execução.", code="monitor_already_running")
