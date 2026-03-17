# -*- coding: utf-8 -*-
"""
Testes de Propriedade para JWT Service
Usa Hypothesis para validar propriedades do sistema de JWT
"""

import pytest
import jwt
import time
from hypothesis import given, strategies as st, settings
from services.jwt_service import JWTService


# Estratégias do Hypothesis para gerar dados de teste
tenant_id_strategy = st.uuids().map(str)
email_strategy = st.emails()
role_strategy = st.sampled_from(["tenant", "admin"])
plan_strategy = st.sampled_from(["basic", "premium"])


class TestJWTProperties:
    """
    Testes de propriedade para validar comportamento do JWT Service
    """
    
    @given(
        tenant_id=tenant_id_strategy,
        email=email_strategy,
        role=role_strategy,
        plan=plan_strategy
    )
    @settings(max_examples=100)  # Limita número de exemplos para performance
    def test_property_jwt_token_contains_tenant_id(
        self,
        tenant_id: str,
        email: str,
        role: str,
        plan: str
    ):
        """
        Property 1: JWT Token Contains Tenant ID
        
        Valida: Requisitos 1.2
        
        Propriedade: Para qualquer tenant_id válido, o token JWT gerado
        deve conter exatamente o mesmo tenant_id quando decodificado.
        
        Esta propriedade garante que o isolamento multi-tenant funciona
        corretamente, pois cada token carrega a identidade do tenant.
        """
        # Arrange
        jwt_service = JWTService()
        
        # Act - Gera token JWT
        token = jwt_service.generate_jwt_token(
            tenant_id=tenant_id,
            email=email,
            role=role,
            plan=plan
        )
        
        # Pequeno delay para evitar problemas de timing com iat
        time.sleep(0.01)
        
        # Assert - Decodifica token diretamente (sem validação de tempo)
        # Isso evita problemas de timing em testes de propriedade
        payload = jwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": True, "verify_iat": False}  # Desabilita verificação de iat
        )
        
        # Propriedade: tenant_id no payload deve ser idêntico ao original
        assert payload["sub"] == tenant_id, \
            f"Tenant ID no token ({payload['sub']}) difere do original ({tenant_id})"
        
        # Validações adicionais para garantir integridade do token
        assert payload["email"] == email, \
            f"Email no token ({payload['email']}) difere do original ({email})"
        assert payload["role"] == role, \
            f"Role no token ({payload['role']}) difere do original ({role})"
        assert payload["plan"] == plan, \
            f"Plan no token ({payload['plan']}) difere do original ({plan})"
        assert "exp" in payload, "Token deve conter campo 'exp' (expiration)"
        assert "iat" in payload, "Token deve conter campo 'iat' (issued at)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
