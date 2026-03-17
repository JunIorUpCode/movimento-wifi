#!/usr/bin/env python3
"""
Script para criar schemas SaaS no banco wifi_movimento LOCAL
WiFiSense SaaS Multi-Tenant Platform
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

print("\n" + "="*60)
print("🔧 CRIANDO SCHEMAS SAAS NO BANCO LOCAL")
print("="*60)

# Configurações do banco (do backend/.env)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'wifi_movimento',
    'user': 'postgres',
    'password': 'NovaSenhaForte123!'
}

print(f"\n📊 Conectando ao banco de dados...")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Porta: {DB_CONFIG['port']}")
print(f"   Banco: {DB_CONFIG['database']}")
print(f"   Usuário: {DB_CONFIG['user']}")

try:
    # Conectar ao banco
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    print("✅ Conectado com sucesso!")
    print()
    
    # Habilitar extensões
    print("🔌 Habilitando extensões...")
    cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    cursor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    print("✅ Extensões habilitadas")
    print()
    
    # Criar schemas
    schemas = [
        ('auth_schema', 'Schema para autenticação e autorização (auth-service)'),
        ('tenant_schema', 'Schema para gerenciamento de tenants (tenant-service)'),
        ('device_schema', 'Schema para gerenciamento de dispositivos (device-service)'),
        ('license_schema', 'Schema para sistema de licenciamento (license-service)'),
        ('event_schema', 'Schema para processamento de eventos (event-service)'),
        ('notification_schema', 'Schema para notificações multi-canal (notification-service)'),
        ('billing_schema', 'Schema para faturamento e pagamentos (billing-service)')
    ]
    
    print("📋 Criando schemas SaaS...")
    for schema_name, description in schemas:
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')
        cursor.execute(f"COMMENT ON SCHEMA {schema_name} IS '{description}';")
        print(f"   ✅ {schema_name}")
    
    print()
    print("🔐 Configurando permissões...")
    
    # Dar permissões ao usuário postgres
    for schema_name, _ in schemas:
        cursor.execute(f'GRANT ALL PRIVILEGES ON SCHEMA {schema_name} TO postgres;')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL ON TABLES TO postgres;')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL ON SEQUENCES TO postgres;')
    
    print("✅ Permissões configuradas")
    print()
    
    # Verificar schemas criados
    print("📊 Verificando schemas criados...")
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE '%_schema'
        ORDER BY schema_name;
    """)
    
    created_schemas = cursor.fetchall()
    print(f"\n✅ {len(created_schemas)} schemas SaaS encontrados:")
    for (schema,) in created_schemas:
        print(f"   ✅ {schema}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*60)
    print("🎉 SCHEMAS CRIADOS COM SUCESSO!")
    print("="*60)
    print()
    print("Próximos passos:")
    print("1. ✅ Schemas criados no banco wifi_movimento")
    print("2. 🚀 Executar: python scripts/test-integration-simple.py")
    print()
    
except psycopg2.Error as e:
    print()
    print("❌ Erro ao conectar/criar schemas:")
    print(f"   {e}")
    print()
    print("Verifique:")
    print("1. PostgreSQL está rodando")
    print("2. Credenciais estão corretas")
    print("3. Banco wifi_movimento existe")
    print()
    exit(1)
    
except Exception as e:
    print()
    print(f"❌ Erro inesperado: {e}")
    print()
    exit(1)
