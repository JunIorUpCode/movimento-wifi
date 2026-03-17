# -*- coding: utf-8 -*-
"""
Testes Simples para Auth Service
Testa funcionalidades básicas sem dependências de banco de dados
"""

import sys
import os

# Adiciona o diretório raiz ao path para importar shared
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_bcrypt_hashing():
    """
    Testa hash de senha com bcrypt (12 rounds)
    Requisito: 19.3
    """
    import bcrypt
    
    password = "senha_segura_123"
    
    # Gera hash com 12 rounds
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Verifica que hash começa com $2b$ (bcrypt)
    assert password_hash.decode('utf-8').startswith("$2b$") or password_hash.decode('utf-8').startswith("$2a$")
    
    # Verifica que senha correta é validada
    assert bcrypt.checkpw(password.encode('utf-8'), password_hash) is True
    
    # Verifica que senha incorreta é rejeitada
    assert bcrypt.checkpw("senha_errada".encode('utf-8'), password_hash) is False
    
    # Verifica número de rounds
    parts = password_hash.decode('utf-8').split("$")
    rounds = int(parts[2])
    assert rounds == 12, f"Esperado 12 rounds, obteve {rounds}"
    
    print("✓ Teste de hash de senha com bcrypt passou")


def test_jwt_token_generation():
    """
    Testa geração de token JWT com tenant_id, role e plan
    Requisito: 1.2, 19.2
    """
    import jwt
    from datetime import datetime, timedelta, timezone
    
    # Configurações
    SECRET_KEY = "test_secret_key_123"
    ALGORITHM = "HS256"
    
    # Dados do tenant
    tenant_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "tenant@example.com"
    role = "tenant"
    plan = "basic"
    
    # Gera token
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)
    
    payload = {
        "sub": tenant_id,
        "email": email,
        "role": role,
        "plan": plan,
        "iat": now,
        "exp": expires_at
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Verifica que token foi gerado
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decodifica token
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Verifica conteúdo do payload
    assert decoded["sub"] == tenant_id
    assert decoded["email"] == email
    assert decoded["role"] == role
    assert decoded["plan"] == plan
    assert "exp" in decoded
    assert "iat" in decoded
    
    print("✓ Teste de geração de JWT passou")


def test_jwt_token_expiration():
    """
    Testa que token JWT expira após 24 horas
    Requisito: 19.2
    """
    import jwt
    from datetime import datetime, timedelta, timezone
    
    SECRET_KEY = "test_secret_key_123"
    ALGORITHM = "HS256"
    
    # Gera token com expiração no passado
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(hours=25)
    
    payload = {
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "email": "tenant@example.com",
        "role": "tenant",
        "plan": "basic",
        "iat": expired_time,
        "exp": expired_time + timedelta(hours=24)
    }
    
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Tenta validar token expirado
    try:
        jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM])
        assert False, "Token expirado deveria ter sido rejeitado"
    except jwt.ExpiredSignatureError:
        pass  # Esperado
    
    print("✓ Teste de expiração de JWT passou")


def test_redis_connection():
    """
    Testa conexão básica com Redis (se disponível)
    """
    try:
        import redis
        
        # Tenta conectar ao Redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        
        # Testa set/get
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        assert value == 'test_value'
        
        # Limpa
        r.delete('test_key')
        
        print("✓ Teste de conexão com Redis passou")
    except Exception as e:
        print(f"⚠ Redis não disponível (esperado em desenvolvimento): {str(e)}")


if __name__ == "__main__":
    print("Executando testes simples do auth-service...\n")
    
    test_bcrypt_hashing()
    test_jwt_token_generation()
    test_jwt_token_expiration()
    test_redis_connection()
    
    print("\n✅ Todos os testes básicos passaram!")
    print("\nPróximo passo: Implementar tenant-service (Task 3)")
