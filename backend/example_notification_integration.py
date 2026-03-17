"""
Exemplo de uso da integração de notificações no MonitorService.

Este script demonstra:
1. Como configurar notificações via API
2. Como testar notificações
3. Como o MonitorService envia notificações automaticamente
"""

import asyncio
import time

import httpx

# URL base da API
BASE_URL = "http://localhost:8000/api"


async def configure_notifications():
    """Configura notificações via API."""
    print("\n" + "="*70)
    print("1. CONFIGURANDO NOTIFICAÇÕES")
    print("="*70)
    
    config = {
        "enabled": True,
        "channels": ["telegram"],  # Adicione "whatsapp", "webhook" conforme necessário
        "min_confidence": 0.7,
        "cooldown_seconds": 60,  # 1 minuto entre alertas do mesmo tipo
        "quiet_hours": [[22, 7]],  # Silêncio das 22h às 7h
        
        # Telegram (substitua com suas credenciais)
        "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
        "telegram_chat_ids": ["YOUR_CHAT_ID_HERE"],
        
        # WhatsApp (opcional - via Twilio)
        "twilio_account_sid": None,
        "twilio_auth_token": None,
        "twilio_whatsapp_from": None,
        "whatsapp_recipients": [],
        
        # Webhook (opcional)
        "webhook_urls": [],
        "webhook_secret": None
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{BASE_URL}/notifications/config", json=config)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Notificações configuradas com sucesso!")
            print(f"  - Habilitado: {data['enabled']}")
            print(f"  - Canais: {', '.join(data['channels'])}")
            print(f"  - Confiança mínima: {data['min_confidence']}")
            print(f"  - Cooldown: {data['cooldown_seconds']}s")
            print(f"  - Telegram configurado: {data['telegram_configured']}")
            print(f"  - Chats Telegram: {data['telegram_chat_count']}")
        else:
            print(f"✗ Erro ao configurar notificações: {response.status_code}")
            print(f"  {response.text}")


async def get_notification_config():
    """Obtém configuração atual de notificações."""
    print("\n" + "="*70)
    print("2. CONSULTANDO CONFIGURAÇÃO ATUAL")
    print("="*70)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/notifications/config")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Configuração atual:")
            print(f"  - Habilitado: {data['enabled']}")
            print(f"  - Canais: {', '.join(data['channels']) if data['channels'] else 'Nenhum'}")
            print(f"  - Confiança mínima: {data['min_confidence']}")
            print(f"  - Cooldown: {data['cooldown_seconds']}s")
            print(f"  - Quiet hours: {data['quiet_hours']}")
            print(f"  - Telegram: {'✓' if data['telegram_configured'] else '✗'} ({data['telegram_chat_count']} chats)")
            print(f"  - WhatsApp: {'✓' if data['whatsapp_configured'] else '✗'} ({data['whatsapp_recipient_count']} destinatários)")
            print(f"  - Webhook: {'✓' if data['webhook_configured'] else '✗'} ({data['webhook_url_count']} URLs)")
        else:
            print(f"✗ Erro ao consultar configuração: {response.status_code}")


async def test_notification(channel: str = "telegram"):
    """Testa envio de notificação para um canal."""
    print("\n" + "="*70)
    print(f"3. TESTANDO NOTIFICAÇÃO ({channel.upper()})")
    print("="*70)
    
    test_request = {
        "channel": channel,
        "message": "🧪 Teste de notificação WiFiSense - Tudo funcionando!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/notifications/test", json=test_request)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {data['message']}")
            print(f"  Canal: {data['channel']}")
        else:
            print(f"✗ Erro ao testar notificação: {response.status_code}")
            print(f"  {response.text}")


async def get_notification_logs(limit: int = 10):
    """Consulta logs de notificações enviadas."""
    print("\n" + "="*70)
    print("4. CONSULTANDO LOGS DE NOTIFICAÇÕES")
    print("="*70)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/notifications/logs?limit={limit}")
        
        if response.status_code == 200:
            logs = response.json()
            
            if not logs:
                print("  Nenhum log de notificação encontrado.")
                return
            
            print(f"✓ Últimos {len(logs)} logs:")
            for log in logs:
                status = "✓" if log['success'] else "✗"
                print(f"\n  {status} {log['timestamp']}")
                print(f"     Canal: {log['channel']}")
                print(f"     Evento: {log['event_type']}")
                print(f"     Confiança: {log['confidence']:.2f}")
                print(f"     Destinatário: {log['recipient']}")
                if not log['success'] and log['error_message']:
                    print(f"     Erro: {log['error_message']}")
        else:
            print(f"✗ Erro ao consultar logs: {response.status_code}")


async def monitor_with_notifications():
    """Demonstra o fluxo completo de monitoramento com notificações."""
    print("\n" + "="*70)
    print("5. MONITORAMENTO COM NOTIFICAÇÕES ATIVAS")
    print("="*70)
    
    print("\nO MonitorService está configurado para:")
    print("  1. Capturar sinais Wi-Fi")
    print("  2. Processar e detectar eventos")
    print("  3. Avaliar se deve gerar alerta (AlertService)")
    print("  4. Enviar notificação se alerta foi gerado")
    print("\nFluxo de notificação:")
    print("  Detecção → AlertService.evaluate() → _send_notification() → NotificationService.send_alert()")
    print("\nValidações aplicadas:")
    print("  ✓ Notificações habilitadas?")
    print("  ✓ Confiança >= min_confidence?")
    print("  ✓ Cooldown expirado?")
    print("  ✓ Fora de quiet hours?")
    print("\nSe todas as validações passarem, notificação é enviada para todos os canais configurados.")
    
    # Inicia monitoramento
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/monitor/start")
        if response.status_code == 200:
            print("\n✓ Monitoramento iniciado!")
            print("  Aguardando eventos para enviar notificações...")
            print("  (Pressione Ctrl+C para parar)")
            
            try:
                # Aguarda alguns segundos
                await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("\n\nParando monitoramento...")
            finally:
                # Para monitoramento
                await client.post(f"{BASE_URL}/monitor/stop")
                print("✓ Monitoramento parado.")


async def main():
    """Executa todos os exemplos."""
    print("\n" + "="*70)
    print("EXEMPLO: INTEGRAÇÃO DE NOTIFICAÇÕES NO MONITORSERVICE")
    print("="*70)
    
    try:
        # 1. Configura notificações
        await configure_notifications()
        
        # 2. Consulta configuração
        await get_notification_config()
        
        # 3. Testa notificação
        # NOTA: Descomente a linha abaixo se tiver credenciais configuradas
        # await test_notification("telegram")
        print("\n⚠️  Teste de notificação desabilitado (configure credenciais primeiro)")
        
        # 4. Consulta logs
        await get_notification_logs(limit=5)
        
        # 5. Demonstra monitoramento com notificações
        # NOTA: Descomente a linha abaixo para iniciar monitoramento
        # await monitor_with_notifications()
        print("\n⚠️  Monitoramento desabilitado (descomente para testar)")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
    
    print("\n" + "="*70)
    print("EXEMPLO CONCLUÍDO")
    print("="*70)
    print("\nPróximos passos:")
    print("  1. Configure suas credenciais (Telegram, WhatsApp, Webhook)")
    print("  2. Execute: python example_notification_integration.py")
    print("  3. Teste notificações via API")
    print("  4. Inicie o monitoramento e aguarde eventos")
    print("  5. Receba notificações em tempo real!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
