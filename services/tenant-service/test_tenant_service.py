# -*- coding: utf-8 -*-
"""
Testes básicos para tenant-service
Verifica funcionalidades principais do serviço
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Adiciona paths necessários
sys.path.insert(0, '.')
sys.path.insert(0, '../..')

from models.tenant import Tenant, PlanType, TenantStatus
from services.tenant_service import tenant_service
from shared.database import DatabaseManager


async def test_tenant_service():
    """Testa funcionalidades básicas do tenant service"""
    
    print("=== Teste do Tenant Service ===\n")
    
    # Inicializa database
    db_manager = DatabaseManager("tenant_schema")
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    
    print("✓ Database inicializado\n")
    
    try:
        # Teste 1: Criar tenant
        print("Teste 1: Criar tenant")
        async with db_manager.get_session() as session:
            tenant = await tenant_service.create_tenant(
                email=f"teste_{datetime.now().timestamp()}@example.com",
                name="Tenant Teste",
                plan_type=PlanType.BASIC,
                session=session
            )
            print(f"✓ Tenant criado: {tenant.email}")
            print(f"  - ID: {tenant.id}")
            print(f"  - Status: {tenant.status.value}")
            print(f"  - Trial ends: {tenant.trial_ends_at}")
            tenant_id = tenant.id
        
        # Teste 2: Buscar tenant por ID
        print("\nTeste 2: Buscar tenant por ID")
        async with db_manager.get_session() as session:
            found_tenant = await tenant_service.get_tenant_by_id(tenant_id, session)
            assert found_tenant is not None
            assert found_tenant.email == tenant.email
            print(f"✓ Tenant encontrado: {found_tenant.email}")
        
        # Teste 3: Listar tenants
        print("\nTeste 3: Listar tenants")
        async with db_manager.get_session() as session:
            tenants = await tenant_service.list_tenants(session, limit=10)
            count = await tenant_service.count_tenants(session)
            print(f"✓ Total de tenants: {count}")
            print(f"  - Listados: {len(tenants)}")
        
        # Teste 4: Atualizar tenant
        print("\nTeste 4: Atualizar tenant")
        async with db_manager.get_session() as session:
            updated = await tenant_service.update_tenant(
                tenant_id=tenant_id,
                session=session,
                name="Tenant Atualizado",
                plan_type=PlanType.PREMIUM
            )
            assert updated is not None
            assert updated.name == "Tenant Atualizado"
            assert updated.plan_type == PlanType.PREMIUM
            print(f"✓ Tenant atualizado")
            print(f"  - Nome: {updated.name}")
            print(f"  - Plano: {updated.plan_type.value}")
        
        # Teste 5: Suspender tenant
        print("\nTeste 5: Suspender tenant")
        async with db_manager.get_session() as session:
            suspended = await tenant_service.suspend_tenant(tenant_id, session)
            assert suspended is not None
            assert suspended.status == TenantStatus.SUSPENDED
            print(f"✓ Tenant suspenso")
            print(f"  - Status: {suspended.status.value}")
        
        # Teste 6: Ativar tenant
        print("\nTeste 6: Ativar tenant")
        async with db_manager.get_session() as session:
            activated = await tenant_service.activate_tenant(tenant_id, session)
            assert activated is not None
            assert activated.status == TenantStatus.ACTIVE
            print(f"✓ Tenant ativado")
            print(f"  - Status: {activated.status.value}")
        
        # Teste 7: Deletar tenant
        print("\nTeste 7: Deletar tenant")
        async with db_manager.get_session() as session:
            deleted = await tenant_service.delete_tenant(tenant_id, session)
            assert deleted is True
            print(f"✓ Tenant deletado")
        
        # Teste 8: Verificar que tenant foi deletado
        print("\nTeste 8: Verificar deleção")
        async with db_manager.get_session() as session:
            not_found = await tenant_service.get_tenant_by_id(tenant_id, session)
            assert not_found is None
            print(f"✓ Tenant não encontrado (deletado com sucesso)")
        
        print("\n=== Todos os testes passaram! ===")
    
    except Exception as e:
        print(f"\n✗ Erro nos testes: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_tenant_service())
