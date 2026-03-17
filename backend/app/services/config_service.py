"""
ConfigService — Gerenciamento de configuração com suporte a múltiplos perfis.

Perfis são salvos em ``config_profiles.json`` no diretório do backend.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from app.detection.heuristic_detector import ThresholdConfig
from app.schemas.schemas import ConfigIn, ConfigOut

logger = logging.getLogger(__name__)

# Arquivo de persistência dos perfis (junto ao main.py)
_PROFILES_FILE = Path(__file__).resolve().parent.parent.parent / "config_profiles.json"


class ConfigService:
    """Singleton de configuração do sistema com suporte a múltiplos perfis."""

    _instance: ConfigService | None = None

    def __new__(cls) -> ConfigService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = ConfigOut()
            cls._instance._profiles: Dict[str, dict] = {}
            cls._instance._load_profiles()
        return cls._instance

    # ─── config ativa ────────────────────────────────────────────────────────

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

    # ─── perfis ──────────────────────────────────────────────────────────────

    def list_profiles(self) -> List[str]:
        """Retorna lista de nomes de perfis salvos."""
        return list(self._profiles.keys())

    def save_profile(self, name: str) -> None:
        """
        Salva a configuração ativa como um perfil nomeado.

        Sobrescreve perfil existente se o nome já existir.
        """
        self._profiles[name] = self._config.model_dump()
        self._persist_profiles()
        logger.info(f"Perfil de configuração salvo: '{name}'")

    def load_profile(self, name: str) -> ConfigOut:
        """
        Carrega e aplica um perfil nomeado como configuração ativa.

        Returns:
            ConfigOut com a configuração carregada.

        Raises:
            KeyError: Se o perfil não existir.
        """
        if name not in self._profiles:
            raise KeyError(f"Perfil '{name}' não encontrado.")
        self._config = ConfigOut(**self._profiles[name])
        logger.info(f"Perfil de configuração ativado: '{name}'")
        return self._config

    def delete_profile(self, name: str) -> None:
        """
        Remove um perfil salvo.

        Raises:
            KeyError: Se o perfil não existir.
        """
        if name not in self._profiles:
            raise KeyError(f"Perfil '{name}' não encontrado.")
        del self._profiles[name]
        self._persist_profiles()
        logger.info(f"Perfil de configuração removido: '{name}'")

    def get_profile(self, name: str) -> ConfigOut:
        """Retorna um perfil sem aplicá-lo como config ativa."""
        if name not in self._profiles:
            raise KeyError(f"Perfil '{name}' não encontrado.")
        return ConfigOut(**self._profiles[name])

    # ─── validação e parsing ──────────────────────────────────────────────────

    @staticmethod
    def parse_config(raw: dict[str, Any]) -> ConfigOut:
        """
        Faz parse e validação de um dicionário de configuração.

        Usa Pydantic para validar tipos e valores. Campos ausentes recebem
        os valores padrão de ConfigOut.

        Args:
            raw: Dicionário com campos de configuração (pode ser parcial).

        Returns:
            ConfigOut validado.

        Raises:
            ValueError: Se algum campo tiver valor inválido (ex: tipo errado).
        """
        try:
            return ConfigOut(**raw)
        except (ValidationError, TypeError) as exc:
            raise ValueError(f"Configuração inválida: {exc}") from exc

    @staticmethod
    def get_json_schema() -> dict[str, Any]:
        """
        Retorna o JSON Schema de ConfigOut para validação externa.

        Returns:
            Dicionário com o schema JSON (compatível com JSON Schema Draft 7).
        """
        return ConfigOut.model_json_schema()

    def validate_and_update(self, raw: dict[str, Any]) -> ConfigOut:
        """
        Valida um dicionário de configuração e aplica como config ativa.

        Combina parse_config + update em um único método seguro.

        Args:
            raw: Dicionário com campos de ConfigIn (pode ser parcial).

        Returns:
            ConfigOut com a configuração aplicada.

        Raises:
            ValueError: Se algum campo tiver valor inválido.
        """
        try:
            data = ConfigIn(**raw)
        except (ValidationError, TypeError) as exc:
            raise ValueError(f"Dados de configuração inválidos: {exc}") from exc
        return self.update(data)

    # ─── persistência ────────────────────────────────────────────────────────

    def _persist_profiles(self) -> None:
        """Salva perfis no arquivo JSON."""
        try:
            _PROFILES_FILE.write_text(
                json.dumps(self._profiles, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(f"Não foi possível persistir perfis de configuração: {exc}")

    def _load_profiles(self) -> None:
        """Carrega perfis do arquivo JSON (se existir)."""
        try:
            if _PROFILES_FILE.exists():
                data = json.loads(_PROFILES_FILE.read_text(encoding="utf-8"))
                # Valida cada perfil contra ConfigOut
                for name, raw in data.items():
                    try:
                        ConfigOut(**raw)  # valida estrutura
                        self._profiles[name] = raw
                    except Exception:
                        logger.warning(f"Perfil inválido ignorado: '{name}'")
                logger.info(f"Perfis carregados: {list(self._profiles.keys())}")
        except Exception as exc:
            logger.warning(f"Erro ao carregar perfis de configuração: {exc}")


# Instância global
config_service = ConfigService()
