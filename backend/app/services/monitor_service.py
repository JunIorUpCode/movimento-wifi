"""
MonitorService — Serviço central de monitoramento em loop assíncrono.

Orquestra o pipeline: captura → processamento → detecção → broadcast → persistência.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional

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

    def set_simulation_mode(self, mode: str) -> None:
        """Altera o modo de simulação do MockSignalProvider."""
        if isinstance(self._provider, MockSignalProvider):
            self._provider.set_mode(SimulationMode(mode))

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
