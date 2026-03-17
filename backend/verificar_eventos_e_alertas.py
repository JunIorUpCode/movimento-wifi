"""
Script para verificar eventos detectados e alertas enviados.
"""

import asyncio
from app.db.database import async_session
from sqlalchemy import select
from app.models.models import Event, NotificationLog


async def verificar():
    """Verifica eventos e logs de notificação."""
    
    async with async_session() as db:
        # Últimos eventos
        result = await db.execute(
            select(Event).order_by(Event.timestamp.desc()).limit(20)
        )
        events = result.scalars().all()
        
        print("="*70)
        print("ÚLTIMOS 20 EVENTOS DETECTADOS")
        print("="*70)
        
        if not events:
            print("❌ Nenhum evento encontrado no banco de dados")
        else:
            for e in events:
                emoji_map = {
                    'no_presence': '⚪',
                    'presence_still': '🟢',
                    'presence_moving': '🔵',
                    'fall_suspected': '🔴',
                    'prolonged_inactivity': '🟡',
                    'anomaly_detected': '🟣'
                }
                emoji = emoji_map.get(e.event_type, '⚪')
                print(f"{emoji} {e.timestamp} | {e.event_type:25} | Conf: {e.confidence:.0%}")
        
        # Logs de notificação
        result2 = await db.execute(
            select(NotificationLog).order_by(NotificationLog.timestamp.desc()).limit(20)
        )
        logs = result2.scalars().all()
        
        print("\n" + "="*70)
        print("ÚLTIMOS 20 LOGS DE NOTIFICAÇÃO")
        print("="*70)
        
        if not logs:
            print("❌ Nenhum log de notificação encontrado")
            print("\nISSO SIGNIFICA:")
            print("- Sistema detectou eventos MAS não gerou alertas")
            print("- Ou eventos não atingiram critérios para alerta")
        else:
            for l in logs:
                status = "✅" if l.success else "❌"
                print(f"{status} {l.timestamp} | {l.channel:10} | {l.event_type:25} | Conf: {l.confidence:.0%}")
                if not l.success and l.error_message:
                    print(f"   Erro: {l.error_message}")
        
        print("\n" + "="*70)
        print("ANÁLISE")
        print("="*70)
        
        # Conta eventos por tipo
        event_counts = {}
        for e in events:
            event_counts[e.event_type] = event_counts.get(e.event_type, 0) + 1
        
        print("\nEventos detectados:")
        for event_type, count in event_counts.items():
            print(f"  - {event_type}: {count}")
        
        # Conta alertas enviados
        alert_counts = {}
        for l in logs:
            alert_counts[l.event_type] = alert_counts.get(l.event_type, 0) + 1
        
        if alert_counts:
            print("\nAlertas enviados:")
            for event_type, count in alert_counts.items():
                print(f"  - {event_type}: {count}")
        else:
            print("\n⚠️  NENHUM ALERTA FOI ENVIADO!")
            print("\nMotivos possíveis:")
            print("1. Eventos detectados não são críticos (movimento normal)")
            print("2. Confiança abaixo do mínimo (70%)")
            print("3. Cooldown ativo (60s entre alertas)")
            print("4. AlertService só alerta para: fall_suspected e prolonged_inactivity")


if __name__ == "__main__":
    asyncio.run(verificar())
