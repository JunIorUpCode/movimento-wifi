#!/usr/bin/env python3
"""
Teste de Integração Simplificado
WiFiSense SaaS Multi-Tenant Platform
"""

import asyncio
import sys
import os

# Adicionar path do shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.config import settings
from shared.database import DatabaseManager

print("\n" + "="*60)
print("🧪 TESTE DE INTEGRAÇÃO SIMPLIFICADO")
print("WiFiSense SaaS Multi-Tenant Platform")
print("="*60)

async def test_infrastructure():
    """Teste 1: Infraestrutura"""
    print("\n" + "="*60)
    print("TESTE 1: INFRAESTRUTURA")
    print("="*60)
    
    # PostgreSQL
    print("\n📊 PostgreSQL:")
    try:
        db = DatabaseManager("auth_schema")
        await db.initialize()
        health = await db.health_check()
        if health:
            print("   ✅ Conectado")
            print(f"   📍 URL: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
        else:
            print("   ❌ Falha na conexão")
            return False
        await db.close()
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Redis
    print("\n🔴 Redis:")
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        result = await r.ping()
        if result:
            print("   ✅ Conectado")
            print(f"   📍 URL: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        await r.close()
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # RabbitMQ
    print("\n🐰 RabbitMQ:")
    try:
        import aio_pika
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        print("   ✅ Conectado")
        print(f"   📍 URL: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        await connection.close()
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    return True

async def test_schemas():
    """Teste 2: Schemas PostgreSQL"""
    print("\n" + "="*60)
    print("TESTE 2: SCHEMAS POSTGRESQL")
    print("="*60)
    
    try:
        db = DatabaseManager("public")
        await db.initialize()
        
        async with db.get_session() as session:
            result = await session.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE '%_schema'"
            )
            schemas = [row[0] for row in result.fetchall()]
            
            expected_schemas = [
                'auth_schema',
                'tenant_schema',
                'device_schema',
                'license_schema',
                'event_schema',
                'notification_schema',
                'billing_schema'
            ]
            
            print(f"\n📋 Schemas encontrados: {len(schemas)}")
            for schema in schemas:
                status = "✅" if schema in expected_schemas else "⚠️"
                print(f"   {status} {schema}")
            
            missing = set(expected_schemas) - set(schemas)
            if missing:
                print(f"\n⚠️  Schemas faltando: {', '.join(missing)}")
                return False
            
            print(f"\n✅ Todos os {len(expected_schemas)} schemas encontrados!")
            
        await db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bcrypt():
    """Teste 3: Bcrypt"""
    print("\n" + "="*60)
    print("TESTE 3: BCRYPT PASSWORD HASHING")
    print("="*60)
    
    try:
        import bcrypt
        
        password = "senha_teste_123"
        
        # Hash
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        print(f"\n🔐 Senha original: {password}")
        print(f"🔒 Hash gerado: {hashed.decode()[:50]}...")
        
        # Verificar
        if bcrypt.checkpw(password.encode('utf-8'), hashed):
            print("✅ Verificação de senha funcionando")
        else:
            print("❌ Verificação de senha falhou")
            return False
        
        # Verificar rounds
        if hashed.startswith(b'$2b$12$'):
            print("✅ Bcrypt usando 12 rounds (correto)")
        else:
            print("⚠️  Bcrypt não está usando 12 rounds")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_jwt():
    """Teste 4: JWT Tokens"""
    print("\n" + "="*60)
    print("TESTE 4: JWT TOKENS")
    print("="*60)
    
    try:
        import jwt
        from datetime import datetime, timedelta
        
        # Criar token
        payload = {
            "sub": "test-tenant-id",
            "email": "test@example.com",
            "role": "tenant",
            "plan": "basic",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        print(f"\n🎫 Token gerado: {token[:50]}...")
        
        # Decodificar
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        if decoded["sub"] == "test-tenant-id" and decoded["role"] == "tenant":
            print("✅ JWT: Geração e decodificação funcionando")
        else:
            print("❌ JWT: Payload incorreto")
            return False
        
        # Testar expiração
        expired_payload = payload.copy()
        expired_payload["exp"] = datetime.utcnow() - timedelta(seconds=1)
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        try:
            jwt.decode(expired_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            print("❌ JWT: Token expirado não foi rejeitado")
            return False
        except jwt.ExpiredSignatureError:
            print("✅ JWT: Expiração funcionando (24 horas)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_database_operations():
    """Teste 5: Operações de Banco de Dados"""
    print("\n" + "="*60)
    print("TESTE 5: OPERAÇÕES DE BANCO DE DADOS")
    print("="*60)
    
    try:
        # Criar schema de teste
        db = DatabaseManager("auth_schema")
        await db.initialize()
        await db.create_schema()
        print("\n✅ Schema criado/verificado")
        
        # Testar transação
        async with db.get_session() as session:
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            if row[0] == 1:
                print("✅ Query simples funcionando")
            else:
                print("❌ Query simples falhou")
                return False
        
        await db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Executar todos os testes"""
    
    results = {
        "infrastructure": False,
        "schemas": False,
        "bcrypt": False,
        "jwt": False,
        "database_operations": False
    }
    
    try:
        results["infrastructure"] = await test_infrastructure()
        
        if not results["infrastructure"]:
            print("\n❌ Infraestrutura falhou. Verifique se Docker está rodando.")
            print("   Execute: docker-compose up -d postgres redis rabbitmq")
            return False
        
        results["schemas"] = await test_schemas()
        results["bcrypt"] = await test_bcrypt()
        results["jwt"] = await test_jwt()
        results["database_operations"] = await test_database_operations()
        
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
    
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
        print("\n✅ Checkpoint Task 4: APROVADO")
        print("\n🚀 Próximo passo: Task 5 - License Service")
        return True
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
