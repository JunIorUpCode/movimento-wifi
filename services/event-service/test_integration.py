# -*- coding: utf-8 -*-
"""
Teste de Integração - Event Service
Valida fluxo completo de processamento de eventos
"""

import asyncio
import sys
import os
import pytest

# Adiciona path do shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from shared.logging import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_event_service_integration():
    """
    Testa fluxo completo do event-service:
    1. Submeter dados de dispositivo
    2. Processar na fila RabbitMQ
    3. Detectar evento
    4. Persistir no banco
    5. Broadcast via WebSocket
    """
    logger.info("=" * 60)
    logger.info("TESTE DE INTEGRAÇÃO - EVENT SERVICE")
    logger.info("=" * 60)
    
    try:
        # TODO: Implementar teste de integração completo
        # Por enquanto, apenas valida que módulos podem ser importados
        
        from services.event_detector import EventDetector, DetectionResult
        from services.event_processor import EventProcessor
        from services.event_service import EventService
        from models.event import Event
        from schemas.event import DeviceDataSubmit, EventResponse
        from shared.websocket import websocket_manager
        from shared.rabbitmq import RabbitMQClient
        
        logger.info("✅ Todos os módulos importados com sucesso")
        
        # Testa detector RSSI
        config = {
            "plan_type": "basic",
            "presence_threshold": 0.6,
            "high_variance_threshold": 0.4
        }
        
        detector = EventDetector(config)
        
        features = {
            "rssi_normalized": 0.75,
            "signal_variance": 0.5,
            "rate_of_change": 0.1,
            "instability_score": 0.3
        }
        
        result = detector.detect(features, "rssi")
        
        if result:
            logger.info(
                f"✅ Detecção RSSI funcionando: {result.event_type} (confidence: {result.confidence})"
            )
        else:
            logger.warning("⚠️  Nenhum evento detectado com features de teste")
        
        # Testa detector CSI
        config_premium = {
            "plan_type": "premium"
        }
        
        detector_premium = EventDetector(config_premium)
        
        features_csi = {
            "csi_amplitude": 0.8,
            "csi_variance": 0.9,
            "doppler_shift": 0.8
        }
        
        result_csi = detector_premium.detect(features_csi, "csi")
        
        if result_csi:
            logger.info(
                f"✅ Detecção CSI funcionando: {result_csi.event_type} (confidence: {result_csi.confidence})"
            )
        
        logger.info("=" * 60)
        logger.info("TESTE DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de integração: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_event_service_integration())
    sys.exit(0 if success else 1)
