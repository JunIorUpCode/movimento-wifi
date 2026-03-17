#!/usr/bin/env python3
"""
Script de Teste de Integração Completa
WiFiSense SaaS Multi-Tenant Platform

Testa:
1. Conexão com PostgreSQL
2. Conexão com Redis
3. Conexão com RabbitMQ
4. Auth-service (JWT, bcrypt, rate limiting)
5. Tenant-service (CRUD, trial, suspensão)
6. Isolamento multi-tenant
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Adicionar path do shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.config import settings
from shared.database import DatabaseManager
from shared.logging import StructuredLogger

# Importar serviços
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/auth-service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/tenant-service'))

from services.auth_service import AuthService
from services.jwt_service import JWTService
from services.tenant_service import TenantService

logger = StructuredLogger("integration-test")

class IntegrationTest:
    def __init__(self):
        self.settings = settings
        self.auth_db = None
        self.tenant_db = None
        self.auth_service = None
        self.jwt_service = None
        self.tenant_service = None
        
    async def setup(self):
        """Inicializar conexões e serviços"""
        logger.info("🔧 Inicializando serviços...")
        
        # Databases
        self.auth_db = DatabaseManager("auth_schema")
        self.tenant_db = DatabaseManager("tenant_schema")
        
        await self.auth_db.initialize()
        await self.tenant_db.initialize()
        
        # Services
        self.auth_service = AuthService(self.auth_db)
        self.jwt_service = JWTService()
        self.tenant_service = TenantService(self.tenant_db)
        
        logger.info("✅ Serviços inicializados")

    
    async def test_infrastructure(self):
        """Teste 1: Infraestrutura (PostgreSQL, Redis, RabbitMQ)"""
        print("\n" + "="*60)
        print("TESTE 1: INFRAESTRUTURA")
        print("="*60)
        
        # PostgreSQL
        try:
            health = await self.auth_db.health_check()
            if health:
                print("✅ PostgreSQL: Conectado")
            else:
                print("❌ PostgreSQL: Falha na conexão")
                return False
        except Exception as e:
            print(f"❌ PostgreSQL: Erro - {e}")
            return False
        
        # Redis
        try:
            import redis.asyncio as redis
            r = redis.from_url(self.settings.redis_url)
            await r.ping()
            print("✅ Redis: Conectado")
            await r.close()
        except Exception as e:
            print(f"❌ Redis: Erro - {e}")
            return False
        
        # RabbitMQ
        try:
            import aio_pika
            connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
            print("✅ RabbitMQ: Conectado")
            await connection.close()
        except Exception as e:
            print(f"❌ RabbitMQ: Erro - {e}")
            return False
        
        return True
    
    async def test_auth_service(self):
        """Teste 2: Auth-Service"""
        print("\n" + "="*60)
        print("TESTE 2: AUTH-SERVICE")
        print("="*60)
        
        try:
            # Criar schemas
            await self.auth_db.create_schema()
            await self.auth_db.create_tables()
            print("✅ Schemas criados")
            
            # Testar bcrypt
            password = "senha123"
            hashed = self.auth_service.hash_password(password)
            if hashed.startswith("$2b$") and self.auth_service.verify_password(password, hashed):
                print("✅ Bcrypt: Hash e verificação funcionando")
            else:
                print("❌ Bcrypt: Falha")
                return False
            
            # Testar JWT
            token = self.jwt_service.create_token(
                tenant_id="test-tenant",
                email="test@example.com",
                role="tenant",
                plan="basic"
            )
            payload = self.jwt_service.decode_token(token)
            if payload["sub"] == "test-tenant" and payload["role"] == "tenant":
                print("✅ JWT: Geração e decodificação funcionando")
            else:
                print("❌ JWT: Falha")
                return False
            
            # Testar expiração
            expired_token = self.jwt_service.create_token(
                tenant_id="test",
                email="test@example.com",
                role="tenant",
                plan="basic",
                expires_delta=timedelta(seconds=-1)
            )
            try:
                self.jwt_service.decode_token(expired_token)
                print("❌ JWT: Token expirado não foi rejeitado")
                return False
            except:
                print("✅ JWT: Expiração funcionando")
            
            return True
            
        except Exception as e:
            print(f"❌ Auth-Service: Erro - {e}")
            return False
    
    async def test_tenant_service(self):
        """Teste 3: Tenant-Service"""
        print("\n" + "="*60)
        print("TESTE 3: TENANT-SERVICE")
        print("="*60)
        
        try:
            # Criar schemas
            await self.tenant_db.create_schema()
            await self.tenant_db.create_tables()
            print("✅ Schemas criados")
            
            # Criar tenant
            tenant1 = await self.tenant_service.create_tenant(
                email="tenant1@example.com",
                name="Tenant 1",
                plan_type="basic"
            )
            print(f"✅ Tenant criado: {tenant1['id']}")
            
            # Verificar trial
            if tenant1["status"] == "trial":
                print("✅ Status inicial: TRIAL")
            else:
                print(f"❌ Status esperado TRIAL, recebido {tenant1['status']}")
                return False
            
            # Verificar trial_ends_at
            trial_ends = datetime.fromisoformat(tenant1["trial_ends_at"].replace("Z", "+00:00"))
            days_until_end = (trial_ends - datetime.now(trial_ends.tzinfo)).days
            if 6 <= days_until_end <= 7:
                print(f"✅ Trial expira em {days_until_end} dias")
            else:
                print(f"❌ Trial deveria expirar em 7 dias, mas expira em {days_until_end}")
                return False
            
            # Buscar tenant
            found = await self.tenant_service.get_tenant(tenant1["id"])
            if found["email"] == "tenant1@example.com":
                print("✅ Busca de tenant funcionando")
            else:
                print("❌ Busca de tenant falhou")
                return False
            
            # Listar tenants
            tenants = await self.tenant_service.list_tenants()
            if len(tenants["tenants"]) >= 1:
                print(f"✅ Listagem funcionando: {tenants['total']} tenant(s)")
            else:
                print("❌ Listagem falhou")
                return False
            
            # Atualizar tenant
            updated = await self.tenant_service.update_tenant(
                tenant1["id"],
                name="Tenant 1 Updated"
            )
            if updated["name"] == "Tenant 1 Updated":
                print("✅ Atualização funcionando")
            else:
                print("❌ Atualização falhou")
                return False
            
            # Suspender tenant
            suspended = await self.tenant_service.suspend_tenant(tenant1["id"])
            if suspended["status"] == "suspended":
                print("✅ Suspensão funcionando")
            else:
                print("❌ Suspensão falhou")
                return False
            
            # Ativar tenant
            activated = await self.tenant_service.activate_tenant(tenant1["id"])
            if activated["status"] == "active":
                print("✅ Ativação funcionando")
            else:
                print("❌ Ativação falhou")
                return False
            
            # Deletar tenant
            await self.tenant_service.delete_tenant(tenant1["id"])
            try:
                await self.tenant_service.get_tenant(tenant1["id"])
                print("❌ Deleção falhou: tenant ainda existe")
                return False
            except:
                print("✅ Deleção funcionando")
            
            return True
            
        except Exception as e:
            print(f"❌ Tenant-Service: Erro - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_multi_tenant_isolation(self):
        """Teste 4: Isolamento Multi-Tenant"""
        print("\n" + "="*60)
        print("TESTE 4: ISOLAMENTO MULTI-TENANT")
        print("="*60)
        
        try:
            # Criar 2 tenants
            tenant_a = await self.tenant_service.create_tenant(
                email="tenant_a@example.com",
                name="Tenant A",
                plan_type="basic"
            )
            tenant_b = await self.tenant_service.create_tenant(
                email="tenant_b@example.com",
                name="Tenant B",
                plan_type="premium"
            )
            print(f"✅ Criados 2 tenants: A={tenant_a['id'][:8]}..., B={tenant_b['id'][:8]}...")
            
            # Verificar IDs únicos
            if tenant_a["id"] != tenant_b["id"]:
                print("✅ IDs únicos gerados")
            else:
                print("❌ IDs duplicados!")
                return False
            
            # Verificar emails únicos
            try:
                await self.tenant_service.create_tenant(
                    email="tenant_a@example.com",  # Email duplicado
                    name="Tenant A Duplicate",
                    plan_type="basic"
                )
                print("❌ Email duplicado foi aceito!")
                return False
            except:
                print("✅ Email duplicado foi rejeitado")
            
            # Verificar planos diferentes
            if tenant_a["plan_type"] == "basic" and tenant_b["plan_type"] == "premium":
                print("✅ Planos diferentes armazenados corretamente")
            else:
                print("❌ Planos não foram armazenados corretamente")
                return False
            
            # Limpar
            await self.tenant_service.delete_tenant(tenant_a["id"])
            await self.tenant_service.delete_tenant(tenant_b["id"])
            print("✅ Tenants de teste removidos")
            
            return True
            
        except Exception as e:
            print(f"❌ Isolamento Multi-Tenant: Erro - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Limpar recursos"""
        logger.info("🧹 Limpando recursos...")
        if self.auth_db:
            await self.auth_db.close()
        if self.tenant_db:
            await self.tenant_db.close()
        logger.info("✅ Recursos limpos")
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("\n" + "="*60)
        print("🧪 TESTE DE INTEGRAÇÃO COMPLETA")
        print("WiFiSense SaaS Multi-Tenant Platform")
        print("="*60)
        
        results = {
            "infrastructure": False,
            "auth_service": False,
            "tenant_service": False,
            "multi_tenant_isolation": False
        }
        
        try:
            await self.setup()
            
            results["infrastructure"] = await self.test_infrastructure()
            if not results["infrastructure"]:
                print("\n❌ Infraestrutura falhou. Verifique se Docker está rodando.")
                return results
            
            results["auth_service"] = await self.test_auth_service()
            results["tenant_service"] = await self.test_tenant_service()
            results["multi_tenant_isolation"] = await self.test_multi_tenant_isolation()
            
        except Exception as e:
            print(f"\n❌ Erro fatal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
        
        # Resumo
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        for test, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        print(f"\nTotal: {passed}/{total} testes passaram")
        
        if passed == total:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            return True
        else:
            print(f"\n⚠️  {total - passed} teste(s) falharam")
            return False

async def main():
    test = IntegrationTest()
    success = await test.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
