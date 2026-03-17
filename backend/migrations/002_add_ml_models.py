"""
Migração 002: Adiciona tabela ml_models para gerenciamento de modelos ML.

Esta migração cria a tabela para armazenar metadados de modelos ML treinados,
incluindo accuracy, número de amostras de treinamento, e status de ativação.

Implementa Requisitos 8.1, 8.2
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.database import engine


async def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    result = await conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = :table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


async def upgrade():
    """Cria tabela ml_models."""
    async with engine.begin() as conn:
        if not await table_exists(conn, "ml_models"):
            print("  Creating ml_models table...")
            await conn.execute(text("""
                CREATE TABLE ml_models (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    model_type VARCHAR(50) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    accuracy FLOAT,
                    training_samples INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT FALSE,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
            """))
            
            await conn.execute(text("""
                CREATE INDEX ix_ml_models_name ON ml_models (name)
            """))
            
            print("✓ Tabela ml_models criada com sucesso")
        else:
            print("  ml_models table already exists")


async def downgrade():
    """Remove tabela ml_models."""
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS ml_models"))
        print("✓ Tabela ml_models removida")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python 002_add_ml_models.py [upgrade|downgrade]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upgrade":
        asyncio.run(upgrade())
    elif command == "downgrade":
        asyncio.run(downgrade())
    else:
        print(f"Unknown command: {command}")
        print("Usage: python 002_add_ml_models.py [upgrade|downgrade]")
        sys.exit(1)
