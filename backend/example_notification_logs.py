"""
Exemplo de uso do sistema de logs de notificações.

Este script demonstra:
1. Como criar logs de notificações manualmente
2. Como consultar logs do banco de dados
3. Como usar o endpoint REST para consultar logs
"""

import asyncio
import json
import time
from datetime import datetime

from sqlalchemy import select

from app.db.database import async_session, init_db
from app.models.models import NotificationLog
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


async def create_sample_logs():
    """Cria logs de exemplo no banco de dados."""
    print("\n" + "="*70)
    print("CRIANDO LOGS DE EXEMPLO")
    print("="*70 + "\n")
    
    async with async_session() as db:
        # Log 1: Telegram - Sucesso
        log1 = NotificationLog(
            timestamp=datetime.utcnow(),
            channel="telegram",
            event_type="fall_suspected",
            confidence=0.92,
            recipient="123456789",
            success=True,
            error_message=None,
            alert_data=json.dumps({
                "event_type": "fall_suspected",
                "confidence": 0.92,
                "timestamp": time.time(),
                "message": "⚠️ Queda detectada com alta confiança!",
                "details": {"rate_of_change": 18.5}
            })
        )
        db.add(log1)
        print("✓ Log 1: Telegram - Queda detectada (SUCESSO)")
        
        # Log 2: WhatsApp - Sucesso
        log2 = NotificationLog(
            timestamp=datetime.utcnow(),
            channel="whatsapp",
            event_type="presence_moving",
            confidence=0.85,
            recipient="+5511999999999",
            success=True,
            error_message=None,
            alert_data=json.dumps({
                "event_type": "presence_moving",
                "confidence": 0.85,
                "timestamp": time.time(),
                "message": "👤 Movimento detectado no ambiente",
                "details": {"variance": 3.2}
            })
        )
        db.add(log2)
        print("✓ Log 2: WhatsApp - Movimento detectado (SUCESSO)")
        
        # Log 3: Webhook - Falha
        log3 = NotificationLog(
            timestamp=datetime.utcnow(),
            channel="webhook",
            event_type="anomaly_detected",
            confidence=0.95,
            recipient="https://example.com/webhook",
            success=False,
            error_message="Connection timeout after 30 seconds",
            alert_data=json.dumps({
                "event_type": "anomaly_detected",
                "confidence": 0.95,
                "timestamp": time.time(),
                "message": "🔍 Anomalia detectada no padrão de comportamento",
                "details": {"anomaly_score": 0.95}
            })
        )
        db.add(log3)
        print("✓ Log 3: Webhook - Anomalia detectada (FALHA)")
        
        # Log 4: Telegram - Falha
        log4 = NotificationLog(
            timestamp=datetime.utcnow(),
            channel="telegram",
            event_type="prolonged_inactivity",
            confidence=0.88,
            recipient="987654321",
            success=False,
            error_message="Bot token invalid or expired",
            alert_data=json.dumps({
                "event_type": "prolonged_inactivity",
                "confidence": 0.88,
                "timestamp": time.time(),
                "message": "⏱️ Inatividade prolongada detectada",
                "details": {"duration_seconds": 1800}
            })
        )
        db.add(log4)
        print("✓ Log 4: Telegram - Inatividade prolongada (FALHA)")
        
        await db.commit()
        print(f"\n✅ {4} logs de exemplo criados com sucesso!\n")


async def query_all_logs():
    """Consulta todos os logs do banco de dados."""
    print("\n" + "="*70)
    print("CONSULTANDO TODOS OS LOGS")
    print("="*70 + "\n")
    
    async with async_session() as db:
        result = await db.execute(
            select(NotificationLog).order_by(NotificationLog.timestamp.desc())
        )
        logs = result.scalars().all()
        
        if not logs:
            print("❌ Nenhum log encontrado no banco de dados")
            return
        
        print(f"📊 Total de logs: {len(logs)}\n")
        
        for i, log in enumerate(logs, 1):
            status = "✅ SUCESSO" if log.success else "❌ FALHA"
            print(f"Log #{i}:")
            print(f"  ID: {log.id}")
            print(f"  Timestamp: {log.timestamp}")
            print(f"  Canal: {log.channel}")
            print(f"  Evento: {log.event_type}")
            print(f"  Confiança: {log.confidence:.2%}")
            print(f"  Destinatário: {log.recipient}")
            print(f"  Status: {status}")
            if log.error_message:
                print(f"  Erro: {log.error_message}")
            
            # Parse alert_data
            try:
                alert_data = json.loads(log.alert_data)
                print(f"  Mensagem: {alert_data.get('message', 'N/A')}")
            except:
                pass
            
            print()


async def query_logs_by_channel(channel: str):
    """Consulta logs de um canal específico."""
    print("\n" + "="*70)
    print(f"CONSULTANDO LOGS DO CANAL: {channel.upper()}")
    print("="*70 + "\n")
    
    async with async_session() as db:
        result = await db.execute(
            select(NotificationLog)
            .where(NotificationLog.channel == channel)
            .order_by(NotificationLog.timestamp.desc())
        )
        logs = result.scalars().all()
        
        if not logs:
            print(f"❌ Nenhum log encontrado para o canal '{channel}'")
            return
        
        print(f"📊 Total de logs do {channel}: {len(logs)}\n")
        
        success_count = sum(1 for log in logs if log.success)
        failure_count = len(logs) - success_count
        
        print(f"✅ Sucessos: {success_count}")
        print(f"❌ Falhas: {failure_count}")
        print(f"📈 Taxa de sucesso: {success_count/len(logs):.1%}\n")
        
        for i, log in enumerate(logs, 1):
            status = "✅" if log.success else "❌"
            print(f"{status} {log.event_type} - {log.timestamp} - Confiança: {log.confidence:.2%}")


async def query_failed_logs():
    """Consulta apenas logs de falhas."""
    print("\n" + "="*70)
    print("CONSULTANDO LOGS DE FALHAS")
    print("="*70 + "\n")
    
    async with async_session() as db:
        result = await db.execute(
            select(NotificationLog)
            .where(NotificationLog.success == False)
            .order_by(NotificationLog.timestamp.desc())
        )
        logs = result.scalars().all()
        
        if not logs:
            print("✅ Nenhuma falha registrada! Todas as notificações foram enviadas com sucesso.")
            return
        
        print(f"⚠️ Total de falhas: {len(logs)}\n")
        
        for i, log in enumerate(logs, 1):
            print(f"Falha #{i}:")
            print(f"  Canal: {log.channel}")
            print(f"  Evento: {log.event_type}")
            print(f"  Timestamp: {log.timestamp}")
            print(f"  Destinatário: {log.recipient}")
            print(f"  Erro: {log.error_message}")
            print()


async def demonstrate_notification_service_logging():
    """Demonstra logging automático do NotificationService."""
    print("\n" + "="*70)
    print("DEMONSTRANDO LOGGING AUTOMÁTICO DO NOTIFICATIONSERVICE")
    print("="*70 + "\n")
    
    # Configura serviço sem canais reais (para não tentar enviar)
    config = NotificationConfig(
        enabled=True,
        channels=[],  # Sem canais configurados
        min_confidence=0.5
    )
    
    service = NotificationService(config)
    
    # Cria alerta
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.95,
        timestamp=time.time(),
        message="Queda detectada com alta confiança!",
        details={"rate_of_change": 20.0}
    )
    
    print("📤 Enviando alerta através do NotificationService...")
    print(f"   Evento: {alert.event_type}")
    print(f"   Confiança: {alert.confidence:.2%}")
    print(f"   Mensagem: {alert.message}")
    
    # Envia alerta (não criará logs pois não há canais configurados)
    await service.send_alert(alert)
    
    print("\n✅ Alerta processado!")
    print("ℹ️  Como não há canais configurados, nenhum log foi criado.")
    print("   Em produção, com canais configurados, logs seriam criados automaticamente.")


async def main():
    """Função principal."""
    print("\n" + "="*70)
    print("EXEMPLO: SISTEMA DE LOGS DE NOTIFICAÇÕES")
    print("="*70)
    
    # Inicializa banco de dados
    await init_db()
    
    # 1. Cria logs de exemplo
    await create_sample_logs()
    
    # 2. Consulta todos os logs
    await query_all_logs()
    
    # 3. Consulta logs por canal
    await query_logs_by_channel("telegram")
    await query_logs_by_channel("whatsapp")
    await query_logs_by_channel("webhook")
    
    # 4. Consulta apenas falhas
    await query_failed_logs()
    
    # 5. Demonstra logging automático
    await demonstrate_notification_service_logging()
    
    print("\n" + "="*70)
    print("EXEMPLO CONCLUÍDO")
    print("="*70)
    print("\n💡 Dica: Use o endpoint REST para consultar logs:")
    print("   GET /api/notifications/logs")
    print("   GET /api/notifications/logs?channel=telegram")
    print("   GET /api/notifications/logs?limit=10&offset=0")
    print()


if __name__ == "__main__":
    asyncio.run(main())
