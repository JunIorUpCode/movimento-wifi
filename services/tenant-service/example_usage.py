# -*- coding: utf-8 -*-
"""
Exemplo de uso do tenant-service via HTTP
Demonstra como interagir com os endpoints REST
"""

import requests
import json
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8002"
ADMIN_TOKEN = "seu-token-admin-aqui"  # Obter do auth-service

# Headers com autenticação
headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}


def print_response(title, response):
    """Imprime resposta formatada"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def main():
    """Demonstra uso dos endpoints"""
    
    print("=== Exemplo de Uso do Tenant Service ===")
    
    # 1. Health Check
    response = requests.get(f"{BASE_URL}/health")
    print_response("1. Health Check", response)
    
    # 2. Criar Tenant
    tenant_data = {
        "email": f"exemplo_{datetime.now().timestamp()}@example.com",
        "name": "Empresa Exemplo LTDA",
        "plan_type": "basic"
    }
    response = requests.post(
        f"{BASE_URL}/api/admin/tenants",
        headers=headers,
        json=tenant_data
    )
    print_response("2. Criar Tenant", response)
    
    if response.status_code == 201:
        tenant = response.json()
        tenant_id = tenant["id"]
        
        # 3. Listar Tenants
        response = requests.get(
            f"{BASE_URL}/api/admin/tenants",
            headers=headers,
            params={"limit": 10, "offset": 0}
        )
        print_response("3. Listar Tenants", response)
        
        # 4. Obter Detalhes
        response = requests.get(
            f"{BASE_URL}/api/admin/tenants/{tenant_id}",
            headers=headers
        )
        print_response("4. Obter Detalhes do Tenant", response)
        
        # 5. Atualizar Tenant
        update_data = {
            "name": "Empresa Exemplo LTDA - Atualizada",
            "plan_type": "premium",
            "metadata": {
                "custom_field": "valor personalizado",
                "notes": "Cliente VIP"
            }
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/tenants/{tenant_id}",
            headers=headers,
            json=update_data
        )
        print_response("5. Atualizar Tenant", response)
        
        # 6. Suspender Tenant
        response = requests.post(
            f"{BASE_URL}/api/admin/tenants/{tenant_id}/suspend",
            headers=headers
        )
        print_response("6. Suspender Tenant", response)
        
        # 7. Ativar Tenant
        response = requests.post(
            f"{BASE_URL}/api/admin/tenants/{tenant_id}/activate",
            headers=headers
        )
        print_response("7. Ativar Tenant", response)
        
        # 8. Filtrar por Status
        response = requests.get(
            f"{BASE_URL}/api/admin/tenants",
            headers=headers,
            params={"status": "active", "limit": 5}
        )
        print_response("8. Filtrar Tenants Ativos", response)
        
        # 9. Filtrar por Plano
        response = requests.get(
            f"{BASE_URL}/api/admin/tenants",
            headers=headers,
            params={"plan": "premium", "limit": 5}
        )
        print_response("9. Filtrar Tenants Premium", response)
        
        # 10. Deletar Tenant
        response = requests.delete(
            f"{BASE_URL}/api/admin/tenants/{tenant_id}",
            headers=headers
        )
        print_response("10. Deletar Tenant", response)
        
        print("\n=== Exemplo Concluído com Sucesso ===")
    else:
        print("\n✗ Erro ao criar tenant. Verifique:")
        print("  - Serviço está rodando?")
        print("  - Token admin é válido?")
        print("  - Database está acessível?")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Erro de conexão. Verifique se o serviço está rodando:")
        print("  docker-compose up tenant-service")
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
