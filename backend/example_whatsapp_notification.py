"""
Exemplo de uso do WhatsAppChannel.

Este script demonstra como usar o canal de notificação WhatsApp
para enviar alertas via Twilio API.

IMPORTANTE: Para executar este exemplo, você precisa:
1. Uma conta Twilio ativa
2. Um número WhatsApp habilitado no Twilio
3. Destinatários que aceitaram mensagens do seu número Twilio

Para testar com Twilio Sandbox:
1. Acesse: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Envie a mensagem de ativação do seu WhatsApp para o número do sandbox
3. Use as credenciais do sandbox neste script
"""

import asyncio
import os
from datetime import datetime

from app.services.notification_channels import WhatsAppChannel
from app.services.notification_types import Alert


async def main():
    """Exemplo de envio de alerta via WhatsApp."""
    
    # Configuração (substitua com suas credenciais reais)
    # NUNCA commite credenciais reais no código!
    # Use variáveis de ambiente em produção
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")  # Sandbox number
    WHATSAPP_RECIPIENTS = os.getenv("WHATSAPP_RECIPIENTS", "+5511987654321").split(",")
    
    # Verifica se as credenciais foram configuradas
    if TWILIO_ACCOUNT_SID.startswith("ACxxx") or TWILIO_AUTH_TOKEN == "your_auth_token_here":
        print("⚠️  ATENÇÃO: Configure as credenciais Twilio antes de executar!")
        print("   Use variáveis de ambiente:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_WHATSAPP_FROM")
        print("   - WHATSAPP_RECIPIENTS (separados por vírgula)")
        return
    
    # Inicializa canal WhatsApp
    print("📱 Inicializando WhatsAppChannel...")
    channel = WhatsAppChannel(
        account_sid=TWILIO_ACCOUNT_SID,
        auth_token=TWILIO_AUTH_TOKEN,
        from_number=TWILIO_WHATSAPP_FROM,
        recipients=WHATSAPP_RECIPIENTS
    )
    print(f"✅ Canal inicializado com {len(WHATSAPP_RECIPIENTS)} destinatário(s)")
    
    # Exemplo 1: Alerta de queda
    print("\n" + "="*60)
    print("Exemplo 1: Alerta de Queda Suspeita")
    print("="*60)
    
    alert_fall = Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=datetime.now().timestamp(),
        message="Queda detectada no ambiente principal",
        details={
            "rate_of_change": 15.5,
            "location": "Sala de estar"
        }
    )
    
    print("\n📤 Enviando alerta de queda...")
    success = await channel.send(alert_fall)
    
    if success:
        print("✅ Alerta enviado com sucesso!")
    else:
        print("❌ Falha ao enviar alerta")
    
    # Aguarda um pouco antes do próximo exemplo
    await asyncio.sleep(2)
    
    # Exemplo 2: Alerta de movimento
    print("\n" + "="*60)
    print("Exemplo 2: Alerta de Movimento Detectado")
    print("="*60)
    
    alert_movement = Alert(
        event_type="presence_moving",
        confidence=0.75,
        timestamp=datetime.now().timestamp(),
        message="Movimento detectado após período de inatividade",
        details={
            "variance": 3.2,
            "duration": "5 minutos"
        }
    )
    
    print("\n📤 Enviando alerta de movimento...")
    success = await channel.send(alert_movement)
    
    if success:
        print("✅ Alerta enviado com sucesso!")
    else:
        print("❌ Falha ao enviar alerta")
    
    # Aguarda um pouco antes do próximo exemplo
    await asyncio.sleep(2)
    
    # Exemplo 3: Alerta de anomalia
    print("\n" + "="*60)
    print("Exemplo 3: Alerta de Anomalia Detectada")
    print("="*60)
    
    alert_anomaly = Alert(
        event_type="anomaly_detected",
        confidence=0.92,
        timestamp=datetime.now().timestamp(),
        message="Padrão anormal detectado no ambiente",
        details={
            "anomaly_score": 92,
            "expected_pattern": "Sem presença às 14h",
            "actual_pattern": "Presença detectada"
        }
    )
    
    print("\n📤 Enviando alerta de anomalia...")
    success = await channel.send(alert_anomaly)
    
    if success:
        print("✅ Alerta enviado com sucesso!")
    else:
        print("❌ Falha ao enviar alerta")
    
    # Exemplo 4: Visualizar formatação de mensagem
    print("\n" + "="*60)
    print("Exemplo 4: Visualização de Mensagem Formatada")
    print("="*60)
    
    alert_example = Alert(
        event_type="prolonged_inactivity",
        confidence=0.80,
        timestamp=datetime.now().timestamp(),
        message="Nenhum movimento detectado por período prolongado",
        details={
            "duration": "45 minutos",
            "last_movement": "14:30:00"
        }
    )
    
    formatted_message = channel.format_message(alert_example)
    print("\n📝 Mensagem formatada:")
    print("-" * 60)
    print(formatted_message)
    print("-" * 60)
    
    print("\n✅ Exemplos concluídos!")


if __name__ == "__main__":
    print("="*60)
    print("WhatsAppChannel - Exemplo de Uso")
    print("="*60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
