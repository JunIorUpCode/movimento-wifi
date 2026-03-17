"""
PerformanceService - Coleta e análise de métricas de performance do sistema.

Implementa:
- Coleta de métricas de tempo (captura, processamento, detecção, latência total)
- Coleta de métricas de recursos (memória, CPU)
- Persistência no banco de dados
- Cálculo de estatísticas (média, p95, p99)
- Alertas para latência alta (>500ms)
"""

from __future__ import annotations

import asyncio
import psutil
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.logging.structured_logger import get_logger
from app.models.models import PerformanceMetric


logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Métricas de performance de uma iteração do pipeline."""
    
    capture_time_ms: float
    processing_time_ms: float
    detection_time_ms: float
    total_latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class PerformanceStats:
    """Estatísticas agregadas de performance."""
    
    mean_capture_ms: float
    mean_processing_ms: float
    mean_detection_ms: float
    mean_total_latency_ms: float
    
    p95_capture_ms: float
    p95_processing_ms: float
    p95_detection_ms: float
    p95_total_latency_ms: float
    
    p99_capture_ms: float
    p99_processing_ms: float
    p99_detection_ms: float
    p99_total_latency_ms: float
    
    max_capture_ms: float
    max_processing_ms: float
    max_detection_ms: float
    max_total_latency_ms: float
    
    mean_memory_mb: float
    mean_cpu_percent: float
    
    sample_count: int
    period_start: datetime
    period_end: datetime


class PerformanceService:
    """Serviço de coleta e análise de métricas de performance."""
    
    _instance: Optional[PerformanceService] = None
    
    def __new__(cls) -> PerformanceService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        self._process = psutil.Process()
        self._metrics_buffer: List[PerformanceMetrics] = []
        self._buffer_size = 100  # Salva a cada 100 métricas
        self._high_latency_threshold_ms = 500.0
        self._high_latency_count = 0
    
    def get_current_resources(self) -> tuple[float, float]:
        """
        Obtém uso atual de recursos do sistema.
        
        Returns:
            Tupla (memory_mb, cpu_percent)
        """
        memory_mb = self._process.memory_info().rss / (1024 * 1024)
        cpu_percent = self._process.cpu_percent(interval=0.01)
        return memory_mb, cpu_percent
    
    async def record_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Registra métricas de performance.
        
        Args:
            metrics: Métricas coletadas
        """
        # Adiciona ao buffer
        self._metrics_buffer.append(metrics)
        
        # Verifica latência alta
        if metrics.total_latency_ms > self._high_latency_threshold_ms:
            self._high_latency_count += 1
            logger.warning(
                f"High latency detected: {metrics.total_latency_ms:.2f}ms",
                capture_ms=metrics.capture_time_ms,
                processing_ms=metrics.processing_time_ms,
                detection_ms=metrics.detection_time_ms,
                total_ms=metrics.total_latency_ms,
                memory_mb=metrics.memory_usage_mb,
                cpu_percent=metrics.cpu_usage_percent
            )
        
        # Persiste quando buffer está cheio
        if len(self._metrics_buffer) >= self._buffer_size:
            await self._flush_buffer()
    
    async def _flush_buffer(self) -> None:
        """Persiste métricas do buffer no banco de dados."""
        if not self._metrics_buffer:
            return
        
        try:
            async with async_session() as db:
                # Cria registros do banco
                db_metrics = [
                    PerformanceMetric(
                        timestamp=datetime.fromtimestamp(m.timestamp),
                        capture_time_ms=m.capture_time_ms,
                        processing_time_ms=m.processing_time_ms,
                        detection_time_ms=m.detection_time_ms,
                        total_latency_ms=m.total_latency_ms,
                        memory_usage_mb=m.memory_usage_mb,
                        cpu_usage_percent=m.cpu_usage_percent
                    )
                    for m in self._metrics_buffer
                ]
                
                db.add_all(db_metrics)
                await db.commit()
                
                logger.info(
                    f"Persisted {len(self._metrics_buffer)} performance metrics",
                    count=len(self._metrics_buffer),
                    high_latency_count=self._high_latency_count
                )
                
                # Limpa buffer
                self._metrics_buffer.clear()
                self._high_latency_count = 0
                
        except Exception as e:
            logger.error(f"Failed to persist performance metrics: {e}")
    
    async def get_statistics(
        self,
        hours: int = 24
    ) -> Optional[PerformanceStats]:
        """
        Calcula estatísticas de performance para um período.
        
        Args:
            hours: Número de horas para análise (padrão: 24)
            
        Returns:
            PerformanceStats ou None se não houver dados
        """
        try:
            async with async_session() as db:
                # Define período
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=hours)
                
                # Busca métricas do período
                result = await db.execute(
                    select(PerformanceMetric)
                    .where(PerformanceMetric.timestamp >= start_time)
                    .where(PerformanceMetric.timestamp <= end_time)
                    .order_by(PerformanceMetric.timestamp)
                )
                metrics = result.scalars().all()
                
                if not metrics:
                    return None
                
                # Extrai valores para cálculos
                capture_times = [m.capture_time_ms for m in metrics]
                processing_times = [m.processing_time_ms for m in metrics]
                detection_times = [m.detection_time_ms for m in metrics]
                total_latencies = [m.total_latency_ms for m in metrics]
                memory_values = [m.memory_usage_mb for m in metrics]
                cpu_values = [m.cpu_usage_percent for m in metrics]
                
                # Calcula estatísticas
                stats = PerformanceStats(
                    # Médias
                    mean_capture_ms=self._mean(capture_times),
                    mean_processing_ms=self._mean(processing_times),
                    mean_detection_ms=self._mean(detection_times),
                    mean_total_latency_ms=self._mean(total_latencies),
                    
                    # P95
                    p95_capture_ms=self._percentile(capture_times, 95),
                    p95_processing_ms=self._percentile(processing_times, 95),
                    p95_detection_ms=self._percentile(detection_times, 95),
                    p95_total_latency_ms=self._percentile(total_latencies, 95),
                    
                    # P99
                    p99_capture_ms=self._percentile(capture_times, 99),
                    p99_processing_ms=self._percentile(processing_times, 99),
                    p99_detection_ms=self._percentile(detection_times, 99),
                    p99_total_latency_ms=self._percentile(total_latencies, 99),
                    
                    # Máximos
                    max_capture_ms=max(capture_times),
                    max_processing_ms=max(processing_times),
                    max_detection_ms=max(detection_times),
                    max_total_latency_ms=max(total_latencies),
                    
                    # Recursos
                    mean_memory_mb=self._mean(memory_values),
                    mean_cpu_percent=self._mean(cpu_values),
                    
                    # Metadata
                    sample_count=len(metrics),
                    period_start=start_time,
                    period_end=end_time
                )
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to calculate performance statistics: {e}")
            return None
    
    async def cleanup_old_metrics(self, days: int = 7) -> int:
        """
        Remove métricas antigas do banco de dados.
        
        Args:
            days: Número de dias para manter (padrão: 7)
            
        Returns:
            Número de registros removidos
        """
        try:
            async with async_session() as db:
                cutoff_time = datetime.utcnow() - timedelta(days=days)
                
                result = await db.execute(
                    select(func.count(PerformanceMetric.id))
                    .where(PerformanceMetric.timestamp < cutoff_time)
                )
                count = result.scalar()
                
                if count > 0:
                    await db.execute(
                        select(PerformanceMetric)
                        .where(PerformanceMetric.timestamp < cutoff_time)
                    )
                    await db.commit()
                    
                    logger.info(
                        f"Cleaned up {count} old performance metrics",
                        days=days,
                        cutoff_time=cutoff_time.isoformat()
                    )
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
    
    @staticmethod
    def _mean(values: List[float]) -> float:
        """Calcula média."""
        return sum(values) / len(values) if values else 0.0
    
    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calcula percentil."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    async def force_flush(self) -> None:
        """Força persistência imediata do buffer."""
        await self._flush_buffer()


# Instância global
performance_service = PerformanceService()
