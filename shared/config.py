# -*- coding: utf-8 -*-
"""
Shared Config - Configuração Compartilhada com suporte a YAML.

Além do carregamento via variáveis de ambiente / .env (pydantic-settings),
permite sobrescrever configurações a partir de um arquivo YAML.

Ordem de precedência (maior → menor):
  1. Variáveis de ambiente do SO
  2. Arquivo .env
  3. Arquivo YAML (CONFIG_FILE ou config.yaml)
  4. Valores default
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

# PyYAML é opcional — se não estiver instalado, suporte YAML é desativado
try:
    import yaml as _yaml  # type: ignore[import-untyped]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ── Carregamento de arquivo YAML ─────────────────────────────────────────────

def _load_yaml_config(path: str | Path) -> dict[str, Any]:
    """
    Carrega um arquivo YAML e retorna o conteúdo como dict.

    Args:
        path: Caminho para o arquivo YAML.

    Returns:
        Dict com as configurações ou {} se arquivo não existir/YAML indisponível.
    """
    if not _YAML_AVAILABLE:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        data = _yaml.safe_load(f) or {}
    return {k.upper(): v for k, v in data.items()} if isinstance(data, dict) else {}


# ── Modelo de configurações ──────────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Configurações globais da aplicação.

    Carrega em ordem: variáveis de ambiente → .env → YAML → defaults.
    O arquivo YAML é especificado pela variável CONFIG_FILE (default: config.yaml).
    """

    # Database
    DATABASE_HOST: str = Field(default="localhost", description="Host do PostgreSQL")
    DATABASE_PORT: int = Field(default=5432, description="Porta do PostgreSQL")
    DATABASE_USER: str = Field(default="wifisense", description="Usuário do banco")
    DATABASE_PASSWORD: str = Field(default="wifisense_password", description="Senha do banco")
    DATABASE_NAME: str = Field(default="wifisense_saas", description="Nome do banco")

    # Redis
    REDIS_HOST: str = Field(default="localhost", description="Host do Redis")
    REDIS_PORT: int = Field(default=6379, description="Porta do Redis")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Senha do Redis")
    REDIS_DB: int = Field(default=0, description="Database do Redis")

    # RabbitMQ
    RABBITMQ_HOST: str = Field(default="localhost", description="Host do RabbitMQ")
    RABBITMQ_PORT: int = Field(default=5672, description="Porta do RabbitMQ")
    RABBITMQ_USER: str = Field(default="wifisense", description="Usuário do RabbitMQ")
    RABBITMQ_PASSWORD: str = Field(default="wifisense_password", description="Senha do RabbitMQ")
    RABBITMQ_VHOST: str = Field(default="/", description="Virtual host do RabbitMQ")

    # JWT
    JWT_SECRET_KEY: str = Field(default="change-me-in-production", description="Chave secreta para JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo de assinatura JWT")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="Expiração do token em horas")

    # Application
    APP_NAME: str = Field(default="WiFiSense SaaS", description="Nome da aplicação")
    APP_VERSION: str = Field(default="1.0.0", description="Versão da aplicação")
    DEBUG: bool = Field(default=False, description="Modo debug")
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Origens CORS permitidas (separadas por vírgula)",
    )

    # Security
    ENCRYPTION_KEY: str = Field(
        default="change-me-32-byte-encryption-key",
        description="Chave para encriptação de dados sensíveis (Fernet base64)",
    )
    BCRYPT_ROUNDS: int = Field(default=12, description="Rounds do bcrypt")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Limite de req/minuto")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Limite de req/hora")

    # Stripe (Billing)
    STRIPE_API_KEY: str = Field(
        default="sk_test_change_me",
        description="Chave da API do Stripe",
    )

    # ── Propriedades derivadas ────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de origens CORS."""
        if isinstance(self.CORS_ORIGINS, str):
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return list(self.CORS_ORIGINS)

    @property
    def database_url(self) -> str:
        """URL asyncpg para SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def redis_url(self) -> str:
        """URL de conexão Redis."""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def rabbitmq_url(self) -> str:
        """URL de conexão RabbitMQ (AMQP)."""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# ── Fábrica com suporte a YAML ────────────────────────────────────────────────

def _create_settings() -> Settings:
    """
    Cria instância de Settings aplicando overrides do arquivo YAML (se existir).

    O arquivo YAML é lido de:
    1. Variável de ambiente CONFIG_FILE
    2. Arquivo `config.yaml` no diretório de trabalho atual
    """
    yaml_path = os.environ.get("CONFIG_FILE", "config.yaml")
    yaml_overrides = _load_yaml_config(yaml_path)

    if yaml_overrides:
        # Aplica apenas os campos que não foram definidos via env var / .env
        # (env vars têm precedência; só sobrescreve se o campo ainda está no default)
        tmp = Settings()
        init_kwargs: dict[str, Any] = {}
        for field_name, yaml_value in yaml_overrides.items():
            if field_name in Settings.model_fields:
                env_var = os.environ.get(field_name)
                if env_var is None:  # variável de ambiente não definida → usa YAML
                    init_kwargs[field_name] = yaml_value
        return Settings(**init_kwargs) if init_kwargs else tmp

    return Settings()


def load_yaml_override(path: str | Path) -> Settings:
    """
    Cria uma nova instância de Settings com overrides do arquivo YAML informado.

    Útil para testes ou ambientes que usam arquivos de configuração diferentes.

    Args:
        path: Caminho para o arquivo YAML de configuração.

    Returns:
        Settings com valores do YAML sobrescrevendo os defaults.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se YAML não estiver disponível (PyYAML não instalado).
    """
    if not _YAML_AVAILABLE:
        raise ValueError(
            "PyYAML não está instalado. Instale com: pip install pyyaml"
        )
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")

    yaml_overrides = _load_yaml_config(config_path)
    valid_overrides = {
        k: v for k, v in yaml_overrides.items()
        if k in Settings.model_fields
    }
    return Settings(**valid_overrides)


# ── Instância global ──────────────────────────────────────────────────────────

settings = _create_settings()
