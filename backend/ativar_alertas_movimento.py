"""
Script para ativar alertas de MOVIMENTO.
Modo teste: recebe alerta para qualquer movimento detectado.
"""

import asyncio
import httpx


async def ativar_alertas_movimento():
    """Ativa alertas para movimento."""
    
    print("="*70)
    print("ATIVANDO ALERTAS DE MOVIMENTO")
    print("="*70)
    
    config = {
        "enabled": True,
        "channels": ["telegram"],
        "telegram_bot_token": "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA",
        "telegram_chat_ids": ["2085218769"],
        "min_confidence": 0.6,  # 60% - detecta mais eventos
        "cooldown_seconds": 30,  # 30 segundos entre alertas
        "quiet_hours": []
    }
    
    print("\n📱 Configurando Telegram...")
    print(f"   - Confiança mínima: {config['min_confidence']*100:.0f}%")
    print(f"   - Cooldown: {config['cooldown_seconds']}s")
    print(f"   - Alertas ativos:")
    print(f"     • 🚶 Movimento")
    print(f"     • 👤 Presença parada")
    print(f"     • 🚨 Queda")
    print(f"     • ⏰ Inatividade")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.put(
                "http://localhost:8000/api/notifications/config",
                json=config
            )
            
            if response.status_code == 200:
                print("\n✅ Configuração atualizada com sucesso!")
                print("\n🎯 MODO TESTE ATIVO")
                print("   Você receberá alertas no Telegram para:")
                print("   - Qualquer movimento detectado")
                print("   - Presença no ambiente")
                print("   - Quedas")
                print("   - Inatividade prolongada")
                print("\n📱 Agora ande pelo ambiente e veja os alertas chegando!")
            else:
                print(f"\n❌ Erro: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nCertifique-se que o backend está rodando:")
        print("  uvicorn app.main:app --reload")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(ativar_alertas_movimento())
