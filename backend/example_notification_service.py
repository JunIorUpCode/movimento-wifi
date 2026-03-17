"""
Exemplo de uso do NotificationService

Demonstra como usar o NotificationService para enviar alertas
com validações de confiança, cooldown e quiet hours.
"""

import asyncio
import time

from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


async def main():
    """Exemplo de uso do NotificationService."""
    
    print("=" * 60)
    print("NotificationService - Exemplo de Uso")
    print("=" * 60)
    
    # 1. Criar configuração
    print("\n1. Criando configuração...")
    config = NotificationConfig(
        enabled=True,
        channels=[],  # Sem canais reais para este exemplo
        min_confidence=0.7,
        cooldown_seconds=5,  # 5 segundos para demonstração
        quiet_hours=[(22, 7)]  # 22h-7h
    )
    print(f"   ✓ Confiança mínima: {config.min_confidence}")
    print(f"   ✓ Cooldown: {config.cooldown_seconds}s")
    print(f"   ✓ Quiet hours: {config.quiet_hours}")
    
    # 2. Criar serviço (singleton)
    print("\n2. Criando NotificationService...")
    service = NotificationService(config)
    print(f"   ✓ Canais configurados: {len(service._channels)}")
    
    # 3. Criar alertas
    print("\n3. Criando alertas de teste...")
    
    alert_high = Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=time.time(),
        message="Queda detectada com alta confiança"
    )
    print(f"   ✓ Alerta 1: {alert_high.event_type} (confiança: {alert_high.confidence})")
    
    alert_low = Alert(
        event_type="presence_moving",
        confidence=0.5,
        timestamp=time.time(),
        message="Movimento detectado"
    )
    print(f"   ✓ Alerta 2: {alert_low.event_type} (confiança: {alert_low.confidence})")
    
    # 4. Enviar alerta com alta confiança
    print("\n4. Enviando alerta com alta confiança...")
    await service.send_alert(alert_high)
    print("   ✓ Alerta enviado (passou validação de confiança)")
    
    # 5. Tentar enviar alerta com baixa confiança
    print("\n5. Tentando enviar alerta com baixa confiança...")
    await service.send_alert(alert_low)
    print("   ✗ Alerta bloqueado (confiança abaixo do mínimo)")
    
    # 6. Tentar enviar mesmo alerta novamente (cooldown)
    print("\n6. Tentando enviar mesmo tipo de alerta (cooldown ativo)...")
    alert_duplicate = Alert(
        event_type="fall_suspected",
        confidence=0.90,
        timestamp=time.time(),
        message="Outra queda"
    )
    await service.send_alert(alert_duplicate)
    print("   ✗ Alerta bloqueado (cooldown ativo)")
    
    # 7. Aguardar cooldown expirar
    print("\n7. Aguardando cooldown expirar (5 segundos)...")
    await asyncio.sleep(5.1)
    print("   ✓ Cooldown expirado")
    
    # 8. Enviar após cooldown
    print("\n8. Enviando após cooldown expirar...")
    await service.send_alert(alert_duplicate)
    print("   ✓ Alerta enviado (cooldown expirado)")
    
    # 9. Verificar timestamps
    print("\n9. Verificando timestamps de notificações...")
    last_time = service.get_last_notification_time("fall_suspected")
    if last_time:
        print(f"   ✓ Última notificação de 'fall_suspected': {last_time:.2f}")
    
    # 10. Reset de cooldown
    print("\n10. Resetando cooldown...")
    service.reset_cooldown("fall_suspected")
    print("   ✓ Cooldown resetado")
    
    # 11. Verificar quiet hours
    print("\n11. Verificando quiet hours...")
    is_quiet = service._is_quiet_hours()
    print(f"   {'✓' if not is_quiet else '✗'} Quiet hours: {is_quiet}")
    
    print("\n" + "=" * 60)
    print("Exemplo concluído com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
