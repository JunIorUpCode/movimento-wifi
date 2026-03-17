#!/bin/bash
# Script para criar usuário administrador no auth_schema
# Uso: ./scripts/create-admin.sh [email] [senha]

EMAIL="${1:-admin@wifisense.com}"
PASSWORD="${2:-admin123}"

echo "=== Criando Usuário Administrador ==="
echo "Email: $EMAIL"
echo "Senha: $PASSWORD"
echo ""

# Gera hash bcrypt da senha usando Python
PASSWORD_HASH=$(python3 -c "
import bcrypt
password = '$PASSWORD'.encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hash = bcrypt.hashpw(password, salt).decode('utf-8')
print(hash)
")

echo "Hash gerado: $PASSWORD_HASH"
echo ""

# Insere usuário no banco
docker exec -i wifisense-postgres psql -U wifisense -d wifisense_saas <<EOF
-- Deletar admin existente se houver
DELETE FROM auth_schema.users WHERE email = '$EMAIL';

-- Criar novo admin
INSERT INTO auth_schema.users (id, email, password_hash, name, plan_type, status, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  '$EMAIL',
  '$PASSWORD_HASH',
  'Administrador',
  'premium',
  'active',
  NOW(),
  NOW()
);

-- Verificar criação
SELECT id, email, name, plan_type, status FROM auth_schema.users WHERE email = '$EMAIL';
EOF

echo ""
echo "✓ Usuário administrador criado com sucesso!"
echo ""
echo "Para fazer login:"
echo "curl -X POST http://localhost:8001/api/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}'"
