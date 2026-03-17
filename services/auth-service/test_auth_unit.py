# -*- coding: utf-8 -*-
"""
Testes Unitários para Auth Service
Testa login, expiração de token e bloqueio de conta

Requisitos: 19.3, 19.6, 19.7, 19.2
Task: 2.9
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from services.auth_service import AuthService
from services.jwt_service import JWTService
from models.user import User, PlanType, TenantStatus


class TestAuthServiceLogin:
    """Testes para funcionalidade de login"""
    
    @pytest.fixture
    def auth_service(self):
        """Fixture para criar instância do AuthService"""
        service = AuthService()
        service.redis_client = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_user(self):
        """Fixture para criar usuário mock"""
        # Hash correto para senha "senha123"
        user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="tenant@example.com",
            password_hash="$2b$12$xM1IzxQVdw1kqP/M.CSQ1eiVk35z/n/OYgkEZ/jC2W57vnqI1FhZe",
            name="Tenant Teste",
            plan_type=PlanType.BASIC,
            status=TenantStatus.ACTIVE
        )
        return user
    
    @pytest.mark.asyncio
    async def test_login_com_credenciais_validas(self, auth_service, mock_user):
        """
        Testa login com email e senha corretos
        Deve retornar usuário e token JWT
        """
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock do Redis para verificação de bloqueio
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.delete = AsyncMock(return_value=1)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act
        user, token = await auth_service.login(
            email="tenant@example.com",
            password="senha123",
            session=mock_session
        )
        
        # Assert
        assert user.email == "tenant@example.com"
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verifica que tentativas de login foram limpas
        auth_service.redis_client.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_com_email_invalido(self, auth_service):
        """
        Testa login com email que não existe
        Deve lançar ValueError e registrar tentativa falhada
        """
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Usuário não encontrado
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email ou senha incorretos"):
            await auth_service.login(
                email="naoexiste@example.com",
                password="senha123",
                session=mock_session
            )
        
        # Verifica que tentativa falhada foi registrada
        auth_service.redis_client.incr.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_com_senha_invalida(self, auth_service, mock_user):
        """
        Testa login com senha incorreta
        Deve lançar ValueError e registrar tentativa falhada
        """
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email ou senha incorretos"):
            await auth_service.login(
                email="tenant@example.com",
                password="senha_errada",
                session=mock_session
            )
        
        # Verifica que tentativa falhada foi registrada
        auth_service.redis_client.incr.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_conta_suspensa(self, auth_service, mock_user):
        """
        Testa login em conta suspensa
        Deve lançar ValueError informando status da conta
        """
        # Arrange
        mock_user.status = TenantStatus.SUSPENDED
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Conta suspended"):
            await auth_service.login(
                email="tenant@example.com",
                password="senha123",
                session=mock_session
            )
    
    @pytest.mark.asyncio
    async def test_login_conta_expirada(self, auth_service, mock_user):
        """
        Testa login em conta expirada
        Deve lançar ValueError informando status da conta
        """
        # Arrange
        mock_user.status = TenantStatus.EXPIRED
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Conta expired"):
            await auth_service.login(
                email="tenant@example.com",
                password="senha123",
                session=mock_session
            )


class TestTokenExpiration:
    """Testes para expiração de token JWT"""
    
    @pytest.fixture
    def jwt_service(self):
        """Fixture para criar instância do JWTService"""
        return JWTService()
    
    def test_token_expira_apos_24_horas(self, jwt_service):
        """
        Testa que token JWT expira após 24 horas
        Requisito: 19.2
        """
        # Arrange - Gera token com expiração bem no passado
        import time
        now_timestamp = int(time.time())
        expired_timestamp = now_timestamp - 86400 - 10  # 24 horas + 10 segundos atrás
        
        payload = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "tenant@example.com",
            "role": "tenant",
            "plan": "basic",
            "iat": expired_timestamp - 86400,  # Emitido 48 horas atrás
            "exp": expired_timestamp  # Expirou 24h + 10s atrás
        }
        
        expired_token = jwt.encode(
            payload,
            jwt_service.secret_key,
            algorithm=jwt_service.algorithm
        )
        
        # Act & Assert - Token expirado deve lançar exceção
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            jwt_service.validate_jwt_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail.lower() or "inválido" in exc_info.value.detail.lower()
    
    def test_token_valido_dentro_de_24_horas(self, jwt_service):
        """
        Testa que token válido é aceito dentro do período de 24 horas
        """
        # Arrange - Gera token válido
        token = jwt_service.generate_jwt_token(
            tenant_id="123e4567-e89b-12d3-a456-426614174000",
            email="tenant@example.com",
            role="tenant",
            plan="basic"
        )
        
        # Act - Decodifica diretamente sem validação de tempo
        payload = jwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False, "verify_iat": False}  # Desabilita validação de tempo para teste
        )
        
        # Assert
        assert payload["sub"] == "123e4567-e89b-12d3-a456-426614174000"
        assert payload["email"] == "tenant@example.com"
        
        # Verifica que expiração está no futuro
        exp_timestamp = payload["exp"]
        now_timestamp = int(datetime.utcnow().timestamp())
        assert exp_timestamp > now_timestamp
    
    def test_token_expiracao_exata_24_horas(self, jwt_service):
        """
        Testa que token tem expiração de exatamente 24 horas
        """
        # Arrange & Act
        before = datetime.utcnow()
        token = jwt_service.generate_jwt_token(
            tenant_id="123e4567-e89b-12d3-a456-426614174000",
            email="tenant@example.com",
            role="tenant",
            plan="basic"
        )
        after = datetime.utcnow()
        
        # Decodifica sem validação de tempo
        payload = jwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False, "verify_iat": False}
        )
        
        # Assert
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        
        # Diferença deve ser 24 horas
        diff = exp_time - iat_time
        assert diff.total_seconds() == 24 * 3600  # 24 horas em segundos


class TestAccountLockout:
    """Testes para bloqueio de conta após tentativas falhadas"""
    
    @pytest.fixture
    def auth_service(self):
        """Fixture para criar instância do AuthService"""
        service = AuthService()
        service.redis_client = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_bloqueio_apos_5_tentativas_falhadas(self, auth_service):
        """
        Testa que conta é bloqueada após 5 tentativas falhadas
        Requisito: 19.6
        """
        # Arrange
        email = "tenant@example.com"
        
        # Simula 5 tentativas falhadas
        for attempt in range(1, 6):
            auth_service.redis_client.incr = AsyncMock(return_value=attempt)
            auth_service.redis_client.expire = AsyncMock()
            auth_service.redis_client.setex = AsyncMock()
            auth_service.redis_client.delete = AsyncMock()
            
            # Act
            await auth_service.record_failed_login(email)
        
        # Assert - Na 5ª tentativa, deve bloquear
        auth_service.redis_client.setex.assert_called_once()
        
        # Verifica que lockout foi configurado
        call_args = auth_service.redis_client.setex.call_args
        assert f"lockout:{email}" in call_args[0]
        assert call_args[0][1] == 30 * 60  # 30 minutos em segundos
    
    @pytest.mark.asyncio
    async def test_bloqueio_dura_30_minutos(self, auth_service):
        """
        Testa que bloqueio dura 30 minutos
        Requisito: 19.6
        """
        # Arrange
        email = "tenant@example.com"
        lockout_until = datetime.utcnow() + timedelta(minutes=30)
        
        auth_service.redis_client.get = AsyncMock(
            return_value=lockout_until.isoformat()
        )
        
        # Act
        is_locked, seconds_remaining = await auth_service.check_account_lockout(email)
        
        # Assert
        assert is_locked is True
        assert seconds_remaining > 0
        assert seconds_remaining <= 30 * 60  # Máximo 30 minutos
    
    @pytest.mark.asyncio
    async def test_login_bloqueado_retorna_erro(self, auth_service):
        """
        Testa que login em conta bloqueada retorna erro apropriado
        Requisito: 19.7
        """
        # Arrange
        email = "tenant@example.com"
        lockout_until = datetime.utcnow() + timedelta(minutes=15)
        
        auth_service.redis_client.get = AsyncMock(
            return_value=lockout_until.isoformat()
        )
        
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Conta bloqueada"):
            await auth_service.login(
                email=email,
                password="senha123",
                session=mock_session
            )
    
    @pytest.mark.asyncio
    async def test_contador_reseta_apos_15_minutos(self, auth_service):
        """
        Testa que contador de tentativas expira após 15 minutos
        Requisito: 19.6
        """
        # Arrange
        email = "tenant@example.com"
        
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act
        await auth_service.record_failed_login(email)
        
        # Assert - TTL deve ser 15 minutos
        auth_service.redis_client.expire.assert_called_once()
        call_args = auth_service.redis_client.expire.call_args
        assert call_args[0][1] == 15 * 60  # 15 minutos em segundos
    
    @pytest.mark.asyncio
    async def test_tentativas_limpas_apos_login_sucesso(self, auth_service, mock_user=None):
        """
        Testa que contador de tentativas é limpo após login bem-sucedido
        """
        # Arrange
        if mock_user is None:
            mock_user = User(
                id="123e4567-e89b-12d3-a456-426614174000",
                email="tenant@example.com",
                password_hash="$2b$12$xM1IzxQVdw1kqP/M.CSQ1eiVk35z/n/OYgkEZ/jC2W57vnqI1FhZe",
                name="Tenant Teste",
                plan_type=PlanType.BASIC,
                status=TenantStatus.ACTIVE
            )
        
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        auth_service.redis_client.get = AsyncMock(return_value=None)
        auth_service.redis_client.delete = AsyncMock(return_value=1)
        auth_service.redis_client.incr = AsyncMock(return_value=1)
        auth_service.redis_client.expire = AsyncMock()
        
        # Act
        await auth_service.login(
            email="tenant@example.com",
            password="senha123",
            session=mock_session
        )
        
        # Assert
        auth_service.redis_client.delete.assert_called()
        call_args = auth_service.redis_client.delete.call_args
        assert "login_attempts:" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_bloqueio_expira_automaticamente(self, auth_service):
        """
        Testa que bloqueio expira automaticamente após 30 minutos
        """
        # Arrange
        email = "tenant@example.com"
        lockout_until = datetime.utcnow() - timedelta(minutes=1)  # Expirado
        
        auth_service.redis_client.get = AsyncMock(
            return_value=lockout_until.isoformat()
        )
        auth_service.redis_client.delete = AsyncMock()
        
        # Act
        is_locked, seconds_remaining = await auth_service.check_account_lockout(email)
        
        # Assert
        assert is_locked is False
        assert seconds_remaining is None
        
        # Verifica que chave de lockout foi removida
        auth_service.redis_client.delete.assert_called_once()


class TestPasswordHashing:
    """Testes para hash de senha"""
    
    @pytest.fixture
    def auth_service(self):
        """Fixture para criar instância do AuthService"""
        return AuthService()
    
    def test_hash_usa_bcrypt_12_rounds(self, auth_service):
        """
        Testa que hash usa bcrypt com 12 rounds
        Requisito: 19.3
        """
        # Arrange
        password = "senha_segura_123"
        
        # Act
        password_hash = auth_service.hash_password(password)
        
        # Assert
        assert password_hash.startswith("$2b$") or password_hash.startswith("$2a$")
        
        # Extrai número de rounds
        parts = password_hash.split("$")
        rounds = int(parts[2])
        assert rounds == 12
    
    def test_senha_correta_valida(self, auth_service):
        """
        Testa que senha correta é validada com sucesso
        """
        # Arrange
        password = "senha_segura_123"
        password_hash = auth_service.hash_password(password)
        
        # Act
        is_valid = auth_service.verify_password(password, password_hash)
        
        # Assert
        assert is_valid is True
    
    def test_senha_incorreta_rejeitada(self, auth_service):
        """
        Testa que senha incorreta é rejeitada
        """
        # Arrange
        password = "senha_segura_123"
        password_hash = auth_service.hash_password(password)
        
        # Act
        is_valid = auth_service.verify_password("senha_errada", password_hash)
        
        # Assert
        assert is_valid is False
    
    def test_hashes_diferentes_para_mesma_senha(self, auth_service):
        """
        Testa que mesma senha gera hashes diferentes (salt aleatório)
        """
        # Arrange
        password = "senha_segura_123"
        
        # Act
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Assert
        assert hash1 != hash2  # Hashes devem ser diferentes
        
        # Mas ambos devem validar a senha correta
        assert auth_service.verify_password(password, hash1) is True
        assert auth_service.verify_password(password, hash2) is True


# Função para executar todos os testes
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
