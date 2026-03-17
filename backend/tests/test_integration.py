"""
test_integration.py — Tarefa 40: Testes de Integração

Cobre:
- Pipeline completo: MockProvider → SignalProcessor → HeuristicDetector
- Pipeline com MLDetector (fallback automático)
- Ciclo de calibração + detecção
- Múltiplos sinais em sequência (série temporal)
"""

import time
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.capture.base import SignalData
from app.capture.mock_provider import MockSignalProvider, SimulationMode
from app.processing.signal_processor import SignalProcessor
from app.detection.base import EventType, DetectionResult
from app.detection.heuristic_detector import HeuristicDetector, ThresholdConfig
from app.detection.ml_detector import MLDetector
from app.services.calibration_service import CalibrationService, BaselineData


# ══════════════════════════════════════════════════════
# Pipeline: MockProvider → Processor → HeuristicDetector
# ══════════════════════════════════════════════════════

class TestFullPipelineHeuristic:
    """Testa pipeline completo com detector heurístico."""

    def _run_pipeline(self, mode: SimulationMode, n_samples: int = 20):
        """Executa n_samples amostras do MockProvider pelo pipeline."""
        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(mode)

            processor = SignalProcessor()
            detector = HeuristicDetector()
            results = []

            for _ in range(n_samples):
                signal = await provider.get_signal()
                features = processor.process(signal)
                result = detector.detect(features)
                results.append(result)

            await provider.stop()
            return results

        return asyncio.run(_inner())

    def test_empty_mode_produces_stable_low_energy_signal(self):
        """Modo EMPTY gera sinal de baixa energia e baixa variância."""
        async def _inner():
            from app.capture.mock_provider import MockSignalProvider, SimulationMode
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.EMPTY)

            processor = SignalProcessor()
            energies = []
            variances = []
            for _ in range(15):
                signal = await provider.get_signal()
                features = processor.process(signal)
                energies.append(features.signal_energy)
                variances.append(features.signal_variance)

            await provider.stop()
            return energies, variances

        energies, variances = asyncio.run(_inner())
        avg_energy = sum(energies) / len(energies)
        avg_variance = sum(variances) / len(variances)
        # Modo EMPTY: energia < 10 e variância < 2
        assert avg_energy < 10.0, f"Energia média no modo EMPTY: {avg_energy:.2f}"
        assert avg_variance < 2.0, f"Variância média no modo EMPTY: {avg_variance:.2f}"

    def test_moving_mode_produces_presence_or_moving(self):
        results = self._run_pipeline(SimulationMode.MOVING, n_samples=20)
        # Pelo menos uma detecção de presença (moving ou still)
        presence_types = {EventType.PRESENCE_MOVING, EventType.PRESENCE_STILL, EventType.FALL_SUSPECTED}
        has_presence = any(r.event_type in presence_types for r in results)
        assert has_presence

    def test_all_results_are_valid_detection_results(self):
        results = self._run_pipeline(SimulationMode.STILL, n_samples=10)
        for r in results:
            assert isinstance(r, DetectionResult)
            assert isinstance(r.event_type, EventType)
            assert 0.0 <= r.confidence <= 1.0

    def test_fall_mode_eventually_detects_fall(self):
        results = self._run_pipeline(SimulationMode.FALL, n_samples=30)
        has_fall = any(r.event_type == EventType.FALL_SUSPECTED for r in results)
        assert has_fall, "Modo FALL deve detectar queda em algum momento"

    def test_processor_features_feed_into_detector(self):
        """Garante que features processadas têm os campos esperados pelo detector."""
        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.STILL)

            processor = SignalProcessor()
            signal = await provider.get_signal()
            features = processor.process(signal)

            # Verifica que todos os campos necessários estão presentes
            assert hasattr(features, "signal_energy")
            assert hasattr(features, "signal_variance")
            assert hasattr(features, "rate_of_change")
            assert hasattr(features, "rssi_normalized")
            assert hasattr(features, "instability_score")

            await provider.stop()

        asyncio.run(_inner())

    def test_pipeline_processes_50_samples_without_error(self):
        """Pipeline deve processar 50 amostras sem levantar exceção."""
        results = self._run_pipeline(SimulationMode.RANDOM, n_samples=50)
        assert len(results) == 50


class TestFullPipelineML:
    """Testa pipeline com MLDetector (usa fallback quando modelo não existe)."""

    def test_ml_detector_fallback_pipeline(self):
        """MLDetector sem modelo usa fallback e produz resultados válidos."""
        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.STILL)

            processor = SignalProcessor()
            detector = MLDetector(model_path="models/nonexistent_model.pkl")

            results = []
            for _ in range(15):
                signal = await provider.get_signal()
                features = processor.process(signal)
                result = detector.detect(features)
                results.append(result)

            await provider.stop()
            return results

        results = asyncio.run(_inner())
        assert len(results) == 15
        for r in results:
            assert isinstance(r, DetectionResult)
            assert 0.0 <= r.confidence <= 1.0

    def test_ml_detector_with_real_model(self, tmp_path):
        """MLDetector com modelo real produz resultados ML após 10 amostras."""
        import numpy as np
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        # Cria e salva modelo real mínimo
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.rand(50, 18)
        y = ["no_presence", "presence_still", "presence_moving", "fall_suspected", "prolonged_inactivity"] * 10
        model.fit(X, y)
        scaler = StandardScaler().fit(X)

        model_path = tmp_path / "classifier.pkl"
        scaler_path = tmp_path / "classifier_scaler.pkl"
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.MOVING)

            processor = SignalProcessor()
            detector = MLDetector(model_path=str(model_path))

            results = []
            for _ in range(15):
                signal = await provider.get_signal()
                features = processor.process(signal)
                result = detector.detect(features)
                results.append(result)

            await provider.stop()
            return results

        results = asyncio.run(_inner())
        # Últimas 6 detecções devem ter usado ML
        ml_results = [r for r in results[9:] if r.details.get("model") == "ml"]
        assert len(ml_results) > 0


class TestCalibrationPlusDetectionIntegration:
    """Testa integração entre calibração e detecção."""

    def test_calibration_baseline_reflects_empty_environment(self):
        """Baseline de calibração deve refletir ambiente vazio."""
        async def _inner():
            provider = MockSignalProvider()
            await provider.start()
            provider.set_mode(SimulationMode.EMPTY)

            svc = CalibrationService(provider)

            # Injeta amostras manualmente (evita sleep real)
            signals = []
            for _ in range(20):
                s = await provider.get_signal()
                signals.append(s)
            svc._calibration_samples = signals

            baseline = svc._calculate_baseline("integration_test")
            await provider.stop()
            return baseline

        baseline = asyncio.run(_inner())
        # Ambiente vazio: RSSI ~-75 dBm
        assert -85.0 <= baseline.mean_rssi <= -65.0
        assert baseline.samples_count == 20
        assert baseline.noise_floor <= baseline.mean_rssi

    def test_calibration_then_detect_still(self):
        """Após calibrar com ambiente vazio, detecta presença parada corretamente."""
        async def _inner():
            empty_provider = MockSignalProvider()
            await empty_provider.start()
            empty_provider.set_mode(SimulationMode.EMPTY)

            svc = CalibrationService(empty_provider)
            signals = [await empty_provider.get_signal() for _ in range(20)]
            svc._calibration_samples = signals
            baseline = svc._calculate_baseline("integration")

            # Agora detecta com pessoa parada
            still_provider = MockSignalProvider()
            await still_provider.start()
            still_provider.set_mode(SimulationMode.STILL)

            processor = SignalProcessor()
            detector = HeuristicDetector()

            results = []
            for _ in range(15):
                signal = await still_provider.get_signal()
                features = processor.process(signal)
                result = detector.detect(features)
                results.append(result)

            await empty_provider.stop()
            await still_provider.stop()
            return baseline, results

        baseline, results = asyncio.run(_inner())
        # Deve detectar alguma presença (still ou moving)
        presence_detected = any(
            r.event_type in {EventType.PRESENCE_STILL, EventType.PRESENCE_MOVING}
            for r in results
        )
        assert presence_detected


class TestSignalProcessorPipelineStateful:
    """Testa o comportamento stateful do SignalProcessor no pipeline."""

    def test_rate_of_change_increases_on_step_change(self):
        proc = SignalProcessor()
        # 5 amostras estáveis
        for _ in range(5):
            f = proc.process(SignalData(rssi=-60.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="t"))
        # Pico brusco
        f_spike = proc.process(SignalData(rssi=-30.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="t"))
        assert f_spike.rate_of_change > 20.0

    def test_window_buffer_bounded(self):
        """Buffer nunca excede window_size."""
        proc = SignalProcessor(window_size=10)
        for i in range(25):
            proc.process(SignalData(rssi=-60.0, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="t"))
        assert len(proc._rssi_buffer) <= 10

    def test_instability_increases_with_variable_csi(self):
        stable = SignalProcessor()
        for _ in range(10):
            stable.process(SignalData(rssi=-60.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="t"))
        stable_result = stable.process(SignalData(rssi=-60.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="t"))

        variable = SignalProcessor()
        for i in range(10):
            csi = [0.1 if i % 2 == 0 else 10.0] * 10
            variable.process(SignalData(rssi=-60.0, csi_amplitude=csi, timestamp=time.time(), provider="t"))
        variable_result = variable.process(SignalData(rssi=-60.0, csi_amplitude=[5.0] * 10, timestamp=time.time(), provider="t"))

        assert variable_result.instability_score > stable_result.instability_score
