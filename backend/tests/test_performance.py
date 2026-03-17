"""
test_performance.py — Tarefa 41: Testes de Performance

Valida:
- Latência do SignalProcessor < 10ms por amostra
- Latência do HeuristicDetector < 5ms por detecção
- Pipeline completo (Provider + Processor + Detector) < 100ms
- Throughput ≥ 100 amostras/segundo
- Memória do SignalProcessor bounded (window_size)
"""

import time
import asyncio
import sys

import pytest

from app.capture.base import SignalData
from app.processing.signal_processor import SignalProcessor
from app.detection.base import EventType
from app.detection.heuristic_detector import HeuristicDetector, ThresholdConfig


def _make_signal(rssi: float = -60.0, n_csi: int = 30) -> SignalData:
    return SignalData(
        rssi=rssi,
        csi_amplitude=[1.5] * n_csi,
        timestamp=time.time(),
        provider="perf_test",
    )


def _make_features(rssi_norm: float = 0.5):
    from app.processing.signal_processor import ProcessedFeatures
    return ProcessedFeatures(
        rssi_normalized=rssi_norm,
        rssi_smoothed=-55.0,
        signal_energy=3.0,
        signal_variance=0.5,
        rate_of_change=0.3,
        instability_score=0.2,
        csi_mean_amplitude=2.0,
        csi_std_amplitude=0.3,
        raw_rssi=-55.0,
        timestamp=time.time(),
    )


class TestSignalProcessorLatency:
    """SignalProcessor deve processar cada amostra em < 10ms."""

    LATENCY_LIMIT_MS = 10.0

    def test_single_sample_latency(self):
        proc = SignalProcessor()
        signal = _make_signal()

        start = time.perf_counter()
        proc.process(signal)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.LATENCY_LIMIT_MS, (
            f"SignalProcessor.process() levou {elapsed_ms:.2f}ms (limite: {self.LATENCY_LIMIT_MS}ms)"
        )

    def test_100_samples_total_latency(self):
        proc = SignalProcessor()
        signal = _make_signal()

        start = time.perf_counter()
        for _ in range(100):
            proc.process(signal)
        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / 100

        assert avg_ms < self.LATENCY_LIMIT_MS, (
            f"Latência média por amostra: {avg_ms:.3f}ms (limite: {self.LATENCY_LIMIT_MS}ms)"
        )

    def test_1000_samples_throughput(self):
        """Deve processar ≥ 100 amostras/segundo."""
        proc = SignalProcessor()
        signal = _make_signal()
        n = 1000

        start = time.perf_counter()
        for _ in range(n):
            proc.process(signal)
        elapsed_s = time.perf_counter() - start

        throughput = n / elapsed_s
        assert throughput >= 100, (
            f"Throughput: {throughput:.0f} amostras/s (mínimo: 100)"
        )


class TestHeuristicDetectorLatency:
    """HeuristicDetector deve classificar cada amostra em < 5ms."""

    LATENCY_LIMIT_MS = 5.0

    def test_single_detection_latency(self):
        detector = HeuristicDetector()
        features = _make_features()

        start = time.perf_counter()
        detector.detect(features)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.LATENCY_LIMIT_MS, (
            f"HeuristicDetector.detect() levou {elapsed_ms:.2f}ms (limite: {self.LATENCY_LIMIT_MS}ms)"
        )

    def test_100_detections_average_latency(self):
        detector = HeuristicDetector()
        features = _make_features()

        start = time.perf_counter()
        for _ in range(100):
            detector.detect(features)
        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / 100

        assert avg_ms < self.LATENCY_LIMIT_MS, (
            f"Latência média por detecção: {avg_ms:.3f}ms (limite: {self.LATENCY_LIMIT_MS}ms)"
        )

    def test_fall_detection_latency(self):
        """Detecção de queda não deve ser mais lenta que o limite."""
        detector = HeuristicDetector()
        from app.processing.signal_processor import ProcessedFeatures
        fall_features = ProcessedFeatures(
            rssi_normalized=0.9,
            rssi_smoothed=-30.0,
            signal_energy=30.0,
            signal_variance=10.0,
            rate_of_change=20.0,
            instability_score=0.95,
            csi_mean_amplitude=12.0,
            csi_std_amplitude=4.0,
            raw_rssi=-30.0,
            timestamp=time.time(),
        )
        start = time.perf_counter()
        result = detector.detect(fall_features)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.event_type == EventType.FALL_SUSPECTED
        assert elapsed_ms < self.LATENCY_LIMIT_MS


class TestFullPipelineLatency:
    """Pipeline completo (captura + processamento + detecção) < 100ms."""

    PIPELINE_LIMIT_MS = 100.0

    def test_pipeline_single_cycle_latency(self):
        proc = SignalProcessor()
        detector = HeuristicDetector()
        signal = _make_signal()

        start = time.perf_counter()
        features = proc.process(signal)
        detector.detect(features)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.PIPELINE_LIMIT_MS, (
            f"Pipeline levou {elapsed_ms:.2f}ms (limite: {self.PIPELINE_LIMIT_MS}ms)"
        )

    def test_pipeline_50_cycles_average(self):
        proc = SignalProcessor()
        detector = HeuristicDetector()
        signal = _make_signal()
        n = 50

        times = []
        for _ in range(n):
            start = time.perf_counter()
            features = proc.process(signal)
            detector.detect(features)
            times.append((time.perf_counter() - start) * 1000)

        avg_ms = sum(times) / len(times)
        p95_ms = sorted(times)[int(0.95 * n)]

        assert avg_ms < self.PIPELINE_LIMIT_MS, (
            f"Latência média do pipeline: {avg_ms:.2f}ms (limite: {self.PIPELINE_LIMIT_MS}ms)"
        )
        assert p95_ms < self.PIPELINE_LIMIT_MS * 2, (
            f"P95 do pipeline: {p95_ms:.2f}ms (limite: {self.PIPELINE_LIMIT_MS * 2}ms)"
        )

    def test_async_pipeline_latency(self):
        """Testa pipeline com MockProvider real."""
        from app.capture.mock_provider import MockSignalProvider, SimulationMode

        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.STILL)

            proc = SignalProcessor()
            detector = HeuristicDetector()

            times = []
            for _ in range(20):
                start = time.perf_counter()
                signal = await provider.get_signal()
                features = proc.process(signal)
                detector.detect(features)
                times.append((time.perf_counter() - start) * 1000)

            await provider.stop()
            return times

        times = asyncio.run(_inner())
        avg_ms = sum(times) / len(times)
        assert avg_ms < self.PIPELINE_LIMIT_MS


class TestMemoryBounds:
    """Testa que as estruturas têm uso de memória delimitado."""

    def test_signal_processor_buffer_bounded(self):
        """Buffer do SignalProcessor não excede window_size."""
        window = 20
        proc = SignalProcessor(window_size=window)

        for i in range(100):
            proc.process(_make_signal(rssi=float(-60 - i % 10)))

        assert len(proc._rssi_buffer) <= window
        assert len(proc._energy_buffer) <= window
        assert len(proc._csi_buffer) <= window

    def test_signal_processor_reset_releases_buffer(self):
        """Após reset, buffers estão vazios."""
        proc = SignalProcessor(window_size=50)
        for _ in range(50):
            proc.process(_make_signal())
        proc.reset()

        assert len(proc._rssi_buffer) == 0
        assert len(proc._energy_buffer) == 0
        assert len(proc._csi_buffer) == 0
        assert proc._last_rssi is None

    def test_heuristic_detector_no_memory_growth(self):
        """HeuristicDetector não acumula estado indefinidamente."""
        detector = HeuristicDetector()
        for i in range(1000):
            detector.detect(_make_features())
        # Detector apenas mantém _still_since e _last_event — sem listas
        assert not hasattr(detector, "_history") or len(getattr(detector, "_history", [])) == 0


class TestThroughput:
    """Testa taxa de processamento do pipeline."""

    def test_processor_throughput_1000_samples(self):
        """Deve processar 1000 amostras em < 5 segundos."""
        proc = SignalProcessor()
        signal = _make_signal()

        start = time.perf_counter()
        for _ in range(1000):
            proc.process(signal)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"1000 amostras levaram {elapsed:.2f}s (limite: 5s)"

    def test_detector_throughput_1000_detections(self):
        """Deve classificar 1000 detecções em < 1 segundo."""
        detector = HeuristicDetector()
        features = _make_features()

        start = time.perf_counter()
        for _ in range(1000):
            detector.detect(features)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"1000 detecções levaram {elapsed:.2f}s (limite: 1s)"

    def test_combined_throughput_per_second(self):
        """Pipeline combinado deve superar 200 ciclos/segundo."""
        proc = SignalProcessor()
        detector = HeuristicDetector()
        signal = _make_signal()

        n = 500
        start = time.perf_counter()
        for _ in range(n):
            features = proc.process(signal)
            detector.detect(features)
        elapsed = time.perf_counter() - start

        throughput = n / elapsed
        assert throughput >= 200, f"Throughput: {throughput:.0f} ciclos/s (mínimo: 200)"
