"""
ConfigService — Gerenciamento de configuração em memória.
"""

from __future__ import annotations

from app.detection.heuristic_detector import ThresholdConfig
from app.schemas.schemas import ConfigIn, ConfigOut


class ConfigService:
    """Singleton de configuração do sistema."""

    _instance: ConfigService | None = None

    def __new__(cls) -> ConfigService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = ConfigOut()
        return cls._instance

    @property
    def config(self) -> ConfigOut:
        return self._config

    def update(self, data: ConfigIn) -> ConfigOut:
        """Atualiza configuração com os campos fornecidos."""
        update_data = data.model_dump(exclude_none=True)
        current = self._config.model_dump()
        current.update(update_data)
        self._config = ConfigOut(**current)
        return self._config

    def get_threshold_config(self) -> ThresholdConfig:
        """Converte para ThresholdConfig do detector."""
        return ThresholdConfig(
            movement_variance_min=self._config.movement_sensitivity,
            movement_rate_min=self._config.movement_sensitivity * 1.5,
            fall_rate_spike=self._config.fall_threshold,
            fall_energy_spike=self._config.fall_threshold * 2,
            inactivity_timeout=self._config.inactivity_timeout,
        )


# Instância global
config_service = ConfigService()
