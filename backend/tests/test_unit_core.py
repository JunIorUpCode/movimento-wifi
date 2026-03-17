"""
test_unit_core.py — Tarefa 39: Testes Unitários Core

Cobre:
- SignalProcessor: normalização, suavização, energia, variância, taxa de variação, instabilidade
- HeuristicDetector: presença, movimento, queda, inatividade, confiança
- CalibrationService: baseline, detecção de movimento, reset, baseline adaptativo
"""

import time
import math
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.capture.base import SignalData
from app.processing.signal_processor import SignalProcessor, ProcessedFeatures
from app.detection.base import EventType, DetectionResult
from app.detection.heuristic_detector import HeuristicDetector, ThresholdConfig
from app.services.calibration_service import CalibrationService, BaselineData, CalibrationError


# ══════════════════════════════════════════════════════
# SignalProcessor
# ══════════════════════════════════════════════════════

class TestSignalProcessorNormalization:
    """Testa normalização RSSI para [0, 1]."""

    def _make_signal(self, rssi: float, csi=None) -> SignalData:
        return SignalData(
            rssi=rssi,
            csi_amplitude=csi or [1.0] * 10,
            timestamp=time.time(),
            provider="test",
        )

    def test_rssi_min_normalizes_to_zero(self):
        proc = SignalProcessor(rssi_min=-100.0, rssi_max=-20.0)
        result = proc.process(self._make_signal(-100.0))
        assert result.rssi_normalized == pytest.approx(0.0)

    def test_rssi_max_normalizes_to_one(self):
        proc = SignalProcessor(rssi_min=-100.0, rssi_max=-20.0)
        result = proc.process(self._make_signal(-20.0))
        assert result.rssi_normalized == pytest.approx(1.0)

    def test_rssi_mid_normalizes_to_half(self):
        proc = SignalProcessor(rssi_min=-100.0, rssi_max=-20.0)
        result = proc.process(self._make_signal(-60.0))
        assert result.rssi_normalized == pytest.approx(0.5)

    def test_rssi_below_min_clamps_to_zero(self):
        proc = SignalProcessor(rssi_min=-100.0, rssi_max=-20.0)
        result = proc.process(self._make_signal(-120.0))
        assert result.rssi_normalized == 0.0

    def test_rssi_above_max_clamps_to_one(self):
        proc = SignalProcessor(rssi_min=-100.0, rssi_max=-20.0)
        result = proc.process(self._make_signal(0.0))
        assert result.rssi_normalized == 1.0

    def test_equal_min_max_returns_half(self):
        proc = SignalProcessor(rssi_min=-50.0, rssi_max=-50.0)
        result = proc.process(self._make_signal(-50.0))
        assert result.rssi_normalized == 0.5

    def test_raw_rssi_preserved(self):
        proc = SignalProcessor()
        sig = self._make_signal(-65.3)
        result = proc.process(sig)
        assert result.raw_rssi == pytest.approx(-65.3)


class TestSignalProcessorSmoothing:
    """Testa suavização por média móvel."""

    def _make_signal(self, rssi: float) -> SignalData:
        return SignalData(rssi=rssi, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="test")

    def test_single_sample_smoothed_equals_raw(self):
        proc = SignalProcessor(smoothing_window=5)
        result = proc.process(self._make_signal(-60.0))
        assert result.rssi_smoothed == pytest.approx(-60.0)

    def test_smoothed_is_average_of_window(self):
        proc = SignalProcessor(smoothing_window=3)
        values = [-60.0, -62.0, -64.0]
        for v in values:
            result = proc.process(self._make_signal(v))
        # Média dos últimos 3: (-60 + -62 + -64) / 3 = -62
        assert result.rssi_smoothed == pytest.approx(-62.0, abs=0.01)

    def test_smoothed_ignores_older_values_beyond_window(self):
        proc = SignalProcessor(window_size=20, smoothing_window=3)
        for v in [-80.0, -80.0, -80.0, -80.0, -80.0]:
            proc.process(self._make_signal(v))
        # Adiciona 3 novos valores
        for v in [-50.0, -50.0, -50.0]:
            result = proc.process(self._make_signal(v))
        assert result.rssi_smoothed == pytest.approx(-50.0, abs=0.01)


class TestSignalProcessorEnergy:
    """Testa cálculo de energia do sinal."""

    def _make_signal(self, csi: list[float]) -> SignalData:
        return SignalData(rssi=-60.0, csi_amplitude=csi, timestamp=time.time(), provider="test")

    def test_zero_csi_energy_is_zero(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal([]))
        assert result.signal_energy == 0.0

    def test_uniform_csi_energy(self):
        proc = SignalProcessor()
        # csi = [2.0] * 4 → energy = (4+4+4+4)/4 = 4.0
        result = proc.process(self._make_signal([2.0] * 4))
        assert result.signal_energy == pytest.approx(4.0)

    def test_energy_is_mean_of_squares(self):
        proc = SignalProcessor()
        csi = [1.0, 2.0, 3.0]
        result = proc.process(self._make_signal(csi))
        expected = (1 + 4 + 9) / 3
        assert result.signal_energy == pytest.approx(expected)

    def test_energy_non_negative(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal([0.5, 1.5, 2.5]))
        assert result.signal_energy >= 0.0


class TestSignalProcessorVariance:
    """Testa cálculo de variância CSI."""

    def _make_signal(self, csi: list[float]) -> SignalData:
        return SignalData(rssi=-60.0, csi_amplitude=csi, timestamp=time.time(), provider="test")

    def test_single_csi_variance_zero(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal([5.0]))
        assert result.signal_variance == 0.0

    def test_uniform_csi_variance_zero(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal([3.0, 3.0, 3.0, 3.0]))
        assert result.signal_variance == pytest.approx(0.0)

    def test_variance_increases_with_spread(self):
        proc = SignalProcessor()
        r1 = proc.process(self._make_signal([3.0, 3.0, 3.0]))
        proc.reset()
        proc2 = SignalProcessor()
        r2 = proc2.process(self._make_signal([1.0, 3.0, 5.0]))
        assert r2.signal_variance > r1.signal_variance


class TestSignalProcessorRateOfChange:
    """Testa taxa de variação do RSSI."""

    def _make_signal(self, rssi: float) -> SignalData:
        return SignalData(rssi=rssi, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="test")

    def test_first_sample_rate_is_zero(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal(-60.0))
        assert result.rate_of_change == 0.0

    def test_rate_is_absolute_difference(self):
        proc = SignalProcessor()
        proc.process(self._make_signal(-60.0))
        result = proc.process(self._make_signal(-70.0))
        assert result.rate_of_change == pytest.approx(10.0)

    def test_rate_is_always_non_negative(self):
        proc = SignalProcessor()
        proc.process(self._make_signal(-50.0))
        result = proc.process(self._make_signal(-60.0))  # descida
        assert result.rate_of_change >= 0.0

    def test_rate_zero_for_same_rssi(self):
        proc = SignalProcessor()
        proc.process(self._make_signal(-55.0))
        result = proc.process(self._make_signal(-55.0))
        assert result.rate_of_change == pytest.approx(0.0)


class TestSignalProcessorInstability:
    """Testa score de instabilidade."""

    def _make_signal(self, csi: list[float], rssi=-60.0) -> SignalData:
        return SignalData(rssi=rssi, csi_amplitude=csi, timestamp=time.time(), provider="test")

    def test_instability_zero_with_few_samples(self):
        proc = SignalProcessor()
        result = proc.process(self._make_signal([1.0] * 5))
        # Menos de 3 amostras no buffer de energia → score = 0
        assert result.instability_score == 0.0

    def test_instability_range_zero_to_one(self):
        proc = SignalProcessor()
        for i in range(10):
            result = proc.process(self._make_signal([float(i)] * 5))
        assert 0.0 <= result.instability_score <= 1.0

    def test_instability_higher_for_variable_signal(self):
        import random
        random.seed(42)
        # Sinal estável
        stable = SignalProcessor()
        for _ in range(15):
            stable.process(self._make_signal([1.0] * 5))
        # Sinal variável
        variable = SignalProcessor()
        for i in range(15):
            csi = [float(1 + 10 * (i % 2)) for _ in range(5)]
            variable.process(self._make_signal(csi))
        stable_result = stable.process(self._make_signal([1.0] * 5))
        variable_result = variable.process(self._make_signal([10.0] * 5))
        assert variable_result.instability_score >= stable_result.instability_score


class TestSignalProcessorReset:
    """Testa reset do processador."""

    def _make_signal(self, rssi=-60.0) -> SignalData:
        return SignalData(rssi=rssi, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="test")

    def test_reset_clears_rate_of_change(self):
        proc = SignalProcessor()
        proc.process(self._make_signal(-60.0))
        proc.reset()
        result = proc.process(self._make_signal(-70.0))
        # Após reset, não há _last_rssi → rate_of_change = 0
        assert result.rate_of_change == 0.0

    def test_reset_clears_instability(self):
        proc = SignalProcessor()
        for i in range(10):
            proc.process(self._make_signal(float(-60 + i)))
        proc.reset()
        result = proc.process(self._make_signal(-60.0))
        assert result.instability_score == 0.0


# ══════════════════════════════════════════════════════
# HeuristicDetector
# ══════════════════════════════════════════════════════

class TestHeuristicDetectorNoPresence:
    """Testa detecção de ausência de presença."""

    def test_low_energy_returns_no_presence(self, low_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(low_energy_features)
        assert result.event_type == EventType.NO_PRESENCE

    def test_no_presence_confidence_above_half(self, low_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(low_energy_features)
        assert result.confidence >= 0.5

    def test_no_presence_details_include_energy(self, low_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(low_energy_features)
        assert "energy" in result.details

    def test_result_is_detection_result(self, low_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(low_energy_features)
        assert isinstance(result, DetectionResult)


class TestHeuristicDetectorMoving:
    """Testa detecção de presença em movimento."""

    def test_high_variance_returns_moving(self, high_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(high_energy_features)
        assert result.event_type == EventType.PRESENCE_MOVING

    def test_moving_confidence_range(self, high_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(high_energy_features)
        assert 0.0 <= result.confidence <= 1.0

    def test_moving_details_include_variance_and_rate(self, high_energy_features):
        detector = HeuristicDetector()
        result = detector.detect(high_energy_features)
        assert "variance" in result.details or "rate" in result.details


class TestHeuristicDetectorFall:
    """Testa detecção de queda."""

    def test_high_rate_of_change_returns_fall(self, fall_features):
        detector = HeuristicDetector()
        result = detector.detect(fall_features)
        assert result.event_type == EventType.FALL_SUSPECTED

    def test_fall_confidence_above_half(self, fall_features):
        detector = HeuristicDetector()
        result = detector.detect(fall_features)
        assert result.confidence >= 0.5

    def test_fall_confidence_at_most_one(self, fall_features):
        detector = HeuristicDetector()
        result = detector.detect(fall_features)
        assert result.confidence <= 1.0

    def test_fall_details_include_rate_or_energy(self, fall_features):
        detector = HeuristicDetector()
        result = detector.detect(fall_features)
        assert "rate_of_change" in result.details or "energy" in result.details

    def test_high_energy_alone_triggers_fall(self):
        """Energia muito alta (sem rate) também detecta queda."""
        detector = HeuristicDetector()
        features = ProcessedFeatures(
            rssi_normalized=0.9,
            rssi_smoothed=-30.0,
            signal_energy=30.0,   # >= fall_energy_spike (20.0)
            signal_variance=1.0,
            rate_of_change=0.0,   # sem taxa de variação
            instability_score=0.5,
            csi_mean_amplitude=10.0,
            csi_std_amplitude=2.0,
            raw_rssi=-30.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert result.event_type == EventType.FALL_SUSPECTED


class TestHeuristicDetectorStill:
    """Testa detecção de presença parada."""

    def test_still_presence_detected(self, still_features):
        detector = HeuristicDetector()
        result = detector.detect(still_features)
        assert result.event_type == EventType.PRESENCE_STILL

    def test_still_confidence_at_least_0_5(self, still_features):
        detector = HeuristicDetector()
        result = detector.detect(still_features)
        assert result.confidence >= 0.5


class TestHeuristicDetectorInactivity:
    """Testa detecção de inatividade prolongada."""

    def test_inactivity_after_timeout(self):
        config = ThresholdConfig(inactivity_timeout=0.0)  # Timeout imediato
        detector = HeuristicDetector(config=config)

        features = ProcessedFeatures(
            rssi_normalized=0.5,
            rssi_smoothed=-55.0,
            signal_energy=3.0,
            signal_variance=0.1,  # baixa variância → parado
            rate_of_change=0.2,   # baixa taxa → parado
            instability_score=0.1,
            csi_mean_amplitude=3.0,
            csi_std_amplitude=0.2,
            raw_rssi=-55.0,
            timestamp=time.time(),
        )
        # Primeiro ciclo define _still_since
        detector.detect(features)
        # Segundo ciclo com timeout=0 → inatividade
        result = detector.detect(features)
        assert result.event_type == EventType.PROLONGED_INACTIVITY

    def test_inactivity_confidence_increases_with_time(self):
        """Quanto maior o tempo parado, maior a confiança."""
        detector = HeuristicDetector(config=ThresholdConfig(inactivity_timeout=0.0))
        features = ProcessedFeatures(
            rssi_normalized=0.5,
            rssi_smoothed=-55.0,
            signal_energy=3.0,
            signal_variance=0.1,
            rate_of_change=0.2,
            instability_score=0.1,
            csi_mean_amplitude=3.0,
            csi_std_amplitude=0.2,
            raw_rssi=-55.0,
            timestamp=time.time(),
        )
        detector.detect(features)
        # Simula longa inatividade forçando _still_since no passado
        detector._still_since = time.time() - 200
        result = detector.detect(features)
        assert result.event_type == EventType.PROLONGED_INACTIVITY
        assert result.confidence > 0.5


class TestHeuristicDetectorReset:
    """Testa reset do detector."""

    def test_reset_clears_still_since(self, still_features):
        detector = HeuristicDetector()
        detector.detect(still_features)
        assert detector._still_since is not None
        detector.reset()
        assert detector._still_since is None

    def test_reset_restores_last_event_to_no_presence(self, still_features):
        detector = HeuristicDetector()
        detector.detect(still_features)
        detector.reset()
        assert detector._last_event == EventType.NO_PRESENCE


class TestHeuristicDetectorConfig:
    """Testa configuração personalizada."""

    def test_custom_config_applied(self):
        config = ThresholdConfig(
            presence_energy_min=100.0,      # Limiar impossível de energy
            presence_rssi_norm_min=2.0,     # Limiar impossível de rssi_norm
            fall_rate_spike=200.0,          # Sem queda
            fall_energy_spike=200.0,
        )
        detector = HeuristicDetector(config=config)
        features = ProcessedFeatures(
            rssi_normalized=0.9,
            rssi_smoothed=-30.0,
            signal_energy=5.0,   # << 100 → sem presença
            signal_variance=0.1,
            rate_of_change=0.1,
            instability_score=0.1,
            csi_mean_amplitude=2.0,
            csi_std_amplitude=0.2,
            raw_rssi=-30.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert result.event_type == EventType.NO_PRESENCE

    def test_update_config(self):
        detector = HeuristicDetector()
        new_config = ThresholdConfig(fall_rate_spike=100.0)  # Limiar impossível
        detector.update_config(new_config)
        assert detector._config.fall_rate_spike == 100.0

    def test_confidence_always_between_zero_and_one(
        self, low_energy_features, high_energy_features, fall_features, still_features
    ):
        detector = HeuristicDetector()
        for features in [low_energy_features, high_energy_features, fall_features, still_features]:
            result = detector.detect(features)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Confiança fora do intervalo: {result.confidence} para {result.event_type}"
            )


# ══════════════════════════════════════════════════════
# CalibrationService
# ══════════════════════════════════════════════════════

class TestCalibrationServiceBaseline:
    """Testa cálculo e manipulação de baseline."""

    def _make_provider(self, rssi=-75.0):
        """Cria um provider mock que retorna sinal estável."""
        provider = AsyncMock()
        provider.get_signal = AsyncMock(return_value=SignalData(
            rssi=rssi,
            csi_amplitude=[1.0] * 10,
            timestamp=time.time(),
            provider="mock",
        ))
        return provider

    def _make_baseline(self, mean_rssi=-60.0, profile="test") -> BaselineData:
        return BaselineData(
            mean_rssi=mean_rssi,
            std_rssi=2.0,
            mean_variance=1.0,
            std_variance=0.5,
            noise_floor=mean_rssi - 5.0,
            samples_count=30,
            timestamp=time.time(),
            profile_name=profile,
        )

    def test_initial_state(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        assert svc.baseline is None
        assert not svc.is_calibrating

    def test_set_baseline_stores_value(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        bl = self._make_baseline()
        svc.set_baseline(bl)
        assert svc.baseline is bl

    def test_set_baseline_updates_profile_name(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        svc.set_baseline(self._make_baseline(profile="custom"))
        assert svc.baseline.profile_name == "custom"

    def test_reset_clears_baseline(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        svc.set_baseline(self._make_baseline())
        svc.reset()
        assert svc.baseline is None

    def test_reset_clears_calibrating_flag(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        svc._is_calibrating = True
        svc.reset()
        assert not svc.is_calibrating

    def test_baseline_mean_rssi_within_range(self):
        """Baseline calculado deve ter RSSI médio no intervalo esperado."""
        provider = self._make_provider(rssi=-75.0)
        svc = CalibrationService(provider)

        # Injeta amostras manualmente
        samples = [
            SignalData(rssi=-75.0 + (i * 0.1), csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="mock")
            for i in range(10)
        ]
        svc._calibration_samples = samples
        baseline = svc._calculate_baseline("profile_test")

        assert -80.0 <= baseline.mean_rssi <= -70.0

    def test_baseline_std_rssi_non_negative(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        samples = [
            SignalData(rssi=-75.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="mock")
            for _ in range(10)
        ]
        svc._calibration_samples = samples
        baseline = svc._calculate_baseline("test")
        assert baseline.std_rssi >= 0.0

    def test_baseline_noise_floor_below_mean(self):
        """Noise floor (percentil 5) deve ser <= média do RSSI."""
        provider = self._make_provider()
        svc = CalibrationService(provider)
        samples = [
            SignalData(rssi=-75.0 + i, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="mock")
            for i in range(20)
        ]
        svc._calibration_samples = samples
        baseline = svc._calculate_baseline("test")
        assert baseline.noise_floor <= baseline.mean_rssi

    def test_calculate_baseline_raises_without_samples(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        with pytest.raises(ValueError, match="Nenhuma amostra"):
            svc._calculate_baseline("test")

    def test_baseline_samples_count_matches(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        n = 15
        samples = [
            SignalData(rssi=-75.0, csi_amplitude=[1.0] * 10, timestamp=time.time(), provider="mock")
            for _ in range(n)
        ]
        svc._calibration_samples = samples
        baseline = svc._calculate_baseline("test")
        assert baseline.samples_count == n


class TestCalibrationServiceMovementDetection:
    """Testa detecção de movimento durante calibração."""

    def _make_provider(self):
        provider = AsyncMock()
        return provider

    def test_no_movement_with_less_than_5_samples(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        signal = SignalData(rssi=-80.0, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="mock")
        # Menos de 5 amostras → nunca detecta movimento
        for _ in range(4):
            svc._calibration_samples.append(signal)
        result = svc._detect_movement_during_calibration(signal)
        assert result is False

    def test_stable_signal_no_movement(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        # 5 amostras estáveis
        for _ in range(5):
            svc._calibration_samples.append(
                SignalData(rssi=-75.0, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="mock")
            )
        new_signal = SignalData(rssi=-75.0, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="mock")
        result = svc._detect_movement_during_calibration(new_signal)
        assert not result

    def test_high_variance_triggers_movement(self):
        provider = self._make_provider()
        svc = CalibrationService(provider)
        # 5 amostras com grande variação
        rssi_values = [-75.0, -60.0, -80.0, -50.0, -90.0]
        for rssi in rssi_values:
            svc._calibration_samples.append(
                SignalData(rssi=rssi, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="mock")
            )
        new_signal = SignalData(rssi=-40.0, csi_amplitude=[1.0] * 5, timestamp=time.time(), provider="mock")
        result = svc._detect_movement_during_calibration(new_signal)
        assert result


class TestCalibrationServiceAdaptive:
    """Testa atualização adaptativa do baseline."""

    def _make_provider(self):
        return AsyncMock()

    def _make_baseline(self, mean_rssi=-60.0) -> BaselineData:
        return BaselineData(
            mean_rssi=mean_rssi,
            std_rssi=2.0,
            mean_variance=2.0,
            std_variance=0.5,
            noise_floor=mean_rssi - 5.0,
            samples_count=30,
            timestamp=time.time(),
            profile_name="adaptive_test",
        )

    def _make_features(self, raw_rssi=-61.0, variance=2.05) -> ProcessedFeatures:
        return ProcessedFeatures(
            rssi_normalized=0.5,
            rssi_smoothed=raw_rssi,
            signal_energy=3.0,
            signal_variance=variance,
            rate_of_change=0.1,
            instability_score=0.1,
            csi_mean_amplitude=2.0,
            csi_std_amplitude=0.2,
            raw_rssi=raw_rssi,
            timestamp=time.time(),
        )

    def test_no_update_without_baseline(self):
        svc = CalibrationService(self._make_provider())
        features = self._make_features()
        # Não deve lançar exceção mesmo sem baseline
        svc.update_baseline_adaptive(features, no_presence_duration=600)
        assert svc.baseline is None

    def test_no_update_below_5_min_threshold(self):
        svc = CalibrationService(self._make_provider())
        bl = self._make_baseline()
        svc.set_baseline(bl)
        original_rssi = bl.mean_rssi
        # Menos de 300s → não atualiza
        svc.update_baseline_adaptive(self._make_features(), no_presence_duration=100)
        assert svc.baseline.mean_rssi == original_rssi

    def test_gradual_update_applied(self):
        svc = CalibrationService(self._make_provider())
        bl = self._make_baseline(mean_rssi=-60.0)
        svc.set_baseline(bl)
        # Sinal próximo (-61, variação ~3%) → deve atualizar gradualmente
        features = self._make_features(raw_rssi=-61.0, variance=2.05)
        svc.update_baseline_adaptive(features, no_presence_duration=600)
        # Deve ter mudado levemente
        assert svc.baseline.mean_rssi != -60.0
        # Deve estar em direção a -61 (mudança pequena por EMA com rate=0.01)
        assert svc.baseline.mean_rssi < -60.0

    def test_abrupt_change_not_applied(self):
        svc = CalibrationService(self._make_provider())
        bl = self._make_baseline(mean_rssi=-60.0)
        svc.set_baseline(bl)
        # Variação de >30% no RSSI → não deve atualizar
        features = self._make_features(raw_rssi=-10.0)  # -10 vs -60 = 83% de mudança
        original_rssi = bl.mean_rssi
        svc.update_baseline_adaptive(features, no_presence_duration=600)
        assert svc.baseline.mean_rssi == original_rssi


class TestCalibrationServiceAsync:
    """Testa fluxo assíncrono da calibração."""

    def test_start_calibration_returns_baseline(self):
        """Calibração assíncrona retorna BaselineData válido."""
        async def run():
            call_count = 0

            async def mock_get_signal():
                nonlocal call_count
                call_count += 1
                return SignalData(
                    rssi=-75.0 + (call_count * 0.1 % 1),
                    csi_amplitude=[1.0] * 10,
                    timestamp=time.time(),
                    provider="mock",
                )

            provider = AsyncMock()
            provider.get_signal = mock_get_signal

            svc = CalibrationService(provider)
            # Usa duration=3s com sleep mockado
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # Limita a 5 iterações ajustando o tempo simulado
                call_times = [0, 1, 2, 3, 4, 10]  # Último valor > duration
                elapsed = iter(call_times)

                with patch("time.time", side_effect=lambda: next(elapsed, 10)):
                    baseline = await svc.start_calibration(duration_seconds=5, profile_name="async_test")

            assert baseline is not None
            assert isinstance(baseline, BaselineData)
            assert baseline.profile_name == "async_test"
            assert baseline.samples_count >= 1

        asyncio.run(run())

    def test_calibration_error_on_movement(self):
        """CalibrationError é levantado ao detectar movimento."""
        async def run():
            call_count = 0
            # RSSI com grande variação para disparar detecção de movimento
            rssi_sequence = [-75, -60, -80, -50, -90, -40, -85]

            async def mock_get_signal():
                nonlocal call_count
                rssi = rssi_sequence[call_count % len(rssi_sequence)]
                call_count += 1
                return SignalData(
                    rssi=float(rssi),
                    csi_amplitude=[1.0] * 5,
                    timestamp=time.time(),
                    provider="mock",
                )

            provider = AsyncMock()
            provider.get_signal = mock_get_signal

            svc = CalibrationService(provider)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with patch("time.time", side_effect=[0] + [0.5 * i for i in range(1, 30)]):
                    with pytest.raises(CalibrationError, match="Movimento detectado"):
                        await svc.start_calibration(duration_seconds=20)

        asyncio.run(run())
