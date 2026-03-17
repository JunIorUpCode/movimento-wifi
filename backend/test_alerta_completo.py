"""
Teste COMPLETO do fluxo de alertas
Simula detecção → NotificationService → Telegram
"""

import asyncio
import time
from datetime import datetime

# Importa componentes do sistema
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


async def test_alerta_completo():
    """Testa fluxo completo de alerta até o Telegram."""
    
    print("="*70)
    print("TESTE COMPLETO - FLUXO DE ALERTAS")
    print("="*70)
    
    # Configuração do Telegram
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    print(f"\n📱 Bot: @zelarupcode_bot")
    print(f"📱 Chat ID: {CHAT_ID}")
    
    # Passo 1: Configurar NotificationService
    print("\n[1/4] Configurando NotificationService...")
    config = NotificationConfig(
        enabled=True,
        channels=["telegram"],
        telegram_bot_token=BOT_TOKEN,
        telegram_chat_ids=[CHAT_ID],
        min_confidence=0.7,
        cooldown_seconds=10,  # 10 segundos para teste
        quiet_hours=[]  # Sem quiet hours para teste
    )
    
    # Força nova instância (limpa singleton)
    NotificationService._instance = None
    service = NotificationService(config)
    print("✅ NotificationService configurado")
    
    # Passo 2: Criar alerta de teste
    print("\n[2/4] Criando alerta de teste...")
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.95,
        timestamp=time.time(),
        message="🚨 Queda detectada no teste!",
        details={
            "rate_of_change": 15.5,
            "rssi_before": -45.0,
            "rssi_after": -60.0,
            "test": True
        }
    )
    print(f"✅ Alerta criado: {alert.event_type} (confiança: {alert.confidence:.0%})")
    
    # Passo 3: Enviar alerta
    print("\n[3/4] Enviando alerta...")
    try:
        await service.send_alert(alert)
        print("✅ Alerta enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar alerta: {e}")
        return
    
    # Passo 4: Verificar
    print("\n[4/4] Verificação")
    print("📱 Verifique seu Telegram agora!")
    print("Você deve ter recebido uma mensagem com:")
    print("  - 🚨 ALERTA: Queda suspeita")
    print("  - ⏰ Data/hora")
    print("  - 📊 Confiança: 95%")
    print("  - 📝 Detalhes técnicos")
    
    print("\n" + "="*70)
    print("TESTE CONCLUÍDO")
    print("="*70)


async def test_multiplos_alertas():
    """Testa múltiplos tipos de alertas."""
    
    print("\n\n")
    print("="*70)
    print("TESTE DE MÚLTIPLOS ALERTAS")
    print("="*70)
    
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    # Configurar serviço
    config = NotificationConfig(
        enabled=True,
        channels=["telegram"],
        telegram_bot_token=BOT_TOKEN,
        telegram_chat_ids=[CHAT_ID],
        min_confidence=0.7,
        cooldown_seconds=5,  # 5 segundos entre alertas
        quiet_hours=[]
    )
    
    NotificationService._instance = None
    service = NotificationService(config)
    
    # Lista de alertas para testar
    alertas = [
        Alert(
            event_type="fall_suspected",
            confidence=0.95,
            timestamp=time.time(),
            message="🚨 Queda detectada!",
            details={"rate_of_change": 15.5}
        ),
        Alert(
            event_type="prolonged_inactivity",
            confidence=0.85,
            timestamp=time.time(),
            message="⏰ Inatividade prolongada",
            details={"duration": 7200}  # 2 horas
        ),
        Alert(
            event_type="presence_moving",
            confidence=0.75,
            timestamp=time.time(),
            message="🚶 Movimento detectado",
            details={"variance": 3.5}
        ),
        Alert(
            event_type="anomaly_detected",
            confidence=0.90,
            timestamp=time.time(),
            message="📊 Anomalia detectada",
            details={"anomaly_score": 92}
        )
    ]
    
    print(f"\nEnviando {len(alertas)} alertas diferentes...\n")
    
    for i, alert in enumerate(alertas, 1):
        print(f"[{i}/{len(alertas)}] Enviando: {alert.event_type}...")
        try:
            await service.send_alert(alert)
            print(f"  ✅ Enviado com sucesso!")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        # Aguarda cooldown entre alertas
        if i < len(alertas):
            print(f"  ⏳ Aguardando cooldown (5s)...")
            await asyncio.sleep(6)
    
    print("\n" + "="*70)
    print("TODOS OS ALERTAS ENVIADOS")
    print("="*70)
    print("\n📱 Verifique seu Telegram!")
    print(f"Você deve ter recebido {len(alertas)} mensagens diferentes.")


async def main():
    """Executa todos os testes."""
    
    print("\n🧪 INICIANDO TESTES DE ALERTAS\n")
    
    # Teste 1: Alerta único
    await test_alerta_completo()
    
    # Aguarda um pouco
    await asyncio.sleep(3)
    
    # Teste 2: Múltiplos alertas (opcional)
    resposta = input("\n\nDeseja testar múltiplos tipos de alertas? (s/n): ")
    if resposta.lower() == 's':
        await test_multiplos_alertas()
    
    print("\n\n✅ Testes finalizados!")


if __name__ == "__main__":
    asyncio.run(main())
