"""
Testes para Task 4: Sistema de Métricas de Performance

Valida:
- Coleta de métricas no MonitorService
- PerformanceMetrics dataclass
- Persistência de métricas no banco
- Cálculo de estatísticas (média, p95, p99)
- Warning para latência >500ms

Requisitos: 26.1, 26.2, 26.4, 26.6
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.performance_service import (
    PerformanceMetrics,
    PerformanceService,
    PerformanceStats,
)
from app.models.models import PerformanceMetric
from app.db.database import async_session, init_db
from sqlalchemy import select


@pytest.fixture
async def setup_db():
    """Setup test database."""
    await init_db()
    yield
    # Cleanup is handled by test isolation


@pytest.fixture
def perf_service():
    """Create a fresh PerformanceService instance."""
    service = PerformanceService()
    service._metrics_buffer.clear()
    service._high_latency_count = 0
    return service


class TestPerformanceMetricsDataclass:
    """Testa PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Testa criação de métricas."""
        metrics = PerformanceMetrics(
            capture_time_ms=10.5,
            processing_time_ms=5.2,
            detection_time_ms=3.1,
            total_latency_ms=18.8,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.5
        )
        
        assert metrics.capture_time_ms == 10.5
        assert metrics.processing_time_ms == 5.2
        assert metrics.detection_time_ms == 3.1
        assert metrics.total_latency_ms == 18.8
        assert metrics.memory_usage_mb == 150.0
        assert metrics.cpu_usage_percent == 25.5
        assert metrics.timestamp > 0  # Auto-generated
    
    def test_metrics_with_timestamp(self):
        """Testa criação de métricas com timestamp customizado."""
        custom_time = time.time() - 100
        metrics = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0,
            timestamp=custom_time
        )
        
        assert metrics.timestamp == custom_time


class TestPerformanceServiceResourceCollection:
    """Testa coleta de recursos do sistema."""
    
    def test_get_current_resources(self, perf_service):
        """Testa obtenção de recursos atuais."""
        memory_mb, cpu_percent = perf_service.get_current_resources()
        
        # Valida que valores são razoáveis
        assert memory_mb > 0
        assert memory_mb < 10000  # Menos de 10GB
        assert cpu_percent >= 0
        assert cpu_percent <= 100


class TestPerformanceServiceRecording:
    """Testa gravação de métricas."""
    
    @pytest.mark.asyncio
    async def test_record_metrics_buffering(self, perf_service, setup_db):
        """Testa que métricas são bufferizadas antes de persistir."""
        metrics = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0
        )
        
        await perf_service.record_metrics(metrics)
        
        # Deve estar no buffer
        assert len(perf_service._metrics_buffer) == 1
        assert perf_service._metrics_buffer[0] == metrics
    
    @pytest.mark.asyncio
    async def test_record_metrics_high_latency_warning(self, perf_service, setup_db):
        """Testa warning para latência alta (>500ms)."""
        # Requisito 26.6: Adicionar warning para latência >500ms
        metrics = PerformanceMetrics(
            capture_time_ms=200.0,
            processing_time_ms=150.0,
            detection_time_ms=200.0,
            total_latency_ms=550.0,  # > 500ms
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0
        )
        
        await perf_service.record_metrics(metrics)
        
        # Deve incrementar contador de alta latência
        assert perf_service._high_latency_count == 1
    
    @pytest.mark.asyncio
    async def test_record_metrics_auto_flush(self, perf_service, setup_db):
        """Testa flush automático quando buffer está cheio."""
        # Requisito 26.1: Persistência de métricas no banco
        perf_service._buffer_size = 5  # Reduz para teste
        
        # Adiciona métricas até encher buffer
        for i in range(5):
            metrics = PerformanceMetrics(
                capture_time_ms=10.0 + i,
                processing_time_ms=5.0,
                detection_time_ms=3.0,
                total_latency_ms=18.0,
                memory_usage_mb=150.0,
                cpu_usage_percent=25.0
            )
            await perf_service.record_metrics(metrics)
        
        # Buffer deve ter sido limpo após flush
        assert len(perf_service._metrics_buffer) == 0
        
        # Verifica persistência no banco
        async with async_session() as db:
            result = await db.execute(select(PerformanceMetric))
            db_metrics = result.scalars().all()
            assert len(db_metrics) == 5


class TestPerformanceServicePersistence:
    """Testa persistência de métricas no banco."""
    
    @pytest.mark.asyncio
    async def test_flush_buffer_persists_to_db(self, perf_service, setup_db):
        """Testa que flush persiste métricas no banco."""
        # Requisito 26.1: Persistência de métricas no banco
        metrics1 = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0
        )
        
        metrics2 = PerformanceMetrics(
            capture_time_ms=12.0,
            processing_time_ms=6.0,
            detection_time_ms=4.0,
            total_latency_ms=22.0,
            memory_usage_mb=155.0,
            cpu_usage_percent=30.0
        )
        
        perf_service._metrics_buffer.extend([metrics1, metrics2])
        await perf_service._flush_buffer()
        
        # Verifica no banco
        async with async_session() as db:
            result = await db.execute(select(PerformanceMetric))
            db_metrics = result.scalars().all()
            
            assert len(db_metrics) >= 2
            
            # Verifica últimas 2 métricas
            last_two = db_metrics[-2:]
            assert last_two[0].capture_time_ms == 10.0
            assert last_two[0].processing_time_ms == 5.0
            assert last_two[1].capture_time_ms == 12.0
            assert last_two[1].processing_time_ms == 6.0
    
    @pytest.mark.asyncio
    async def test_force_flush(self, perf_service, setup_db):
        """Testa flush forçado."""
        metrics = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0
        )
        
        perf_service._metrics_buffer.append(metrics)
        await perf_service.force_flush()
        
        # Buffer deve estar vazio
        assert len(perf_service._metrics_buffer) == 0
        
        # Verifica no banco
        async with async_session() as db:
            result = await db.execute(select(PerformanceMetric))
            db_metrics = result.scalars().all()
            assert len(db_metrics) >= 1


class TestPerformanceServiceStatistics:
    """Testa cálculo de estatísticas."""
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_empty(self, perf_service, setup_db):
        """Testa estatísticas com banco vazio."""
        stats = await perf_service.get_statistics(hours=1)
        assert stats is None
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_mean(self, perf_service, setup_db):
        """Testa cálculo de média."""
        # Requisito 26.2: Calcular estatísticas (média)
        
        # Adiciona métricas conhecidas
        test_metrics = [
            PerformanceMetrics(
                capture_time_ms=10.0,
                processing_time_ms=5.0,
                detection_time_ms=3.0,
                total_latency_ms=18.0,
                memory_usage_mb=150.0,
                cpu_usage_percent=25.0
            ),
            PerformanceMetrics(
                capture_time_ms=20.0,
                processing_time_ms=10.0,
                detection_time_ms=5.0,
                total_latency_ms=35.0,
                memory_usage_mb=160.0,
                cpu_usage_percent=30.0
            ),
            PerformanceMetrics(
                capture_time_ms=30.0,
                processing_time_ms=15.0,
                detection_time_ms=7.0,
                total_latency_ms=52.0,
                memory_usage_mb=170.0,
                cpu_usage_percent=35.0
            ),
        ]
        
        perf_service._metrics_buffer.extend(test_metrics)
        await perf_service._flush_buffer()
        
        # Calcula estatísticas
        stats = await perf_service.get_statistics(hours=1)
        
        assert stats is not None
        assert stats.sample_count == 3
        
        # Verifica médias
        assert stats.mean_capture_ms == 20.0  # (10+20+30)/3
        assert stats.mean_processing_ms == 10.0  # (5+10+15)/3
        assert stats.mean_detection_ms == 5.0  # (3+5+7)/3
        assert stats.mean_total_latency_ms == 35.0  # (18+35+52)/3
        assert stats.mean_memory_mb == 160.0  # (150+160+170)/3
        assert stats.mean_cpu_percent == 30.0  # (25+30+35)/3
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_percentiles(self, perf_service, setup_db):
        """Testa cálculo de percentis (p95, p99)."""
        # Requisito 26.2: Calcular estatísticas (p95, p99)
        
        # Adiciona 100 métricas com valores crescentes
        test_metrics = []
        for i in range(100):
            metrics = PerformanceMetrics(
                capture_time_ms=float(i + 1),
                processing_time_ms=float(i + 1) * 0.5,
                detection_time_ms=float(i + 1) * 0.3,
                total_latency_ms=float(i + 1) * 2,
                memory_usage_mb=150.0 + i,
                cpu_usage_percent=25.0 + (i * 0.5)
            )
            test_metrics.append(metrics)
        
        perf_service._metrics_buffer.extend(test_metrics)
        await perf_service._flush_buffer()
        
        # Calcula estatísticas
        stats = await perf_service.get_statistics(hours=1)
        
        assert stats is not None
        assert stats.sample_count == 100
        
        # Verifica p95 (95º valor de 100 = 95)
        assert stats.p95_capture_ms == 95.0
        assert stats.p95_processing_ms == 95.0 * 0.5
        assert stats.p95_detection_ms == 95.0 * 0.3
        assert stats.p95_total_latency_ms == 95.0 * 2
        
        # Verifica p99 (99º valor de 100 = 99)
        assert stats.p99_capture_ms == 99.0
        assert stats.p99_processing_ms == 99.0 * 0.5
        assert stats.p99_detection_ms == 99.0 * 0.3
        assert stats.p99_total_latency_ms == 99.0 * 2
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_max(self, perf_service, setup_db):
        """Testa cálculo de máximos."""
        test_metrics = [
            PerformanceMetrics(
                capture_time_ms=10.0,
                processing_time_ms=5.0,
                detection_time_ms=3.0,
                total_latency_ms=18.0,
                memory_usage_mb=150.0,
                cpu_usage_percent=25.0
            ),
            PerformanceMetrics(
                capture_time_ms=50.0,  # Max
                processing_time_ms=30.0,  # Max
                detection_time_ms=20.0,  # Max
                total_latency_ms=100.0,  # Max
                memory_usage_mb=200.0,
                cpu_usage_percent=50.0
            ),
            PerformanceMetrics(
                capture_time_ms=20.0,
                processing_time_ms=10.0,
                detection_time_ms=5.0,
                total_latency_ms=35.0,
                memory_usage_mb=160.0,
                cpu_usage_percent=30.0
            ),
        ]
        
        perf_service._metrics_buffer.extend(test_metrics)
        await perf_service._flush_buffer()
        
        stats = await perf_service.get_statistics(hours=1)
        
        assert stats is not None
        assert stats.max_capture_ms == 50.0
        assert stats.max_processing_ms == 30.0
        assert stats.max_detection_ms == 20.0
        assert stats.max_total_latency_ms == 100.0


class TestPerformanceServiceCleanup:
    """Testa limpeza de métricas antigas."""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, perf_service, setup_db):
        """Testa remoção de métricas antigas."""
        # Adiciona métricas antigas (8 dias atrás)
        old_time = time.time() - (8 * 24 * 60 * 60)
        old_metrics = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0,
            timestamp=old_time
        )
        
        # Adiciona métricas recentes
        recent_metrics = PerformanceMetrics(
            capture_time_ms=10.0,
            processing_time_ms=5.0,
            detection_time_ms=3.0,
            total_latency_ms=18.0,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0
        )
        
        perf_service._metrics_buffer.extend([old_metrics, recent_metrics])
        await perf_service._flush_buffer()
        
        # Limpa métricas com mais de 7 dias
        count = await perf_service.cleanup_old_metrics(days=7)
        
        # Deve ter removido pelo menos a métrica antiga
        assert count >= 1


class TestPerformanceStatsDataclass:
    """Testa PerformanceStats dataclass."""
    
    def test_stats_creation(self):
        """Testa criação de estatísticas."""
        now = datetime.utcnow()
        stats = PerformanceStats(
            mean_capture_ms=10.0,
            mean_processing_ms=5.0,
            mean_detection_ms=3.0,
            mean_total_latency_ms=18.0,
            p95_capture_ms=15.0,
            p95_processing_ms=8.0,
            p95_detection_ms=5.0,
            p95_total_latency_ms=28.0,
            p99_capture_ms=20.0,
            p99_processing_ms=10.0,
            p99_detection_ms=7.0,
            p99_total_latency_ms=37.0,
            max_capture_ms=25.0,
            max_processing_ms=12.0,
            max_detection_ms=9.0,
            max_total_latency_ms=46.0,
            mean_memory_mb=150.0,
            mean_cpu_percent=25.0,
            sample_count=100,
            period_start=now - timedelta(hours=24),
            period_end=now
        )
        
        assert stats.mean_capture_ms == 10.0
        assert stats.p95_total_latency_ms == 28.0
        assert stats.p99_detection_ms == 7.0
        assert stats.max_processing_ms == 12.0
        assert stats.sample_count == 100


def test_integration_full_pipeline():
    """Teste de integração: pipeline completo de métricas."""
    # Requisitos: 26.1, 26.2, 26.4, 26.6
    
    async def run_test():
        await init_db()
        
        service = PerformanceService()
        service._metrics_buffer.clear()
        service._buffer_size = 10
        
        # Simula coleta de métricas
        for i in range(15):
            latency = 100.0 + (i * 50)  # Algumas com latência alta
            metrics = PerformanceMetrics(
                capture_time_ms=10.0 + i,
                processing_time_ms=5.0 + i,
                detection_time_ms=3.0 + i,
                total_latency_ms=latency,
                memory_usage_mb=150.0 + i,
                cpu_usage_percent=25.0 + i
            )
            await service.record_metrics(metrics)
        
        # Força flush final
        await service.force_flush()
        
        # Verifica estatísticas
        stats = await service.get_statistics(hours=1)
        
        assert stats is not None
        assert stats.sample_count == 15
        assert stats.mean_capture_ms > 0
        assert stats.p95_total_latency_ms > stats.mean_total_latency_ms
        assert stats.p99_total_latency_ms > stats.p95_total_latency_ms
        assert stats.max_total_latency_ms >= stats.p99_total_latency_ms
        
        print("\n✅ Task 4 - Sistema de Métricas de Performance: COMPLETO")
        print(f"   - Métricas coletadas: {stats.sample_count}")
        print(f"   - Latência média: {stats.mean_total_latency_ms:.2f}ms")
        print(f"   - Latência p95: {stats.p95_total_latency_ms:.2f}ms")
        print(f"   - Latência p99: {stats.p99_total_latency_ms:.2f}ms")
        print(f"   - Latência máxima: {stats.max_total_latency_ms:.2f}ms")
        print(f"   - Memória média: {stats.mean_memory_mb:.2f}MB")
        print(f"   - CPU média: {stats.mean_cpu_percent:.2f}%")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    print("Executando testes da Task 4: Sistema de Métricas de Performance\n")
    pytest.main([__file__, "-v", "-s"])
