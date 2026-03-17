# -*- coding: utf-8 -*-
"""
Shared Config - Configuração Compartilhada
Gerencia variáveis de ambiente e configurações globais
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurações globais da aplicação
    Carrega valores de variáveis de ambiente ou arquivo .env
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
        description="Origens permitidas para CORS (separadas por vírgula)"
    )
    
    # Security
    ENCRYPTION_KEY: str = Field(
        default="change-me-32-byte-encryption-key",
        description="Chave para encriptação de dados sensíveis"
    )
    BCRYPT_ROUNDS: int = Field(
        default=12,
        description="Número de rounds do bcrypt"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        description="Limite de requisições por minuto"
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        description="Limite de requisições por hora"
    )
    
    # Stripe (Billing)
    STRIPE_API_KEY: str = Field(
        default="sk_test_change_me",
        description="Chave da API do Stripe para pagamentos"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        """Retorna URL de conexão do PostgreSQL"""
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
    
    @property
    def redis_url(self) -> str:
        """Retorna URL de conexão do Redis"""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def rabbitmq_url(self) -> str:
        """Retorna URL de conexão do RabbitMQ"""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"
        )


# Instância global de configurações
settings = Settings()
