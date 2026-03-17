# -*- coding: utf-8 -*-
"""
Testes de Propriedade e Unitários para Tenant Service

Properties:
  - 3.3: Property 5 — Tenant ID Uniqueness (IDs UUID nunca colidem)
  - 3.5: Property 6 — Suspended Tenant Blocking (suspend sempre define SUSPENDED)

Unit Tests:
  - 3.7: Cobertura completa do TenantService sem banco real

Implementa Tarefas 3.3, 3.5, 3.7 | Requisitos: 2.1–2.6
"""

import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
service_dir = os.path.abspath(os.path.dirname(__file__))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from hypothesis import given, strategies as st
from hypothesis import settings as h_settings


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_tenant(status=None, plan_type=None, email=None):
    """Instancia Tenant sem sessão de banco de dados."""
    from models.tenant import Tenant, TenantStatus, PlanType

    t = Tenant.__new__(Tenant)
    t.id = uuid4()
    t.email = email or f"test-{uuid4()}@example.com"
    t.name = "Tenant Teste"
    t.plan_type = plan_type or PlanType.BASIC
    t.status = status or TenantStatus.TRIAL
    t.trial_ends_at = datetime.utcnow() + timedelta(days=7)
    t.created_at = datetime.utcnow()
    t.updated_at = datetime.utcnow()
    t.language = "pt-BR"
    t.extra_metadata = {}
    return t


def _make_session(tenant_to_return=None, scalars_list=None):
    """
    Cria mock de AsyncSession.

    - scalar_one_or_none() → tenant_to_return
    - scalars().all()      → scalars_list or [tenant_to_return] or []
    - scalar_one()         → count (1 ou 0)
    """
    session = AsyncMock()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant_to_return
    if scalars_list is not None:
        result_mock.scalars.return_value.all.return_value = scalars_list
    else:
        result_mock.scalars.return_value.all.return_value = (
            [tenant_to_return] if tenant_to_return else []
        )
    result_mock.scalar_one.return_value = 1 if tenant_to_return else 0

    session.execute = AsyncMock(return_value=result_mock)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    return session


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── Property 5: Tenant ID Uniqueness (3.3) ──────────────────────────────────

class TestTenantIDUniqueness:
    """Property 5: Tenant IDs nunca colidem — Requisito 2.1"""

    @given(n=st.integers(min_value=2, max_value=100))
    @h_settings(max_examples=50)
    def test_property_n_tenant_instances_have_distinct_ids(self, n: int):
        """
        Property 5a: N instâncias de Tenant têm sempre N IDs distintos.

        O campo `id` usa `default=uuid.uuid4`, garantindo unicidade.
        """
        tenants = [_make_tenant() for _ in range(n)]
        ids = {t.id for t in tenants}
        assert len(ids) == n, f"Colisão de ID detectada em {n} instâncias!"

    @given(
        email_a=st.emails(),
        email_b=st.emails(),
    )
    @h_settings(max_examples=30)
    def test_property_two_tenants_always_have_different_ids(
        self, email_a: str, email_b: str
    ):
        """
        Property 5b: Dois tenants quaisquer têm sempre IDs distintos,
        independentemente do email.
        """
        t_a = _make_tenant(email=email_a)
        t_b = _make_tenant(email=email_b)
        assert t_a.id != t_b.id

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_value_error(self):
        """
        Property 5c: Criar tenant com email já cadastrado lança ValueError.
        Garante unicidade via validação no serviço.
        """
        from services.tenant_service import TenantService
        from models.tenant import PlanType

        service = TenantService()
        existing = _make_tenant(email="duplicado@example.com")
        session = _make_session(tenant_to_return=existing)

        with pytest.raises(ValueError, match="já está em uso"):
            await service.create_tenant(
                email="duplicado@example.com",
                name="Tenant Duplicado",
                plan_type=PlanType.BASIC,
                session=session,
            )

    @pytest.mark.asyncio
    async def test_new_tenant_gets_valid_uuid(self):
        """create_tenant retorna tenant com UUID válido e único."""
        from services.tenant_service import TenantService
        from models.tenant import PlanType

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        tenant = await service.create_tenant(
            email="new-unique@test.com",
            name="Novo Tenant",
            plan_type=PlanType.BASIC,
            session=session,
        )

        assert tenant is not None
        assert isinstance(tenant.id, UUID)
        assert tenant.id is not None


# ─── Property 6: Suspended Tenant Blocking (3.5) ─────────────────────────────

class TestSuspendedTenantBlocking:
    """Property 6: suspend_tenant sempre define SUSPENDED — Requisitos 2.4, 2.5"""

    @pytest.mark.asyncio
    async def test_property_suspend_sets_suspended_status(self):
        """Property 6a: suspend_tenant() define status=SUSPENDED sem exceção."""
        from services.tenant_service import TenantService
        from models.tenant import TenantStatus

        service = TenantService()
        tenant = _make_tenant(status=TenantStatus.ACTIVE)
        session = _make_session(tenant_to_return=tenant)

        result = await service.suspend_tenant(tenant.id, session)

        assert result is not None
        assert result.status == TenantStatus.SUSPENDED

    @given(
        initial_status=st.sampled_from(["trial", "active", "expired"])
    )
    @h_settings(max_examples=20)
    def test_property_suspend_works_from_any_initial_status(
        self, initial_status: str
    ):
        """
        Property 6b: Suspensão funciona independentemente do status inicial.
        """
        async def _inner():
            from services.tenant_service import TenantService
            from models.tenant import TenantStatus

            status_map = {
                "trial": TenantStatus.TRIAL,
                "active": TenantStatus.ACTIVE,
                "expired": TenantStatus.EXPIRED,
            }
            service = TenantService()
            tenant = _make_tenant(status=status_map[initial_status])
            session = _make_session(tenant_to_return=tenant)

            result = await service.suspend_tenant(tenant.id, session)

            assert result.status == TenantStatus.SUSPENDED

        _run(_inner())

    @pytest.mark.asyncio
    async def test_property_suspended_status_is_exclusive(self):
        """
        Property 6c: Após suspensão, o status é SUSPENDED e apenas SUSPENDED.
        Não pode ser ACTIVE, TRIAL ou EXPIRED ao mesmo tempo.
        """
        from services.tenant_service import TenantService
        from models.tenant import TenantStatus

        service = TenantService()
        tenant = _make_tenant(status=TenantStatus.ACTIVE)
        session = _make_session(tenant_to_return=tenant)

        result = await service.suspend_tenant(tenant.id, session)

        assert result.status == TenantStatus.SUSPENDED
        assert result.status != TenantStatus.ACTIVE
        assert result.status != TenantStatus.TRIAL
        assert result.status != TenantStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_suspend_nonexistent_tenant_returns_none(self):
        """Suspender tenant inexistente retorna None sem exceção."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        result = await service.suspend_tenant(uuid4(), session)

        assert result is None

    @pytest.mark.asyncio
    async def test_activate_restores_active_status(self):
        """Property 6d: activate_tenant() sempre define status=ACTIVE."""
        from services.tenant_service import TenantService
        from models.tenant import TenantStatus

        service = TenantService()
        tenant = _make_tenant(status=TenantStatus.SUSPENDED)
        session = _make_session(tenant_to_return=tenant)

        result = await service.activate_tenant(tenant.id, session)

        assert result is not None
        assert result.status == TenantStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_nonexistent_tenant_returns_none(self):
        """Ativar tenant inexistente retorna None sem exceção."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        result = await service.activate_tenant(uuid4(), session)

        assert result is None


# ─── Unit Tests: TenantService (3.7) ─────────────────────────────────────────

class TestTenantServiceUnit:
    """Testes unitários completos do TenantService — Tarefa 3.7"""

    @pytest.mark.asyncio
    async def test_create_tenant_default_status_is_trial(self):
        """Tenant criado em status TRIAL (período de trial de 7 dias)."""
        from services.tenant_service import TenantService
        from models.tenant import PlanType, TenantStatus

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        tenant = await service.create_tenant(
            email="trial@unit.com",
            name="Tenant Trial",
            plan_type=PlanType.BASIC,
            session=session,
        )

        assert tenant.status == TenantStatus.TRIAL

    @pytest.mark.asyncio
    async def test_create_tenant_trial_ends_in_7_days(self):
        """trial_ends_at é definido como ~7 dias a partir de agora."""
        from services.tenant_service import TenantService
        from models.tenant import PlanType

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        tenant = await service.create_tenant(
            email="trial-7days@unit.com",
            name="Tenant 7 Dias",
            plan_type=PlanType.PREMIUM,
            session=session,
        )

        diff = (tenant.trial_ends_at - datetime.utcnow()).days
        assert 6 <= diff <= 7, f"Esperado ~7 dias, got {diff} dias"

    @pytest.mark.asyncio
    async def test_create_tenant_saves_correct_plan(self):
        """create_tenant persiste o plan_type informado."""
        from services.tenant_service import TenantService
        from models.tenant import PlanType

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        tenant = await service.create_tenant(
            email="premium@unit.com",
            name="Premium Tenant",
            plan_type=PlanType.PREMIUM,
            session=session,
        )

        assert tenant.plan_type == PlanType.PREMIUM

    @pytest.mark.asyncio
    async def test_get_tenant_by_id_found(self):
        """get_tenant_by_id retorna o tenant correto quando encontrado."""
        from services.tenant_service import TenantService

        service = TenantService()
        existing = _make_tenant()
        session = _make_session(tenant_to_return=existing)

        result = await service.get_tenant_by_id(existing.id, session)

        assert result == existing

    @pytest.mark.asyncio
    async def test_get_tenant_by_id_not_found(self):
        """get_tenant_by_id retorna None quando tenant não existe."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        result = await service.get_tenant_by_id(uuid4(), session)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_tenant_by_email_found(self):
        """get_tenant_by_email retorna tenant quando email é encontrado."""
        from services.tenant_service import TenantService

        service = TenantService()
        existing = _make_tenant(email="found@unit.com")
        session = _make_session(tenant_to_return=existing)

        result = await service.get_tenant_by_email("found@unit.com", session)

        assert result == existing

    @pytest.mark.asyncio
    async def test_list_tenants_returns_list(self):
        """list_tenants retorna uma lista (possivelmente vazia)."""
        from services.tenant_service import TenantService

        service = TenantService()
        t = _make_tenant()
        session = _make_session(tenant_to_return=t, scalars_list=[t])

        result = await service.list_tenants(session, limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_tenant_name(self):
        """update_tenant atualiza o nome do tenant."""
        from services.tenant_service import TenantService

        service = TenantService()
        tenant = _make_tenant()
        session = _make_session(tenant_to_return=tenant)

        result = await service.update_tenant(
            tenant_id=tenant.id,
            session=session,
            name="Nome Atualizado",
        )

        assert result is not None
        assert result.name == "Nome Atualizado"

    @pytest.mark.asyncio
    async def test_update_tenant_plan(self):
        """update_tenant atualiza o plano do tenant."""
        from services.tenant_service import TenantService
        from models.tenant import PlanType

        service = TenantService()
        tenant = _make_tenant(plan_type=PlanType.BASIC)
        session = _make_session(tenant_to_return=tenant)

        result = await service.update_tenant(
            tenant_id=tenant.id,
            session=session,
            plan_type=PlanType.PREMIUM,
        )

        assert result.plan_type == PlanType.PREMIUM

    @pytest.mark.asyncio
    async def test_update_nonexistent_tenant_returns_none(self):
        """update_tenant retorna None para tenant inexistente."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        result = await service.update_tenant(uuid4(), session, name="Novo")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_tenant_returns_true(self):
        """delete_tenant retorna True quando bem-sucedido."""
        from services.tenant_service import TenantService

        service = TenantService()
        tenant = _make_tenant()
        session = _make_session(tenant_to_return=tenant)

        result = await service.delete_tenant(tenant.id, session)

        assert result is True
        session.delete.assert_called_once_with(tenant)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_tenant_returns_false(self):
        """delete_tenant retorna False para tenant inexistente."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = _make_session(tenant_to_return=None)

        result = await service.delete_tenant(uuid4(), session)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_expired_trials_updates_expired_tenants(self):
        """check_expired_trials marca tenants com trial vencido como EXPIRED."""
        from services.tenant_service import TenantService
        from models.tenant import TenantStatus

        service = TenantService()

        expired_tenant = _make_tenant(status=TenantStatus.TRIAL)
        expired_tenant.trial_ends_at = datetime.utcnow() - timedelta(days=1)

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [expired_tenant]
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()

        expired_list = await service.check_expired_trials(session)

        assert len(expired_list) == 1
        assert expired_list[0].status == TenantStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_check_expired_trials_with_no_expired(self):
        """check_expired_trials não altera nada quando não há trials vencidos."""
        from services.tenant_service import TenantService

        service = TenantService()

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        expired_list = await service.check_expired_trials(session)

        assert expired_list == []

    @pytest.mark.asyncio
    async def test_count_tenants_returns_integer(self):
        """count_tenants retorna um inteiro."""
        from services.tenant_service import TenantService

        service = TenantService()
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 42
        session.execute = AsyncMock(return_value=result_mock)

        count = await service.count_tenants(session)

        assert isinstance(count, int)
        assert count == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
