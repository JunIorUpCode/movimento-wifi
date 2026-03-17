"""
MonitorService — Serviço central de monitoramento em loop assíncrono.

Orquestra o pipeline: captura → processamento → detecção → broadcast → persistência.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

from app.capture.base import SignalProvider
from app.capture.mock_provider import MockSignalProvider, SimulationMode
from app.capture.rssi_windows import RssiWindowsProvider
from app.db.database import async_session
from app.detection.base import DetectionResult, EventType
from app.detection.heuristic_detector import HeuristicDetector
from app.processing.signal_processor import ProcessedFeatures, SignalProcessor
from app.services.alert_service import AlertService, alert_service
from app.services.behavior_service import BehaviorService, behavior_service
from app.services.config_service import config_service
from app.services.history_service import HistoryService
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert
from app.services.performance_service import (
    PerformanceMetrics,
    PerformanceService,
    performance_service,
)


class MonitorService:
    """Serviço central de monitoramento."""

    _instance: MonitorService | None = None

    def __new__(cls) -> MonitorService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # AUTO-DETECÇÃO DE HARDWARE ATIVADA!
        # O sistema detecta automaticamente o melhor provider disponível:
        # 1. CSI (se hardware disponível) - melhor qualidade
        # 2. RSSI Windows (se Windows) - boa qualidade
        # 3. RSSI Linux (se Linux/Raspberry) - boa qualidade
        # 4. Mock (fallback) - apenas simulação
        from app.capture.provider_factory import create_auto_provider
        self._provider: SignalProvider = create_auto_provider()
        
        self._processor = SignalProcessor()
        self._detector = HeuristicDetector()
        self._alert_service: AlertService = alert_service
        self._behavior_service: BehaviorService = behavior_service
        self._performance_service: PerformanceService = performance_service
        self._notification_service: NotificationService = NotificationService()

        self._is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: float = time.time()

        # Estado atual
        self._current_result: Optional[DetectionResult] = None
        self._current_features: Optional[ProcessedFeatures] = None
        self._current_signal: dict[str, Any] = {}
        self._last_persisted_event: Optional[str] = None

        # WebSocket connections
        self._ws_connections: set = set()

        # Cliente RabbitMQ — injetado via initialize_rabbitmq()
        # Permanece None se RabbitMQ não estiver disponível (modo standalone)
        self._rabbitmq_client: Optional[Any] = None

        # Power save
        self._power_save_active: bool = False
        self._pre_power_save_interval: float = 1.0

    # --- Propriedades ---

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def current_result(self) -> Optional[DetectionResult]:
        return self._current_result

    @property
    def current_features(self) -> Optional[ProcessedFeatures]:
        return self._current_features

    @property
    def current_signal(self) -> dict[str, Any]:
        return self._current_signal

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time

    @property
    def simulation_mode(self) -> str:
        if isinstance(self._provider, MockSignalProvider):
            return self._provider.mode.value
        elif isinstance(self._provider, RssiWindowsProvider):
            return "real_wifi"
        return "real"

    # --- WebSocket ---

    def register_ws(self, ws: Any) -> None:
        self._ws_connections.add(ws)

    def unregister_ws(self, ws: Any) -> None:
        self._ws_connections.discard(ws)

    async def _broadcast(self, data: dict) -> None:
        """Envia dados para todos os clientes WebSocket conectados."""
        dead = set()
        for ws in self._ws_connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self._ws_connections -= dead

    async def broadcast_calibration_progress(
        self,
        profile_name: str,
        elapsed_seconds: float,
        duration_seconds: int,
        phase: str = "collecting",
    ) -> None:
        """
        Transmite progresso da calibração para todos os clientes WebSocket.

        Args:
            profile_name: Nome do perfil em calibração
            elapsed_seconds: Segundos decorridos
            duration_seconds: Duração total planejada
            phase: Fase atual ('collecting', 'calculating', 'done', 'error')
        """
        progress_pct = min(100.0, round((elapsed_seconds / duration_seconds) * 100, 1)) if duration_seconds else 0.0
        await self._broadcast({
            "type": "calibration_progress",
            "data": {
                "profile_name": profile_name,
                "elapsed_seconds": round(elapsed_seconds, 1),
                "duration_seconds": duration_seconds,
                "progress_percent": progress_pct,
                "phase": phase,
            },
        })

    async def broadcast_notification_sent(
        self,
        channel: str,
        event_type: str,
        confidence: float,
        success: bool,
        recipient: str = "",
    ) -> None:
        """
        Transmite evento de notificação enviada para todos os clientes WebSocket.

        Args:
            channel: Canal utilizado (telegram, whatsapp, webhook)
            event_type: Tipo do evento que gerou a notificação
            confidence: Confiança da detecção
            success: True se a notificação foi enviada com sucesso
            recipient: Destinatário (sem expor dados sensíveis)
        """
        await self._broadcast({
            "type": "notification_sent",
            "data": {
                "channel": channel,
                "event_type": event_type,
                "confidence": round(confidence, 4),
                "success": success,
                "recipient": recipient,
            },
        })

    async def broadcast_anomaly_detected(
        self,
        event_type: str,
        confidence: float,
        details: dict,
    ) -> None:
        """
        Transmite evento de anomalia detectada para todos os clientes WebSocket.

        Args:
            event_type: Tipo de anomalia (fall_suspected, prolonged_inactivity)
            confidence: Confiança da detecção (0.0–1.0)
            details: Detalhes adicionais da anomalia
        """
        import time as _time
        await self._broadcast({
            "type": "anomaly_detected",
            "data": {
                "event_type": event_type,
                "confidence": round(confidence, 4),
                "timestamp": _time.time(),
                "details": details,
            },
        })

    # --- Controle ---

    async def start(self) -> None:
        """Inicia o loop de monitoramento."""
        if self._is_running:
            return
        self._is_running = True
        await self._provider.start()
        self._processor.reset()
        self._detector.reset()
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Para o loop de monitoramento."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._provider.stop()
        
        # Flush remaining performance metrics
        await self._performance_service.force_flush()

    @property
    def power_save_active(self) -> bool:
        return self._power_save_active

    def set_simulation_mode(self, mode: str) -> None:
        """Altera o modo de simulação do MockSignalProvider."""
        if isinstance(self._provider, MockSignalProvider):
            self._provider.set_mode(SimulationMode(mode))

    def enable_power_save(self) -> dict:
        """
        Ativa modo de economia de energia.

        Aumenta o intervalo de amostragem para 5 s e reduz a sensibilidade
        de movimento para minimizar processamento e consumo.
        Salva os valores atuais para restauração posterior.
        """
        if self._power_save_active:
            return {"status": "already_active", "sampling_interval": config_service.config.sampling_interval}

        self._pre_power_save_interval = config_service.config.sampling_interval
        from app.schemas.schemas import ConfigIn
        config_service.update(ConfigIn(sampling_interval=5.0, movement_sensitivity=0.8))
        self._power_save_active = True
        logger.info("Modo power save ativado — amostragem reduzida para 5s")
        return {"status": "enabled", "sampling_interval": 5.0}

    def disable_power_save(self) -> dict:
        """
        Desativa modo de economia de energia, restaurando configuração anterior.
        """
        if not self._power_save_active:
            return {"status": "not_active", "sampling_interval": config_service.config.sampling_interval}

        from app.schemas.schemas import ConfigIn
        config_service.update(ConfigIn(
            sampling_interval=self._pre_power_save_interval,
            movement_sensitivity=0.5,
        ))
        self._power_save_active = False
        logger.info(f"Modo power save desativado — amostragem restaurada para {self._pre_power_save_interval}s")
        return {"status": "disabled", "sampling_interval": self._pre_power_save_interval}

    async def initialize_rabbitmq(self, client: Any) -> None:
        """
        Injeta o cliente RabbitMQ no MonitorService.

        Deve ser chamado uma vez durante o startup da aplicação, após
        a conexão com o RabbitMQ ser estabelecida. Segue o padrão de
        injeção de dependência para facilitar testes e modo standalone.

        Args:
            client: Instância de RabbitMQClient (de shared/rabbitmq.py)
        """
        self._rabbitmq_client = client
        logger.info("✓ RabbitMQ conectado ao MonitorService")

    async def reload_detector(self, model_path: str) -> dict:
        """
        Troca o detector atual por um MLDetector com o modelo especificado.

        Se o detector já for MLDetector, recarrega o modelo no lugar.
        Se for HeuristicDetector, instancia um novo MLDetector.
        O loop de monitoramento passa a usar o novo detector imediatamente.

        Args:
            model_path: Caminho relativo ou absoluto para o arquivo .pkl

        Returns:
            dict com 'success' (bool) e 'message' (str)
        """
        from app.detection.ml_detector import MLDetector

        if isinstance(self._detector, MLDetector):
            # Recarrega modelo no detector existente
            success = self._detector.reload_model(model_path)
            if success:
                return {"success": True, "message": f"Modelo recarregado: {model_path}"}
            return {"success": False, "message": f"Falha ao recarregar modelo: {model_path}"}

        # Substitui HeuristicDetector por MLDetector
        try:
            new_detector = MLDetector(model_path=model_path)
            self._detector = new_detector
            logger.info(f"✓ Detector trocado para MLDetector: {model_path}")
            return {"success": True, "message": f"MLDetector ativado: {model_path}"}
        except Exception as e:
            logger.error(f"Erro ao ativar MLDetector: {e}")
            return {"success": False, "message": str(e)}

    async def _publish_event(
        self,
        result: DetectionResult,
        signal: Any,
        features: ProcessedFeatures,
    ) -> None:
        """
        Publica evento detectado na fila RabbitMQ 'event_processing'.

        Chamado apenas quando há mudança de estado (should_persist=True).
        Se RabbitMQ não estiver disponível, registra warning e continua
        sem interromper o loop de monitoramento.

        Args:
            result: Resultado da detecção (tipo de evento, confiança)
            signal: Sinal bruto capturado (contém timestamp, provider)
            features: Features processadas do sinal
        """
        if self._rabbitmq_client is None:
            return  # Modo standalone — RabbitMQ não configurado

        import os
        payload = {
            # tenant_id fixo para modo local; em multi-tenant vem do JWT
            "tenant_id": os.getenv("WIFISENSE_TENANT_ID", "local-tenant-00000000"),
            "device_id": os.getenv("WIFISENSE_DEVICE_ID", "local-device-00000000"),
            "event_type": result.event_type.value,
            "confidence": round(result.confidence, 4),
            "timestamp": signal.timestamp,
            "data_type": "rssi",  # Atualizar para "csi" quando hardware CSI disponível
            "features": {
                "rssi_normalized": round(features.rssi_normalized, 4),
                "rssi_smoothed": round(features.rssi_smoothed, 4),
                "rate_of_change": round(features.rate_of_change, 4),
                "signal_energy": round(features.signal_energy, 4),
                "signal_variance": round(features.signal_variance, 4),
                "instability_score": round(features.instability_score, 4),
                "csi_mean_amplitude": round(features.csi_mean_amplitude, 4),
            },
            "metadata": result.details,
        }

        try:
            await self._rabbitmq_client.publish("event_processing", payload)
            logger.debug(
                f"Evento publicado no RabbitMQ: {result.event_type.value} "
                f"(confidence={result.confidence:.3f})"
            )
        except Exception as e:
            logger.warning(f"Falha ao publicar evento no RabbitMQ: {e}")

    # --- Loop principal ---

    async def _monitor_loop(self) -> None:
        """Loop principal do monitoramento."""
        sample_count = 0

        while self._is_running:
            try:
                interval = config_service.config.sampling_interval
                
                # Inicia medição de performance
                loop_start = time.time()

                # 1. Captura
                capture_start = time.time()
                signal = await self._provider.get_signal()
                capture_time = (time.time() - capture_start) * 1000  # ms
                
                self._current_signal = {
                    "rssi": round(signal.rssi, 2),
                    "csi_mean": round(sum(signal.csi_amplitude) / max(len(signal.csi_amplitude), 1), 2),
                    "timestamp": signal.timestamp,
                }

                # 2. Processamento
                processing_start = time.time()
                features = self._processor.process(signal)
                processing_time = (time.time() - processing_start) * 1000  # ms
                
                self._current_features = features

                # 3. Atualiza limiares do detector com config atual
                self._detector.update_config(config_service.get_threshold_config())

                # 4. Detecção
                detection_start = time.time()
                result = self._detector.detect(features)
                detection_time = (time.time() - detection_start) * 1000  # ms
                
                self._current_result = result

                # 5. Alertas
                alert = self._alert_service.evaluate(result.event_type, result.confidence)

                # 5.1. Enviar notificações se alerta foi gerado
                if alert:
                    await self._send_notification(result, alert)

                # 5.2. Detecção de anomalias comportamentais
                behavior_anomaly = None
                try:
                    is_anomaly, anomaly_score, description = (
                        await self._behavior_service.detect_anomalous_behavior(
                            result.event_type, signal.timestamp
                        )
                    )
                    if is_anomaly:
                        behavior_anomaly = {
                            "is_anomaly": is_anomaly,
                            "score": round(anomaly_score, 3),
                            "description": description,
                        }
                except Exception as e:
                    # Não falha o loop se detecção de anomalia falhar
                    print(f"[MonitorService] Erro na detecção de anomalia: {e}")

                # 6. Persistência (salva apenas mudanças de estado ou eventos críticos)
                should_persist = (
                    result.event_type.value != self._last_persisted_event
                    or result.event_type in (EventType.FALL_SUSPECTED, EventType.PROLONGED_INACTIVITY)
                )

                if should_persist:
                    self._last_persisted_event = result.event_type.value
                    async with async_session() as db:
                        await HistoryService.save_event(
                            db=db,
                            event_type=result.event_type.value,
                            confidence=result.confidence,
                            provider=signal.provider,
                            metadata=result.details,
                        )

                    # 6.5. Publica evento no RabbitMQ (apenas em mudanças de estado)
                    await self._publish_event(result, signal, features)

                # 7. Broadcast WebSocket
                payload = {
                    "event_type": result.event_type.value,
                    "confidence": round(result.confidence, 3),
                    "timestamp": signal.timestamp,
                    "signal": self._current_signal,
                    "features": {
                        "rssi_normalized": round(features.rssi_normalized, 3),
                        "rssi_smoothed": round(features.rssi_smoothed, 2),
                        "signal_energy": round(features.signal_energy, 2),
                        "signal_variance": round(features.signal_variance, 3),
                        "rate_of_change": round(features.rate_of_change, 3),
                        "instability_score": round(features.instability_score, 3),
                        "csi_mean_amplitude": round(features.csi_mean_amplitude, 2),
                    },
                    "alert": alert.message if alert else None,
                    "behavior_anomaly": behavior_anomaly,
                }
                await self._broadcast(payload)

                # 7.1. Broadcast anomaly_detected para eventos críticos de alta confiança
                if result.event_type.value in ("fall_suspected", "prolonged_inactivity") and result.confidence >= 0.85:
                    await self.broadcast_anomaly_detected(
                        event_type=result.event_type.value,
                        confidence=result.confidence,
                        details=result.details,
                    )

                # 8. Coleta de métricas de performance
                total_latency = (time.time() - loop_start) * 1000  # ms
                memory_mb, cpu_percent = self._performance_service.get_current_resources()
                
                metrics = PerformanceMetrics(
                    capture_time_ms=capture_time,
                    processing_time_ms=processing_time,
                    detection_time_ms=detection_time,
                    total_latency_ms=total_latency,
                    memory_usage_mb=memory_mb,
                    cpu_usage_percent=cpu_percent,
                    timestamp=signal.timestamp
                )
                
                await self._performance_service.record_metrics(metrics)

                sample_count += 1
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MonitorService] Erro no loop: {e}")
                await asyncio.sleep(1)

    async def _send_notification(self, result: DetectionResult, alert_message: str) -> None:
        """Envia notificação para eventos detectados.
        
        Cria um Alert e envia via NotificationService.
        
        Args:
            result: Resultado da detecção
            alert_message: Mensagem do alerta gerada pelo AlertService
        """
        try:
            alert = Alert(
                event_type=result.event_type.value,
                confidence=result.confidence,
                timestamp=time.time(),  # Usa timestamp atual
                message=alert_message,
                details=result.details
            )
            
            await self._notification_service.send_alert(alert)
        except Exception as e:
            # Não propaga exceção para não interromper o loop de monitoramento
            print(f"[MonitorService] Erro ao enviar notificação: {e}")


# Instância global
monitor_service = MonitorService()
