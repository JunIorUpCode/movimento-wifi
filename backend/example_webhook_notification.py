"""
Exemplo de uso do WebhookChannel para envio de notificações via webhook.

Este script demonstra:
1. Criação de canal webhook com múltiplas URLs
2. Envio de alertas com assinatura HMAC
3. Gerenciamento de fila de webhooks pendentes
4. Retry de webhooks falhados
"""

import asyncio
import time
from app.services.notification_channels import WebhookChannel
from app.services.notification_types import Alert


async def exemplo_basico():
    """Exemplo básico de envio de webhook."""
    print("=" * 60)
    print("EXEMPLO 1: Envio Básico de Webhook")
    print("=" * 60)
    
    # Criar canal com múltiplas URLs
    channel = WebhookChannel(
        urls=[
            "https://webhook.site/unique-id-1",  # Substitua com URL real
            "https://webhook.site/unique-id-2"
        ]
    )
    
    # Criar alerta
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=time.time(),
        message="Queda detectada no ambiente",
        details={
            "rate_of_change": 15.2,
            "location": "sala",
            "rssi_before": -45.0,
            "rssi_after": -60.2
        }
    )
    
    # Enviar alerta
    print(f"\n📤 Enviando alerta: {alert.event_type}")
    print(f"   Confiança: {alert.confidence:.0%}")
    print(f"   Mensagem: {alert.message}")
    
    success = await channel.send(alert)
    
    if success:
        print("✅ Webhook enviado com sucesso!")
    else:
        print("❌ Falha ao enviar webhook")
    
    print(f"📊 Webhooks pendentes: {channel.get_pending_count()}")


async def exemplo_com_assinatura():
    """Exemplo de webhook com assinatura HMAC."""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Webhook com Assinatura HMAC")
    print("=" * 60)
    
    # Criar canal com secret para assinatura
    channel = WebhookChannel(
        urls=["https://webhook.site/unique-id"],
        secret="minha_chave_secreta_123"
    )
    
    # Criar alerta
    alert = Alert(
        event_type="presence_moving",
        confidence=0.75,
        timestamp=time.time(),
        message="Movimento detectado",
        details={"variance": 3.5}
    )
    
    # Gerar assinatura para demonstração
    payload = {
        "event_type": alert.event_type,
        "confidence": alert.confidence,
        "timestamp": alert.timestamp,
        "message": alert.message,
        "details": alert.details
    }
    
    signature = channel._generate_signature(payload)
    
    print(f"\n📤 Enviando alerta com assinatura HMAC")
    print(f"   Evento: {alert.event_type}")
    print(f"   Assinatura: {signature[:16]}...{signature[-16:]}")
    
    success = await channel.send(alert)
    
    if success:
        print("✅ Webhook com assinatura enviado!")
    else:
        print("❌ Falha ao enviar webhook")


async def exemplo_retry_pendentes():
    """Exemplo de gerenciamento de webhooks pendentes."""
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Gerenciamento de Webhooks Pendentes")
    print("=" * 60)
    
    # Criar canal (URLs inválidas para simular falha)
    channel = WebhookChannel(
        urls=[
            "https://invalid-url-that-will-fail.com/webhook1",
            "https://invalid-url-that-will-fail.com/webhook2"
        ]
    )
    
    # Criar alerta
    alert = Alert(
        event_type="anomaly_detected",
        confidence=0.90,
        timestamp=time.time(),
        message="Anomalia detectada no padrão de sinal",
        details={"anomaly_score": 92.5}
    )
    
    print(f"\n📤 Tentando enviar para URLs inválidas...")
    success = await channel.send(alert)
    
    if not success:
        print("❌ Falha esperada - URLs inválidas")
    
    pending_count = channel.get_pending_count()
    print(f"📊 Webhooks na fila pendente: {pending_count}")
    
    if pending_count > 0:
        print("\n🔄 Tentando reenviar webhooks pendentes...")
        success_count = await channel.retry_pending()
        print(f"✅ Webhooks reenviados com sucesso: {success_count}")
        print(f"📊 Ainda pendentes: {channel.get_pending_count()}")
        
        # Limpar fila
        print("\n🗑️  Limpando fila de pendentes...")
        channel.clear_pending_queue()
        print(f"📊 Fila após limpeza: {channel.get_pending_count()}")


async def exemplo_multiplos_alertas():
    """Exemplo de envio de múltiplos tipos de alertas."""
    print("\n" + "=" * 60)
    print("EXEMPLO 4: Múltiplos Tipos de Alertas")
    print("=" * 60)
    
    channel = WebhookChannel(
        urls=["https://webhook.site/unique-id"],
        secret="secret_key"
    )
    
    # Diferentes tipos de alertas
    alertas = [
        Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=time.time(),
            message="Queda suspeita detectada",
            details={"rate_of_change": 15.2}
        ),
        Alert(
            event_type="presence_moving",
            confidence=0.75,
            timestamp=time.time(),
            message="Movimento detectado",
            details={"variance": 3.5}
        ),
        Alert(
            event_type="prolonged_inactivity",
            confidence=0.80,
            timestamp=time.time(),
            message="Inatividade prolongada",
            details={"duration": 1800}
        ),
        Alert(
            event_type="multiple_people",
            confidence=0.70,
            timestamp=time.time(),
            message="Múltiplas pessoas detectadas",
            details={"estimated_count": 2}
        )
    ]
    
    print(f"\n📤 Enviando {len(alertas)} alertas diferentes...\n")
    
    for i, alert in enumerate(alertas, 1):
        print(f"{i}. {alert.event_type} (confiança: {alert.confidence:.0%})")
        success = await channel.send(alert)
        status = "✅" if success else "❌"
        print(f"   {status} {alert.message}")
        await asyncio.sleep(0.5)  # Pequeno delay entre envios
    
    print(f"\n📊 Total de webhooks pendentes: {channel.get_pending_count()}")


async def exemplo_formato_payload():
    """Exemplo mostrando o formato do payload enviado."""
    print("\n" + "=" * 60)
    print("EXEMPLO 5: Formato do Payload")
    print("=" * 60)
    
    channel = WebhookChannel(
        urls=["https://webhook.site/unique-id"],
        secret="secret_key"
    )
    
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=1234567890.123,
        message="Queda detectada",
        details={
            "rate_of_change": 15.2,
            "location": "sala",
            "rssi_before": -45.0,
            "rssi_after": -60.2
        }
    )
    
    # Mostrar formato da mensagem
    formatted = channel.format_message(alert)
    
    print("\n📋 Formato do payload JSON enviado:")
    print("-" * 60)
    print(formatted)
    print("-" * 60)
    
    # Mostrar assinatura
    payload = {
        "event_type": alert.event_type,
        "confidence": alert.confidence,
        "timestamp": alert.timestamp,
        "message": alert.message,
        "details": alert.details
    }
    signature = channel._generate_signature(payload)
    
    print(f"\n🔐 Header X-Webhook-Signature:")
    print(f"   {signature}")


async def main():
    """Executa todos os exemplos."""
    print("\n" + "=" * 60)
    print("EXEMPLOS DE USO DO WEBHOOKCHANNEL")
    print("=" * 60)
    
    try:
        # Exemplo 1: Básico
        await exemplo_basico()
        
        # Exemplo 2: Com assinatura
        await exemplo_com_assinatura()
        
        # Exemplo 3: Retry pendentes
        await exemplo_retry_pendentes()
        
        # Exemplo 4: Múltiplos alertas
        await exemplo_multiplos_alertas()
        
        # Exemplo 5: Formato payload
        await exemplo_formato_payload()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS EXEMPLOS CONCLUÍDOS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Iniciando exemplos de WebhookChannel...")
    print("⚠️  Nota: Substitua as URLs de exemplo por URLs reais para testar")
    print("    Sugestão: Use https://webhook.site para criar URLs de teste\n")
    
    asyncio.run(main())
