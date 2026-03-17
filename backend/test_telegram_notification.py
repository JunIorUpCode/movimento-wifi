"""
Script de teste para notificações do Telegram

INSTRUÇÕES:
1. As credenciais já estão configuradas abaixo
2. Execute: python test_telegram_notification.py
3. Escolha a opção de teste
"""

import asyncio
import time
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


async def test_telegram():
    """Testa envio de notificação via Telegram."""
    
    print("="*70)
    print("TESTE DE NOTIFICAÇÃO TELEGRAM")
    print("="*70)
    
    # ✅ CREDENCIAIS CONFIGURADAS
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    print(f"\n✓ Bot Token: {BOT_TOKEN[:20]}...")
    print(f"✓ Chat ID: {CHAT_ID}")
    
    # Configurar serviço
    print("\n[1/3] Configurando NotificationService...")
    config = NotificationConfig(
        enabled=True,
        channels=["telegram"],
        telegram_bot_token=BOT_TOKEN,
        telegram_chat_ids=[CHAT_ID],
        min_confidence=0.5,  # Baixo para teste
        cooldown_seconds=10   # Curto para teste
    )
    
    service = NotificationService(config)
    print("✓ Serviço configurado")
    
    # Criar alertas de teste
    print("\n[2/3] Criando alertas de teste...")
    
    alerts = [
        Alert(
            event_type="fall_suspected",
            confidence=0.95,
            timestamp=time.time(),
            message="🚨 TESTE: Queda detectada com alta confiança!",
            details={
                "rate_of_change": 15.5,
                "rssi_before": -45.2,
                "rssi_after": -68.7
            }
        ),
        Alert(
            event_type="inactivity_alert",
            confidence=0.85,
            timestamp=time.time(),
            message="⏰ TESTE: Inatividade prolongada detectada",
            details={
                "duration_minutes": 120,
                "last_movement": "2 horas atrás"
            }
        ),
        Alert(
            event_type="movement_detected",
            confidence=0.75,
            timestamp=time.time(),
            message="🚶 TESTE: Movimento detectado no ambiente",
            details={
                "variance": 3.5,
                "zone": "Sala de estar"
            }
        )
    ]
    
    print(f"✓ {len(alerts)} alertas criados")
    
    # Enviar alertas
    print("\n[3/3] Enviando alertas...")
    for i, alert in enumerate(alerts, 1):
        print(f"\n  Enviando alerta {i}/{len(alerts)}: {alert.event_type}")
        try:
            await service.send_alert(alert)
            print(f"  ✓ Alerta {i} enviado com sucesso!")
        except Exception as e:
            print(f"  ✗ Erro ao enviar alerta {i}: {e}")
        
        # Aguardar um pouco entre alertas
        if i < len(alerts):
            await asyncio.sleep(2)
    
    print("\n" + "="*70)
    print("✓ TESTE CONCLUÍDO!")
    print("="*70)
    print("\n📱 Verifique seu Telegram para ver as mensagens!")
    print("\n💡 Dica: Se não recebeu, verifique:")
    print("  1. Token e Chat ID estão corretos")
    print("  2. Você enviou /start para o bot")
    print("  3. O bot não está bloqueado")


async def test_simple():
    """Teste simples e direto."""
    
    print("\n" + "="*70)
    print("TESTE SIMPLES - UMA MENSAGEM")
    print("="*70)
    
    # ✅ CREDENCIAIS CONFIGURADAS
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    config = NotificationConfig(
        enabled=True,
        channels=["telegram"],
        telegram_bot_token=BOT_TOKEN,
        telegram_chat_ids=[CHAT_ID],  # Lista com o chat ID
        min_confidence=0.5
    )
    
    service = NotificationService(config)
    
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.95,
        timestamp=time.time(),
        message="🎉 WiFiSense funcionando! Este é um teste.",
        details={"status": "Sistema operacional"}
    )
    
    print("\nEnviando mensagem de teste...")
    await service.send_alert(alert)
    print("✓ Mensagem enviada! Verifique seu Telegram!")


if __name__ == "__main__":
    print("\n🤖 TESTE DE NOTIFICAÇÕES TELEGRAM - WiFiSense")
    print("\nEscolha o tipo de teste:")
    print("  1 - Teste completo (3 alertas diferentes)")
    print("  2 - Teste simples (1 mensagem)")
    
    choice = input("\nDigite 1 ou 2: ").strip()
    
    if choice == "1":
        asyncio.run(test_telegram())
    elif choice == "2":
        asyncio.run(test_simple())
    else:
        print("Opção inválida!")
