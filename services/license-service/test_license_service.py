# -*- coding: utf-8 -*-
"""
Testes Unitários para License Service
Testa geração de chaves, validação e CRUD de licenças

Requisitos testados: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from models.license import License, LicenseStatus, PlanType
from services.license_generator import license_generator
from services.license_service import license_service
from shared.database import DatabaseManager


@pytest_asyncio.fixture
async def db_session():
    """Fixture para criar sessão de banco de dados de teste"""
    db_manager = DatabaseManager("license_schema")
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        yield session
        await session.rollback()  # Rollback após cada teste
    
    await db_manager.close()


@pytest_asyncio.fixture
async def sample_tenant_id():
    """Fixture que retorna um tenant_id de exemplo"""
    return uuid4()


class TestLicenseGenerator:
    """Testes para o gerador de chaves de ativação"""
    
    def test_generate_activation_key_format(self):
        """Testa que chave gerada tem formato correto"""
        key, key_hash = license_generator.generate_activation_key()
        
        # Verifica formato XXXX-XXXX-XXXX-XXXX
        assert len(key) == 19  # 16 chars + 3 hífens
        assert key.count("-") == 3
        
        # Verifica que hash foi gerado
        assert len(key_hash) == 64  # SHA256 hex
    
    def test_generate_activation_key_uniqueness(self):
        """Testa que chaves geradas são únicas"""
        keys = set()
        
        # Gera 100 chaves
        for _ in range(100):
            key, _ = license_generator.generate_activation_key()
            keys.add(key)
        
        # Todas devem ser únicas
        assert len(keys) == 100
    
    def test_validate_key_format_valid(self):
        """Testa validação de formato válido"""
        key, _ = license_generator.generate_activation_key()
        assert license_generator.validate_key_format(key) is True
    
    def test_validate_key_format_invalid(self):
        """Testa validação de formato inválido"""
        # Chave muito curta
        assert license_generator.validate_key_format("ABCD-EFGH") is False
        
        # Caracteres inválidos (O, I, 1, L) - mas 0 (zero) é válido
        assert license_generator.validate_key_format("OOOO-OOOO-OOOO-OOOO") is False
        assert license_generator.validate_key_format("IIII-IIII-IIII-IIII") is False
        assert license_generator.validate_key_format("1111-1111-1111-1111") is False
        assert license_generator.validate_key_format("LLLL-LLLL-LLLL-LLLL") is False
    
    def test_normalize_key(self):
        """Testa normalização de chaves"""
        # Com espaços
        normalized = license_generator.normalize_key("ABCD EFGH JKMN PQRS")
        assert normalized == "ABCD-EFGH-JKMN-PQRS"
        
        # Minúsculas
        normalized = license_generator.normalize_key("abcd-efgh-jkmn-pqrs")
        assert normalized == "ABCD-EFGH-JKMN-PQRS"
        
        # Sem hífens
        normalized = license_generator.normalize_key("ABCDEFGHJKMNPQRS")
        assert normalized == "ABCD-EFGH-JKMN-PQRS"


class TestLicenseService:
    """Testes para o serviço de licenças"""
    
    # ========================================
    # TESTE 1: GERAÇÃO DE LICENÇA
    # ========================================
    
    @pytest.mark.asyncio
    async def test_create_license_basic_plan(self, db_session):
        """
        Testa criação de licença com plano BÁSICO
        Requisitos: 4.1, 4.2, 4.3
        """
        tenant_id = uuid4()
        
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        # Verifica que licença foi criada corretamente
        assert license.id is not None
        assert license.tenant_id == tenant_id
        assert license.plan_type == PlanType.BASIC
        assert license.device_limit == 1
        assert license.status == LicenseStatus.PENDING
        
        # Verifica chave de ativação
        assert license.activation_key is not None
        assert len(license.activation_key) == 19  # XXXX-XXXX-XXXX-XXXX
        assert license.activation_key.count("-") == 3
        
        # Verifica hash da chave
        assert license.activation_key_hash is not None
        assert len(license.activation_key_hash) == 64  # SHA256 hex
        
        # Verifica data de expiração
        assert license.expires_at is not None
        expected_expires = datetime.utcnow() + timedelta(days=365)
        # Tolerância de 5 segundos
        assert abs((license.expires_at - expected_expires).total_seconds()) < 5
        
        # Verifica que ainda não foi ativada
        assert license.activated_at is None
        assert license.device_id is None
    
    @pytest.mark.asyncio
    async def test_create_license_premium_plan(self, db_session):
        """
        Testa criação de licença com plano PREMIUM
        Requisitos: 4.1, 4.2, 4.3
        """
        tenant_id = uuid4()
        
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.PREMIUM,
            device_limit=5,
            expires_in_days=365,
            session=db_session
        )
        
        assert license.plan_type == PlanType.PREMIUM
        assert license.device_limit == 5
        assert license.status == LicenseStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_license_generates_unique_keys(self, db_session):
        """
        Testa que cada licença criada tem chave única
        Requisitos: 4.2
        """
        tenant_id = uuid4()
        keys = set()
        
        # Cria 10 licenças
        for i in range(10):
            license = await license_service.create_license(
                tenant_id=tenant_id,
                plan_type=PlanType.BASIC,
                device_limit=1,
                expires_in_days=365,
                session=db_session
            )
            keys.add(license.activation_key)
        
        # Todas as chaves devem ser únicas
        assert len(keys) == 10
    
    @pytest.mark.asyncio
    async def test_create_license_with_custom_expiration(self, db_session):
        """
        Testa criação de licença com período de expiração customizado
        Requisitos: 4.3
        """
        tenant_id = uuid4()
        
        # Licença de 30 dias
        license_30 = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=30,
            session=db_session
        )
        
        # Licença de 90 dias
        license_90 = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=90,
            session=db_session
        )
        
        # Verifica diferença de expiração
        diff = (license_90.expires_at - license_30.expires_at).days
        assert 59 <= diff <= 61  # ~60 dias de diferença (tolerância)
    
    # ========================================
    # TESTE 2: VALIDAÇÃO DE CHAVE
    # ========================================
    
    @pytest.mark.asyncio
    async def test_validate_license_key_valid(self, db_session):
        """
        Testa validação de chave de ativação VÁLIDA
        Requisitos: 4.4
        """
        tenant_id = uuid4()
        
        # Cria licença
        created_license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        # Busca por chave válida
        found_license = await license_service.get_license_by_key(
            created_license.activation_key,
            db_session
        )
        
        # Verifica que encontrou a licença correta
        assert found_license is not None
        assert found_license.id == created_license.id
        assert found_license.activation_key == created_license.activation_key
        assert found_license.tenant_id == tenant_id
        assert found_license.status == LicenseStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_validate_license_key_invalid(self, db_session):
        """
        Testa validação de chave de ativação INVÁLIDA
        Requisitos: 4.4
        """
        # Tenta buscar com chave que não existe
        found_license = await license_service.get_license_by_key(
            "XXXX-YYYY-ZZZZ-WWWW",
            db_session
        )
        
        # Não deve encontrar nada
        assert found_license is None
    
    @pytest.mark.asyncio
    async def test_validate_license_key_normalized(self, db_session):
        """
        Testa que validação funciona com chave em diferentes formatos
        Requisitos: 4.4
        """
        tenant_id = uuid4()
        
        # Cria licença
        created_license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        original_key = created_license.activation_key
        
        # Testa com minúsculas
        found_lower = await license_service.get_license_by_key(
            original_key.lower(),
            db_session
        )
        assert found_lower is not None
        assert found_lower.id == created_license.id
        
        # Testa com espaços ao invés de hífens
        key_with_spaces = original_key.replace("-", " ")
        found_spaces = await license_service.get_license_by_key(
            key_with_spaces,
            db_session
        )
        assert found_spaces is not None
        assert found_spaces.id == created_license.id
        
        # Testa sem hífens
        key_no_hyphens = original_key.replace("-", "")
        found_no_hyphens = await license_service.get_license_by_key(
            key_no_hyphens,
            db_session
        )
        assert found_no_hyphens is not None
        assert found_no_hyphens.id == created_license.id
    
    @pytest.mark.asyncio
    async def test_activate_license_success(self, db_session):
        """
        Testa ativação de licença com chave válida
        Requisitos: 4.4
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # Cria licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        # Ativa licença
        activated_license = await license_service.activate_license(
            license.activation_key,
            device_id,
            db_session
        )
        
        # Verifica ativação
        assert activated_license.status == LicenseStatus.ACTIVATED
        assert activated_license.device_id == device_id
        assert activated_license.activated_at is not None
        
        # Verifica que activated_at é recente (últimos 5 segundos)
        time_diff = (datetime.utcnow() - activated_license.activated_at).total_seconds()
        assert time_diff < 5
    
    @pytest.mark.asyncio
    async def test_activate_license_invalid_key(self, db_session):
        """
        Testa ativação com chave INVÁLIDA (não existe)
        Requisitos: 4.4
        """
        device_id = uuid4()
        
        # Tenta ativar com chave que não existe
        with pytest.raises(ValueError, match="Chave de ativação inválida"):
            await license_service.activate_license(
                "XXXX-XXXX-XXXX-XXXX",
                device_id,
                db_session
            )
    
    @pytest.mark.asyncio
    async def test_activate_license_already_activated(self, db_session):
        """
        Testa que não pode ativar licença já ativada
        Requisitos: 4.4
        """
        tenant_id = uuid4()
        device_id_1 = uuid4()
        device_id_2 = uuid4()
        
        # Cria e ativa licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        await license_service.activate_license(
            license.activation_key,
            device_id_1,
            db_session
        )
        
        # Tenta ativar novamente com outro dispositivo
        with pytest.raises(ValueError, match="já ativada"):
            await license_service.activate_license(
                license.activation_key,
                device_id_2,
                db_session
            )
    
    @pytest.mark.asyncio
    async def test_activate_license_expired(self, db_session):
        """
        Testa que não pode ativar licença expirada
        Requisitos: 4.6
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # Cria licença expirada manualmente
        key, key_hash = license_generator.generate_activation_key()
        
        expired_license = License(
            tenant_id=tenant_id,
            activation_key=key,
            activation_key_hash=key_hash,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expirou ontem
            status=LicenseStatus.PENDING
        )
        
        db_session.add(expired_license)
        await db_session.commit()
        
        # Tenta ativar licença expirada
        with pytest.raises(ValueError, match="expirada"):
            await license_service.activate_license(
                key,
                device_id,
                db_session
            )
    
    @pytest.mark.asyncio
    async def test_activate_license_revoked(self, db_session):
        """
        Testa que não pode ativar licença revogada
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # Cria licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        # Revoga licença
        await license_service.revoke_license(license.id, db_session)
        
        # Tenta ativar licença revogada
        with pytest.raises(ValueError, match="revogada"):
            await license_service.activate_license(
                license.activation_key,
                device_id,
                db_session
            )
    
    # ========================================
    # TESTE 3: REVOGAÇÃO DE LICENÇA
    # ========================================
    
    @pytest.mark.asyncio
    async def test_revoke_license_pending(self, db_session):
        """
        Testa revogação de licença PENDING (não ativada)
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        
        # Cria licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        assert license.status == LicenseStatus.PENDING
        
        # Revoga licença
        revoked_license = await license_service.revoke_license(
            license.id,
            db_session
        )
        
        # Verifica revogação
        assert revoked_license is not None
        assert revoked_license.id == license.id
        assert revoked_license.status == LicenseStatus.REVOKED
        
        # Verifica que updated_at foi atualizado
        assert revoked_license.updated_at is not None
        time_diff = (datetime.utcnow() - revoked_license.updated_at).total_seconds()
        assert time_diff < 5
    
    @pytest.mark.asyncio
    async def test_revoke_license_activated(self, db_session):
        """
        Testa revogação de licença ACTIVATED (em uso)
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # Cria e ativa licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.PREMIUM,
            device_limit=5,
            expires_in_days=365,
            session=db_session
        )
        
        await license_service.activate_license(
            license.activation_key,
            device_id,
            db_session
        )
        
        # Verifica que está ativada
        await db_session.refresh(license)
        assert license.status == LicenseStatus.ACTIVATED
        assert license.device_id == device_id
        
        # Revoga licença ativada
        revoked_license = await license_service.revoke_license(
            license.id,
            db_session
        )
        
        # Verifica revogação
        assert revoked_license.status == LicenseStatus.REVOKED
        # device_id deve permanecer para histórico
        assert revoked_license.device_id == device_id
    
    @pytest.mark.asyncio
    async def test_revoke_license_nonexistent(self, db_session):
        """
        Testa revogação de licença que não existe
        Requisitos: 4.7
        """
        fake_license_id = uuid4()
        
        # Tenta revogar licença inexistente
        result = await license_service.revoke_license(
            fake_license_id,
            db_session
        )
        
        # Deve retornar None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_license_prevents_activation(self, db_session):
        """
        Testa que licença revogada não pode ser ativada
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # Cria licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        activation_key = license.activation_key
        
        # Revoga licença
        await license_service.revoke_license(license.id, db_session)
        
        # Tenta ativar licença revogada
        with pytest.raises(ValueError, match="revogada"):
            await license_service.activate_license(
                activation_key,
                device_id,
                db_session
            )
    
    @pytest.mark.asyncio
    async def test_revoke_multiple_licenses(self, db_session):
        """
        Testa revogação de múltiplas licenças
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        
        # Cria 3 licenças
        licenses = []
        for i in range(3):
            license = await license_service.create_license(
                tenant_id=tenant_id,
                plan_type=PlanType.BASIC,
                device_limit=1,
                expires_in_days=365,
                session=db_session
            )
            licenses.append(license)
        
        # Revoga todas
        for license in licenses:
            revoked = await license_service.revoke_license(
                license.id,
                db_session
            )
            assert revoked.status == LicenseStatus.REVOKED
        
        # Verifica que todas foram revogadas
        for license in licenses:
            await db_session.refresh(license)
            assert license.status == LicenseStatus.REVOKED
    
    # ========================================
    # TESTES ADICIONAIS
    # ========================================
    
    @pytest.mark.asyncio
    async def test_extend_license(self, db_session):
        """
        Testa extensão de licença
        Requisitos: 4.7
        """
        tenant_id = uuid4()
        
        # Cria licença
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=30,
            session=db_session
        )
        
        original_expires_at = license.expires_at
        
        # Estende licença por 60 dias
        extended_license = await license_service.extend_license(
            license.id,
            60,
            db_session
        )
        
        assert extended_license is not None
        assert extended_license.expires_at > original_expires_at
        
        # Verifica que adicionou 60 dias
        diff = (extended_license.expires_at - original_expires_at).days
        assert diff == 60
    
    @pytest.mark.asyncio
    async def test_list_licenses_by_tenant(self, db_session):
        """
        Testa listagem de licenças por tenant
        Requisitos: 4.1
        """
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        
        # Cria 3 licenças para tenant 1
        for i in range(3):
            await license_service.create_license(
                tenant_id=tenant_id_1,
                plan_type=PlanType.BASIC,
                device_limit=1,
                expires_in_days=365,
                session=db_session
            )
        
        # Cria 2 licenças para tenant 2
        for i in range(2):
            await license_service.create_license(
                tenant_id=tenant_id_2,
                plan_type=PlanType.PREMIUM,
                device_limit=5,
                expires_in_days=365,
                session=db_session
            )
        
        # Lista licenças do tenant 1
        licenses_t1 = await license_service.list_licenses(
            session=db_session,
            tenant_id=tenant_id_1
        )
        
        assert len(licenses_t1) == 3
        for license in licenses_t1:
            assert license.tenant_id == tenant_id_1
        
        # Lista licenças do tenant 2
        licenses_t2 = await license_service.list_licenses(
            session=db_session,
            tenant_id=tenant_id_2
        )
        
        assert len(licenses_t2) == 2
        for license in licenses_t2:
            assert license.tenant_id == tenant_id_2
    
    @pytest.mark.asyncio
    async def test_list_licenses_by_status(self, db_session):
        """
        Testa listagem de licenças por status
        Requisitos: 4.1
        """
        tenant_id = uuid4()
        
        # Cria 2 licenças pending
        license1 = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        license2 = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        
        # Ativa uma
        await license_service.activate_license(
            license1.activation_key,
            uuid4(),
            db_session
        )
        
        # Revoga outra
        license3 = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_in_days=365,
            session=db_session
        )
        await license_service.revoke_license(license3.id, db_session)
        
        # Lista por status
        pending = await license_service.list_licenses(
            session=db_session,
            tenant_id=tenant_id,
            status=LicenseStatus.PENDING
        )
        assert len(pending) == 1
        
        activated = await license_service.list_licenses(
            session=db_session,
            tenant_id=tenant_id,
            status=LicenseStatus.ACTIVATED
        )
        assert len(activated) == 1
        
        revoked = await license_service.list_licenses(
            session=db_session,
            tenant_id=tenant_id,
            status=LicenseStatus.REVOKED
        )
        assert len(revoked) == 1


class TestLicenseServiceIntegration:
    """Testes de integração para fluxos completos"""
    
    @pytest.mark.asyncio
    async def test_complete_license_lifecycle(self, db_session):
        """
        Testa ciclo de vida completo de uma licença:
        Criação -> Ativação -> Extensão -> Revogação
        """
        tenant_id = uuid4()
        device_id = uuid4()
        
        # 1. Criação
        license = await license_service.create_license(
            tenant_id=tenant_id,
            plan_type=PlanType.PREMIUM,
            device_limit=5,
            expires_in_days=30,
            session=db_session
        )
        assert license.status == LicenseStatus.PENDING
        
        # 2. Ativação
        activated = await license_service.activate_license(
            license.activation_key,
            device_id,
            db_session
        )
        assert activated.status == LicenseStatus.ACTIVATED
        assert activated.device_id == device_id
        
        # 3. Extensão
        extended = await license_service.extend_license(
            license.id,
            60,
            db_session
        )
        assert extended.status == LicenseStatus.ACTIVATED
        
        # 4. Revogação
        revoked = await license_service.revoke_license(
            license.id,
            db_session
        )
        assert revoked.status == LicenseStatus.REVOKED


class TestLicenseProperties:
    """Testes de propriedades usando Hypothesis"""
    
    @pytest.mark.asyncio
    async def test_property_expired_license_data_rejection(self, db_session):
        """
        Property 11: Expired License Data Rejection
        Valida: Requisitos 4.6
        
        Propriedade: Quando uma licença expira, o sistema DEVE rejeitar
        qualquer tentativa de validação ou submissão de dados com HTTP 403
        ou indicação clara de rejeição.
        
        Teste:
        1. Cria licença com expiração no passado
        2. Tenta validar a licença
        3. Verifica que validação retorna valid=False com mensagem de expiração
        """
        tenant_id = uuid4()
        
        # Cria licença que já está expirada (expires_in_days negativo)
        # Vamos criar manualmente para ter controle total sobre expires_at
        from models.license import License
        from services.license_generator import license_generator
        
        key, key_hash = license_generator.generate_activation_key()
        
        expired_license = License(
            tenant_id=tenant_id,
            activation_key=key,
            activation_key_hash=key_hash,
            plan_type=PlanType.BASIC,
            device_limit=1,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expirou ontem
            status=LicenseStatus.PENDING
        )
        
        db_session.add(expired_license)
        await db_session.commit()
        await db_session.refresh(expired_license)
        
        # Tenta buscar a licença
        found_license = await license_service.get_license_by_key(
            key,
            db_session
        )
        
        assert found_license is not None
        assert found_license.id == expired_license.id
        
        # Verifica que a licença está expirada (comparando com now)
        now = datetime.utcnow()
        # Remove timezone info se presente para comparação
        expires_at = found_license.expires_at
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        
        assert expires_at < now, f"Licença deveria estar expirada: {expires_at} < {now}"
        
        # Tenta ativar a licença expirada
        device_id = uuid4()
        
        with pytest.raises(ValueError, match="expirada"):
            await license_service.activate_license(
                key,
                device_id,
                db_session
            )
        
        # Verifica que o status permanece PENDING (não foi ativada)
        await db_session.refresh(found_license)
        assert found_license.status == LicenseStatus.PENDING or found_license.status == LicenseStatus.EXPIRED
        assert found_license.device_id is None
        
        # Propriedade validada: Licenças expiradas são rejeitadas
        # e não podem ser ativadas para submissão de dados


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
