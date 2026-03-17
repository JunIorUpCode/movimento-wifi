#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar usuário administrador
Uso: python scripts/create-admin.py [email] [senha]
"""

import sys
import asyncio
import bcrypt
from datetime import datetime

# Adiciona paths necessários
sys.path.insert(0, '.')

from shared.database import DatabaseManager
from services.auth-service.models.user import User, PlanType, TenantStatus


async def create_admin(email: str, password: str):
    """Cria usuário administrador"""
    
    print("=== Criando Usuário Administrador ===")
    print(f"Email: {email}")
    print(f"Senha: {password}")
    print("")
    
    # Inicializa database
    db_manager = DatabaseManager("auth_schema")
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    
    try:
        # Gera hash da senha
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        print(f"Hash gerado: {password_hash[:50]}...")
        print("")
        
        async with db_manager.get_session() as session:
            # Verifica se admin já existe
            from sqlalchemy import select, delete
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⚠ Admin já existe. Deletando...")
                await session.execute(
                    delete(User).where(User.email == email)
                )
                await session.commit()
            
            # Cria novo admin
            admin = User(
                email=email,
                password_hash=password_hash,
                name="Administrador",
                plan_type=PlanType.PREMIUM,
                status=TenantStatus.ACTIVE,
                trial_ends_at=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            
            print("✓ Usuário administrador criado com sucesso!")
            print("")
            print(f"ID: {admin.id}")
            print(f"Email: {admin.email}")
            print(f"Nome: {admin.name}")
            print(f"Plano: {admin.plan_type.value}")
            print(f"Status: {admin.status.value}")
            print("")
            print("Para fazer login:")
            print(f'curl -X POST http://localhost:8001/api/auth/login \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"email": "{email}", "password": "{password}"}}\'')
    
    except Exception as e:
        print(f"✗ Erro ao criar admin: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.close()


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@wifisense.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    
    asyncio.run(create_admin(email, password))
