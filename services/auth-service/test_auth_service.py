# -*- coding: utf-8 -*-
"""
Testes para Auth Service
Valida funcionalidades de autenticação, JWT e rate limiting
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Testes unitários básicos para validar a implementação


def test_password_hashing():
    """
    Testa hash de senha com bcrypt (12 rounds)
    Requisito: 19.3
    """
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    password = "senha_segura_123"
    
    # Gera hash
    password_hash = auth_service.hash_password(password)
    
    # Verifica que hash começa com $2b$ (bcrypt)
    assert password_hash.startswith("$2b$") or password_hash.startswith("$2a$")
    
    # Verifica que senha correta é validada
    assert auth_service.verify_password(password, password_hash) is True
    
    # Verifica que senha incorreta é rejeitada
    assert auth_service.verify_password("senha_errada", password_hash) is False
    
    print("✓ Teste de hash de senha passou")


def test_jwt_token_generation():
    """
    Testa geração de token JWT com tenant_id, role e plan
    Requisito: 1.2, 19.2
    """
    from services.jwt_service import JWTService
    
    jwt_service = JWTService()
    
    # Gera token
    token = jwt_service.generate_jwt_token(
        tenant_id="123e4567-e89b-12d3-a456-426614174000",
        email="tenant@example.com",
        role="tenant",
        plan="basic"
    )
    
    # Verifica que token foi gerado
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decodifica token
    payload = jwt_service.validate_jwt_token(token)
    
    # Verifica conteúdo do payload
    assert payload["sub"] == "123e4567-e89b-12d3-a456-426614174000"
    assert payload["email"] == "tenant@example.com"
    assert payload["role"] == "tenant"
    assert payload["plan"] == "basic"
    assert "exp" in payload
    assert "iat" in payload
    
    print("✓ Teste de geração de JWT passou")


def test_jwt_token_expiration():
    """
    Testa que token JWT expira após 24 horas
    Requisito: 19.2
    """
    from services.jwt_service import JWTService
    import jwt
    from fastapi import HTTPException
    
    jwt_service_instance = JWTService()
    
    # Gera token com expiração no passado (simulação)
    now = datetime.utcnow()
    expired_time = now - timedelta(hours=25)
    
    payload = {
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "email": "tenant@example.com",
        "role": "tenant",
        "plan": "basic",
        "iat": int(expired_time.timestamp()),
        "exp": int((expired_time + timedelta(hours=24)).timestamp())
    }
    
    expired_token = jwt.encode(
        payload,
        jwt_service_instance.secret_key,
        algorithm=jwt_service_instance.algorithm
    )
    
    # Tenta validar token expirado
    try:
        jwt_service_instance.validate_jwt_token(expired_token)
        assert False, "Token expirado deveria ter sido rejeitado"
    except HTTPException as e:
        assert e.status_code == 401
        assert "expirado" in e.detail.lower()
    
    print("✓ Teste de expiração de JWT passou")


def test_bcrypt_rounds():
    """
    Verifica que bcrypt usa 12 rounds conforme requisito
    Requisito: 19.3
    """
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    password = "test_password"
    
    # Gera hash
    password_hash = auth_service.hash_password(password)
    
    # Extrai número de rounds do hash
    # Formato bcrypt: $2b$12$...
    parts = password_hash.split("$")
    rounds = int(parts[2])
    
    # Verifica que usa 12 rounds
    assert rounds == 12, f"Esperado 12 rounds, obteve {rounds}"
    
    print("✓ Teste de rounds do bcrypt passou")


if __name__ == "__main__":
    print("Executando testes do auth-service...\n")
    
    test_password_hashing()
    test_jwt_token_generation()
    test_jwt_token_expiration()
    test_bcrypt_rounds()
    
    print("\n✅ Todos os testes passaram!")
