"""
Teste DIRETO do Telegram - Sem NotificationService
"""

import asyncio
import httpx


async def test_telegram_direto():
    """Testa envio direto para API do Telegram."""
    
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = """
🎉 *TESTE WiFiSense*

✅ Sistema funcionando!
📱 Notificação via Telegram
⏰ Teste realizado com sucesso

Este é um teste direto da API do Telegram.
    """.strip()
    
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    print("="*70)
    print("TESTE DIRETO - API TELEGRAM")
    print("="*70)
    print(f"\nBot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"\nEnviando mensagem...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=10.0)
            
            if response.status_code == 200:
                print("\n✅ SUCESSO! Mensagem enviada!")
                print(f"Response: {response.json()}")
                print("\n📱 Verifique seu Telegram agora!")
            else:
                print(f"\n❌ ERRO: Status {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_telegram_direto())
