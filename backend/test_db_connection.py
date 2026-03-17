"""
Script de teste para validar conexão com PostgreSQL
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

# Carregar variáveis de ambiente
load_dotenv()

async def test_connection():
    """Testa a conexão com o PostgreSQL"""
    try:
        # Obter credenciais
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        print("=" * 60)
        print("TESTE DE CONEXÃO COM POSTGRESQL")
        print("=" * 60)
        print(f"Host: {db_host}")
        print(f"Porta: {db_port}")
        print(f"Banco: {db_name}")
        print(f"Usuário: {db_user}")
        print(f"Senha: {'*' * len(db_password)} ({len(db_password)} caracteres)")
        print("=" * 60)
        
        # Tentar conectar
        print("\n[1/3] Conectando ao PostgreSQL...")
        conn = await asyncpg.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("✓ Conexão estabelecida com sucesso!")
        
        # Verificar versão do PostgreSQL
        print("\n[2/3] Verificando versão do PostgreSQL...")
        version = await conn.fetchval('SELECT version()')
        print(f"✓ Versão: {version.split(',')[0]}")
        
        # Listar tabelas existentes
        print("\n[3/3] Listando tabelas no banco de dados...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"✓ Encontradas {len(tables)} tabelas:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table['table_name']}")
        else:
            print("⚠ Nenhuma tabela encontrada no banco de dados")
            print("  Execute o script setup_postgresql.sql para criar as tabelas")
        
        # Fechar conexão
        await conn.close()
        print("\n" + "=" * 60)
        print("✓ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        
        return True
        
    except asyncpg.InvalidPasswordError:
        print("\n✗ ERRO: Senha incorreta")
        print("  Verifique a senha no arquivo .env")
        return False
        
    except asyncpg.InvalidCatalogNameError:
        print(f"\n✗ ERRO: Banco de dados '{db_name}' não existe")
        print("  Crie o banco de dados com: CREATE DATABASE wifi_movimento;")
        return False
        
    except Exception as e:
        print(f"\n✗ ERRO: {type(e).__name__}")
        print(f"  Detalhes: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
