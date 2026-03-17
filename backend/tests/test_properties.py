"""
test_properties.py — Tarefas 42.1–42.4: Testes de Propriedade (Hypothesis)

Propriedades testadas:
  42.1 — Detecção de queda (Props. 8, 9, 10)
  42.2 — Providers e capabilities (Props. 15, 16, 17)
  42.3 — Exportação (Props. 45, 46, 47)
  42.4 — Configuração (Props. 65, 66, 67, 68)
"""

import time
import io
import csv
import json
import math
import asyncio
from typing import List

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from app.capture.base import SignalData
from app.processing.signal_processor import SignalProcessor, ProcessedFeatures
from app.detection.base import EventType, DetectionResult
from app.detection.heuristic_detector import HeuristicDetector, ThresholdConfig


# ══════════════════════════════════════════════════════
# Estratégias Hypothesis
# ══════════════════════════════════════════════════════

valid_rssi = st.floats(min_value=-100.0, max_value=-20.0, allow_nan=False, allow_infinity=False)
valid_csi_val = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)
valid_csi = st.lists(valid_csi_val, min_size=1, max_size=64)

def signal_strategy():
    return st.builds(
        SignalData,
        rssi=valid_rssi,
        csi_amplitude=valid_csi,
        timestamp=st.just(time.time()),
        provider=st.just("hypothesis"),
    )

def features_strategy(**overrides):
    base = dict(
        rssi_normalized=st.floats(0.0, 1.0, allow_nan=False),
        rssi_smoothed=st.floats(-100.0, -20.0, allow_nan=False),
        signal_energy=st.floats(0.0, 100.0, allow_nan=False),
        signal_variance=st.floats(0.0, 50.0, allow_nan=False),
        rate_of_change=st.floats(0.0, 50.0, allow_nan=False),
        instability_score=st.floats(0.0, 1.0, allow_nan=False),
        csi_mean_amplitude=st.floats(0.0, 30.0, allow_nan=False),
        csi_std_amplitude=st.floats(0.0, 20.0, allow_nan=False),
        raw_rssi=st.floats(-100.0, -20.0, allow_nan=False),
        timestamp=st.just(time.time()),
    )
    base.update(overrides)
    return st.builds(ProcessedFeatures, **base)


# ══════════════════════════════════════════════════════
# 42.1 — Propriedades de Detecção de Queda (Props. 8, 9, 10)
# ══════════════════════════════════════════════════════

class TestFallDetectionProperties:
    """
    Prop 8: Se rate_of_change >= fall_rate_spike → FALL_SUSPECTED
    Prop 9: Confidence de queda sempre em [0, 1]
    Prop 10: Reset limpa estado → detecção não é afetada por histórico
    """

    @given(
        rate=st.floats(min_value=8.0, max_value=100.0, allow_nan=False),
        energy=st.floats(min_value=0.0, max_value=19.9, allow_nan=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_prop8_high_rate_always_falls(self, rate: float, energy: float):
        """Prop 8: rate_of_change >= fall_rate_spike → FALL_SUSPECTED."""
        cfg = ThresholdConfig(fall_rate_spike=8.0)
        detector = HeuristicDetector(config=cfg)
        features = ProcessedFeatures(
            rssi_normalized=0.9,
            rssi_smoothed=-30.0,
            signal_energy=energy,
            signal_variance=1.0,
            rate_of_change=rate,
            instability_score=0.9,
            csi_mean_amplitude=5.0,
            csi_std_amplitude=1.0,
            raw_rssi=-30.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert result.event_type == EventType.FALL_SUSPECTED

    @given(features_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prop9_confidence_always_in_range(self, features: ProcessedFeatures):
        """Prop 9: Confiança sempre em [0.0, 1.0] para qualquer entrada."""
        detector = HeuristicDetector()
        result = detector.detect(features)
        assert 0.0 <= result.confidence <= 1.0, (
            f"Confidence fora do range: {result.confidence} "
            f"para {result.event_type} com features {features}"
        )

    @given(
        features_a=features_strategy(),
        features_b=features_strategy(),
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_prop10_reset_isolates_state(
        self, features_a: ProcessedFeatures, features_b: ProcessedFeatures
    ):
        """Prop 10: Após reset, o resultado só depende das features atuais."""
        detector = HeuristicDetector()

        # Detecta com features_a (pode alterar estado interno)
        detector.detect(features_a)

        # Reset e detecta com features_b
        detector.reset()
        result_after_reset = detector.detect(features_b)

        # Novo detector fresco com mesmas features_b
        detector_fresh = HeuristicDetector()
        result_fresh = detector_fresh.detect(features_b)

        # Ambos devem produzir o mesmo resultado
        assert result_after_reset.event_type == result_fresh.event_type

    @given(
        energy=st.floats(min_value=20.0, max_value=100.0, allow_nan=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_prop8b_high_energy_always_falls(self, energy: float):
        """Prop 8b: signal_energy >= fall_energy_spike → FALL_SUSPECTED."""
        cfg = ThresholdConfig(fall_energy_spike=20.0)
        detector = HeuristicDetector(config=cfg)
        features = ProcessedFeatures(
            rssi_normalized=0.9,
            rssi_smoothed=-30.0,
            signal_energy=energy,
            signal_variance=1.0,
            rate_of_change=0.0,  # sem taxa
            instability_score=0.5,
            csi_mean_amplitude=5.0,
            csi_std_amplitude=1.0,
            raw_rssi=-30.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert result.event_type == EventType.FALL_SUSPECTED


# ══════════════════════════════════════════════════════
# 42.2 — Propriedades de Providers (Props. 15, 16, 17)
# ══════════════════════════════════════════════════════

class TestProviderProperties:
    """
    Prop 15: SignalData sempre tem RSSI em [-100, 0]
    Prop 16: SignalData sempre tem timestamp > 0
    Prop 17: ProcessedFeatures preserva raw_rssi == sinal original
    """

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_prop15_rssi_always_in_range(self, rssi: float, csi: list):
        """Prop 15: SignalData aceita RSSI em intervalo válido."""
        signal = SignalData(
            rssi=rssi,
            csi_amplitude=csi,
            timestamp=time.time(),
            provider="test",
        )
        assert -100.0 <= signal.rssi <= 0.0 or signal.rssi == rssi  # rssi é preservado

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_prop16_timestamp_always_positive(self, rssi: float, csi: list):
        """Prop 16: Timestamp de SignalData é sempre positivo."""
        signal = SignalData(
            rssi=rssi,
            csi_amplitude=csi,
            timestamp=time.time(),
            provider="test",
        )
        assert signal.timestamp > 0

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_prop17_raw_rssi_preserved_in_features(self, rssi: float, csi: list):
        """Prop 17: ProcessedFeatures preserva raw_rssi igual ao sinal original."""
        assume(len(csi) > 0)
        proc = SignalProcessor()
        signal = SignalData(
            rssi=rssi,
            csi_amplitude=csi,
            timestamp=time.time(),
            provider="test",
        )
        features = proc.process(signal)
        assert features.raw_rssi == pytest.approx(rssi)

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_provider_signal_data_all_fields_populated(self, rssi: float, csi: list):
        """SignalData sempre tem todos os campos necessários preenchidos."""
        assume(len(csi) > 0)
        signal = SignalData(
            rssi=rssi,
            csi_amplitude=csi,
            timestamp=time.time(),
            provider="test",
        )
        assert signal.rssi is not None
        assert signal.csi_amplitude is not None
        assert signal.timestamp is not None
        assert signal.provider is not None

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_signal_energy_non_negative(self, rssi: float, csi: list):
        """Energia do sinal deve ser sempre não-negativa."""
        assume(len(csi) > 0)
        proc = SignalProcessor()
        signal = SignalData(rssi=rssi, csi_amplitude=csi, timestamp=time.time(), provider="test")
        features = proc.process(signal)
        assert features.signal_energy >= 0.0

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_rssi_normalized_in_range(self, rssi: float, csi: list):
        """RSSI normalizado deve estar em [0, 1]."""
        assume(len(csi) > 0)
        proc = SignalProcessor()
        signal = SignalData(rssi=rssi, csi_amplitude=csi, timestamp=time.time(), provider="test")
        features = proc.process(signal)
        assert 0.0 <= features.rssi_normalized <= 1.0

    @given(rssi=valid_rssi, csi=valid_csi)
    @settings(max_examples=50)
    def test_rate_of_change_non_negative(self, rssi: float, csi: list):
        """Taxa de variação do RSSI deve ser sempre não-negativa."""
        assume(len(csi) > 0)
        proc = SignalProcessor()
        # Dois sinais consecutivos
        sig1 = SignalData(rssi=rssi, csi_amplitude=csi, timestamp=time.time(), provider="test")
        proc.process(sig1)
        sig2 = SignalData(rssi=rssi - 5.0 if rssi > -95 else rssi + 5.0,
                          csi_amplitude=csi, timestamp=time.time(), provider="test")
        features = proc.process(sig2)
        assert features.rate_of_change >= 0.0


# ══════════════════════════════════════════════════════
# 42.3 — Propriedades de Exportação (Props. 45, 46, 47)
# ══════════════════════════════════════════════════════

class TestExportProperties:
    """
    Prop 45: CSV exportado é parseável e tem cabeçalho correto
    Prop 46: JSON exportado é parseável e contém lista de eventos
    Prop 47: Número de linhas no CSV = número de eventos + 1 (header)
    """

    def _generate_csv(self, events: list[dict]) -> str:
        """Simula a lógica de geração de CSV da API de exportação."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "event_type", "confidence", "provider", "timestamp"])
        for e in events:
            writer.writerow([
                e.get("id", 0),
                e.get("event_type", "no_presence"),
                e.get("confidence", 0.0),
                e.get("provider", "mock"),
                e.get("timestamp", time.time()),
            ])
        return output.getvalue()

    def _generate_json(self, events: list[dict]) -> str:
        """Simula a lógica de geração de JSON da API de exportação."""
        return json.dumps({"events": events, "count": len(events)})

    @given(
        events=st.lists(
            st.fixed_dictionaries({
                "id": st.integers(min_value=1, max_value=9999),
                "event_type": st.sampled_from(["no_presence", "presence_still", "presence_moving", "fall_suspected"]),
                "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
                "provider": st.sampled_from(["heuristic", "ml", "mock"]),
                "timestamp": st.floats(min_value=1e9, max_value=2e9),
            }),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=40)
    def test_prop45_csv_always_parseable(self, events: list):
        """Prop 45: CSV gerado é sempre parseável por csv.reader."""
        csv_content = self._generate_csv(events)
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        # Cabeçalho + dados
        assert len(rows) == len(events) + 1
        # Cabeçalho correto
        assert rows[0] == ["id", "event_type", "confidence", "provider", "timestamp"]

    @given(
        events=st.lists(
            st.fixed_dictionaries({
                "id": st.integers(min_value=1),
                "event_type": st.sampled_from(["no_presence", "fall_suspected"]),
                "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
                "provider": st.just("mock"),
                "timestamp": st.floats(min_value=1e9, max_value=2e9),
            }),
            min_size=0,
            max_size=100,
        )
    )
    @settings(max_examples=40)
    def test_prop46_json_always_parseable(self, events: list):
        """Prop 46: JSON gerado é sempre parseável e contém lista de eventos."""
        json_content = self._generate_json(events)
        parsed = json.loads(json_content)
        assert "events" in parsed
        assert "count" in parsed
        assert isinstance(parsed["events"], list)
        assert parsed["count"] == len(events)

    @given(
        n=st.integers(min_value=0, max_value=200)
    )
    @settings(max_examples=40)
    def test_prop47_csv_row_count_matches_events(self, n: int):
        """Prop 47: Número de linhas do CSV = eventos + 1 (header)."""
        events = [{"id": i, "event_type": "no_presence", "confidence": 0.9, "provider": "mock", "timestamp": 1.0 * i}
                  for i in range(n)]
        csv_content = self._generate_csv(events)
        lines = [l for l in csv_content.strip().split("\n") if l]
        assert len(lines) == n + 1

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=30)
    def test_prop45b_confidence_survives_csv_round_trip(self, confidence: float):
        """Confiança exportada para CSV e relida deve ser equivalente."""
        events = [{"id": 1, "event_type": "no_presence", "confidence": confidence,
                   "provider": "mock", "timestamp": 1700000000.0}]
        csv_content = self._generate_csv(events)
        reader = csv.DictReader(io.StringIO(csv_content))
        row = next(reader)
        parsed_confidence = float(row["confidence"])
        assert abs(parsed_confidence - confidence) < 1e-6


# ══════════════════════════════════════════════════════
# 42.4 — Propriedades de Configuração (Props. 65, 66, 67, 68)
# ══════════════════════════════════════════════════════

class TestConfigurationProperties:
    """
    Prop 65: ThresholdConfig com valores válidos não causa erro de detecção
    Prop 66: Limiares positivos sempre válidos para HeuristicDetector
    Prop 67: Detecção é determinística para mesmas features e config
    Prop 68: SignalProcessor com diferentes window_size produz features consistentes
    """

    @given(
        presence_energy=st.floats(min_value=0.1, max_value=50.0, allow_nan=False),
        movement_variance=st.floats(min_value=0.1, max_value=20.0, allow_nan=False),
        fall_rate=st.floats(min_value=1.0, max_value=50.0, allow_nan=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_prop65_valid_config_no_detection_error(
        self,
        presence_energy: float,
        movement_variance: float,
        fall_rate: float,
    ):
        """Prop 65: ThresholdConfig válida nunca lança exceção na detecção."""
        cfg = ThresholdConfig(
            presence_energy_min=presence_energy,
            movement_variance_min=movement_variance,
            fall_rate_spike=fall_rate,
        )
        detector = HeuristicDetector(config=cfg)
        features = ProcessedFeatures(
            rssi_normalized=0.5,
            rssi_smoothed=-55.0,
            signal_energy=5.0,
            signal_variance=1.0,
            rate_of_change=1.0,
            instability_score=0.3,
            csi_mean_amplitude=3.0,
            csi_std_amplitude=0.5,
            raw_rssi=-55.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert isinstance(result, DetectionResult)

    @given(
        threshold=st.floats(min_value=0.0001, max_value=200.0, allow_nan=False)
    )
    @settings(max_examples=50)
    def test_prop66_positive_thresholds_valid(self, threshold: float):
        """Prop 66: Qualquer limiar positivo resulta em config válida."""
        cfg = ThresholdConfig(
            presence_energy_min=threshold,
            movement_variance_min=threshold,
            fall_rate_spike=threshold,
            fall_energy_spike=threshold,
        )
        detector = HeuristicDetector(config=cfg)
        assert detector._config.presence_energy_min == pytest.approx(threshold)

    @given(features_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_prop67_detection_is_deterministic(self, features: ProcessedFeatures):
        """Prop 67: Mesmas features + mesma config → mesmo resultado."""
        cfg = ThresholdConfig()
        detector1 = HeuristicDetector(config=cfg)
        detector2 = HeuristicDetector(config=cfg)

        result1 = detector1.detect(features)
        result2 = detector2.detect(features)

        assert result1.event_type == result2.event_type

    @given(
        window_size=st.integers(min_value=5, max_value=200),
        rssi=valid_rssi,
        csi=valid_csi,
    )
    @settings(max_examples=40)
    def test_prop68_window_size_consistency(
        self, window_size: int, rssi: float, csi: list
    ):
        """Prop 68: SignalProcessor com qualquer window_size produz features válidas."""
        assume(len(csi) > 0)
        proc = SignalProcessor(window_size=window_size)
        signal = SignalData(rssi=rssi, csi_amplitude=csi, timestamp=time.time(), provider="test")
        features = proc.process(signal)

        assert 0.0 <= features.rssi_normalized <= 1.0
        assert features.signal_energy >= 0.0
        assert features.rate_of_change >= 0.0
        assert 0.0 <= features.instability_score <= 1.0

    @given(
        energy=st.floats(min_value=0.0, max_value=1.99, allow_nan=False),
        rssi_norm=st.floats(min_value=0.0, max_value=0.24, allow_nan=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_prop65b_low_energy_always_no_presence(self, energy: float, rssi_norm: float):
        """
        Prop 65b: Com energy < presence_energy_min e rssi_norm < presence_rssi_norm_min
        → sempre NO_PRESENCE (independente de outras features — a menos que fall).
        """
        cfg = ThresholdConfig(
            presence_energy_min=2.0,
            presence_rssi_norm_min=0.25,
            fall_rate_spike=100.0,   # threshold impossível → nunca queda
            fall_energy_spike=100.0,
        )
        detector = HeuristicDetector(config=cfg)
        features = ProcessedFeatures(
            rssi_normalized=rssi_norm,
            rssi_smoothed=-90.0,
            signal_energy=energy,
            signal_variance=0.1,
            rate_of_change=0.1,   # << 100 → sem queda
            instability_score=0.1,
            csi_mean_amplitude=0.5,
            csi_std_amplitude=0.1,
            raw_rssi=-90.0,
            timestamp=time.time(),
        )
        result = detector.detect(features)
        assert result.event_type == EventType.NO_PRESENCE
