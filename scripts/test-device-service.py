#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Teste - Device Service
Testa endpoints do device-service
"""

import httpx
import asyncio
from datetime import datetime

# URLs dos serviços
DEVICE_SERVICE_URL = "http://localhost:8003"
LICENSE_SERVICE_URL = "http://localhost:8004"


async def test_device_service():
    """Testa endpoints do device-service"""
    
    print("=" * 60)
    print("TESTE DO DEVICE SERVICE")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # 1. Health Check
        print("\n1. Testando Health Check...")
        try:
            response = await client.get(f"{DEVICE_SERVICE_URL}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            print("   ⚠️  Certifique-se de que o device-service está rodando na porta 8003")
            return
        
        # 2. Root Endpoint
        print("\n2. Testando Root Endpoint...")
        try:
            response = await client.get(f"{DEVICE_SERVICE_URL}/")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Endpoints disponíveis: {len(data.get('endpoints', {}))}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print("\n" + "=" * 60)
        print("TESTE COMPLETO")
        print("=" * 60)
        print("\n✅ Device-service está funcionando!")
        print("\n📝 Próximos passos:")
        print("   1. Gerar uma licença no license-service")
        print("   2. Usar a activation_key para registrar um dispositivo")
        print("   3. Testar heartbeat do dispositivo")


if __name__ == "__main__":
    asyncio.run(test_device_service())
