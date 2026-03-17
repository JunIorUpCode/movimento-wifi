#!/bin/bash
# Script de teste para endpoints do tenant-service
# Requer: curl, jq (opcional para formatação JSON)

BASE_URL="http://localhost:8002"
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJwbGFuIjoicHJlbWl1bSIsImV4cCI6OTk5OTk5OTk5OX0.PLACEHOLDER"

echo "=== Teste de Endpoints do Tenant Service ==="
echo ""

# Health Check
echo "1. Health Check"
curl -s "$BASE_URL/health" | jq '.' || curl -s "$BASE_URL/health"
echo -e "\n"

# Criar Tenant
echo "2. Criar Tenant"
TENANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/tenants" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "name": "Tenant Teste",
    "plan_type": "basic"
  }')

echo "$TENANT_RESPONSE" | jq '.' || echo "$TENANT_RESPONSE"
TENANT_ID=$(echo "$TENANT_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")
echo -e "\n"

if [ -z "$TENANT_ID" ] || [ "$TENANT_ID" = "null" ]; then
  echo "Erro ao criar tenant. Verifique se o serviço está rodando e o token é válido."
  exit 1
fi

# Listar Tenants
echo "3. Listar Tenants"
curl -s "$BASE_URL/api/admin/tenants" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.' || curl -s "$BASE_URL/api/admin/tenants" -H "Authorization: Bearer $ADMIN_TOKEN"
echo -e "\n"

# Obter Detalhes do Tenant
echo "4. Obter Detalhes do Tenant"
curl -s "$BASE_URL/api/admin/tenants/$TENANT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.' || curl -s "$BASE_URL/api/admin/tenants/$TENANT_ID" -H "Authorization: Bearer $ADMIN_TOKEN"
echo -e "\n"

# Atualizar Tenant
echo "5. Atualizar Tenant"
curl -s -X PUT "$BASE_URL/api/admin/tenants/$TENANT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tenant Atualizado",
    "plan_type": "premium"
  }' | jq '.' || curl -s -X PUT "$BASE_URL/api/admin/tenants/$TENANT_ID" -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{"name": "Tenant Atualizado", "plan_type": "premium"}'
echo -e "\n"

# Suspender Tenant
echo "6. Suspender Tenant"
curl -s -X POST "$BASE_URL/api/admin/tenants/$TENANT_ID/suspend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.' || curl -s -X POST "$BASE_URL/api/admin/tenants/$TENANT_ID/suspend" -H "Authorization: Bearer $ADMIN_TOKEN"
echo -e "\n"

# Ativar Tenant
echo "7. Ativar Tenant"
curl -s -X POST "$BASE_URL/api/admin/tenants/$TENANT_ID/activate" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.' || curl -s -X POST "$BASE_URL/api/admin/tenants/$TENANT_ID/activate" -H "Authorization: Bearer $ADMIN_TOKEN"
echo -e "\n"

# Deletar Tenant
echo "8. Deletar Tenant"
curl -s -X DELETE "$BASE_URL/api/admin/tenants/$TENANT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.' || curl -s -X DELETE "$BASE_URL/api/admin/tenants/$TENANT_ID" -H "Authorization: Bearer $ADMIN_TOKEN"
echo -e "\n"

echo "=== Testes Concluídos ==="
