"""
Testes para Task 2.5: Baseline Adaptativo

Valida:
- Atualização gradual com EMA
- Detecção de mudanças abruptas (>30%)
- Logging de atualizações significativas (>10%)
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.capture.base import SignalData
from app.processing.signal_processor import ProcessedFeatures
from app.services.calibration_service import BaselineData, CalibrationService


@pytest.fixture
def mock_provider():
    """Cria um provider mock."""
    provider = AsyncMock()
    provider.get_signal = AsyncMock()
    return provider


@pytest.fixture
def calibration_service(mock_provider):
    """Cria um CalibrationService com provider mock."""
    return CalibrationService(provider=mock_provider)


@pytest.fixture
def baseline_data():
    """Cria baseline de teste."""
    return BaselineData(
        mean_rssi=-50.0,
        std_rssi=2.0,
        mean_variance=1.0,
        std_variance=0.5,
        noise_floor=-55.0,
        samples_count=100,
        timestamp=1000.0,
        profile_name="test",
    )


@pytest.fixture
def features_normal():
    """Features normais (sem mudança abrupta)."""
    return ProcessedFeatures(
        raw_rssi=-51.0,  # Mudança de 2% em relação ao baseline
        rssi_normalized=0.5,
        rssi_smoothed=-51.0,
        rate_of_change=0.1,
        signal_energy=100.0,
        signal_variance=1.05,  # Mudança de 5% em relação ao baseline
        csi_mean_amplitude=10.0,
        csi_std_amplitude=1.0,
        instability_score=0.2,
        timestamp=2000.0,
    )


@pytest.fixture
def features_abrupt_rssi():
    """Features com mudança abrupta no RSSI (>30%)."""
    return ProcessedFeatures(
        raw_rssi=-70.0,  # Mudança de 40% em relação ao baseline
        rssi_normalized=0.3,
        rssi_smoothed=-70.0,
        rate_of_change=2.0,
        signal_energy=50.0,
        signal_variance=1.0,
        csi_mean_amplitude=5.0,
        csi_std_amplitude=1.0,
        instability_score=0.8,
        timestamp=2000.0,
    )


@pytest.fixture
def features_abrupt_variance():
    """Features com mudança abrupta na variância (>30%)."""
    return ProcessedFeatures(
        raw_rssi=-51.0,
        rssi_normalized=0.5,
        rssi_smoothed=-51.0,
        rate_of_change=0.1,
        signal_energy=100.0,
        signal_variance=1.5,  # Mudança de 50% em relação ao baseline
        csi_mean_amplitude=10.0,
        csi_std_amplitude=1.0,
        instability_score=0.5,
        timestamp=2000.0,
    )


def test_baseline_adaptive_not_updated_before_5_minutes(
    calibration_service, baseline_data, features_normal
):
    """Testa que baseline não é atualizado antes de 5 minutos sem presença."""
    calibration_service.set_baseline(baseline_data)

    # Tenta atualizar com apenas 4 minutos (240 segundos) sem presença
    calibration_service.update_baseline_adaptive(features_normal, no_presence_duration=240)

    # Baseline não deve ter mudado
    assert calibration_service.baseline.mean_rssi == -50.0
    assert calibration_service.baseline.mean_variance == 1.0


def test_baseline_adaptive_updated_after_5_minutes(
    calibration_service, baseline_data, features_normal
):
    """Testa que baseline é atualizado após 5 minutos sem presença."""
    calibration_service.set_baseline(baseline_data)

    # Atualiza com 6 minutos (360 segundos) sem presença
    calibration_service.update_baseline_adaptive(features_normal, no_presence_duration=360)

    # Baseline deve ter mudado (EMA com taxa 0.01)
    # Nova média RSSI = 0.99 * (-50.0) + 0.01 * (-51.0) = -50.01
    assert calibration_service.baseline.mean_rssi == pytest.approx(-50.01, abs=0.001)

    # Nova média variância = 0.99 * 1.0 + 0.01 * 1.05 = 1.0005
    assert calibration_service.baseline.mean_variance == pytest.approx(1.0005, abs=0.0001)


def test_baseline_adaptive_not_updated_on_abrupt_rssi_change(
    calibration_service, baseline_data, features_abrupt_rssi, caplog
):
    """Testa que baseline não é atualizado em mudança abrupta de RSSI (>30%)."""
    calibration_service.set_baseline(baseline_data)

    with caplog.at_level(logging.WARNING):
        calibration_service.update_baseline_adaptive(
            features_abrupt_rssi, no_presence_duration=360
        )

    # Baseline não deve ter mudado
    assert calibration_service.baseline.mean_rssi == -50.0
    assert calibration_service.baseline.mean_variance == 1.0

    # Deve ter logado warning
    assert "Mudança abrupta detectada" in caplog.text
    assert "baseline não atualizado" in caplog.text


def test_baseline_adaptive_not_updated_on_abrupt_variance_change(
    calibration_service, baseline_data, features_abrupt_variance, caplog
):
    """Testa que baseline não é atualizado em mudança abrupta de variância (>30%)."""
    calibration_service.set_baseline(baseline_data)

    with caplog.at_level(logging.WARNING):
        calibration_service.update_baseline_adaptive(
            features_abrupt_variance, no_presence_duration=360
        )

    # Baseline não deve ter mudado
    assert calibration_service.baseline.mean_rssi == -50.0
    assert calibration_service.baseline.mean_variance == 1.0

    # Deve ter logado warning
    assert "Mudança abrupta detectada" in caplog.text


def test_baseline_adaptive_logs_significant_update(
    calibration_service, baseline_data, caplog
):
    """Testa que atualizações significativas (>10%) são logadas."""
    calibration_service.set_baseline(baseline_data)

    # Cria features que causarão mudança significativa após múltiplas atualizações
    # Para causar mudança >10%, precisamos de muitas iterações com taxa 0.01
    # Ou podemos aumentar a taxa temporariamente
    calibration_service._adaptive_rate = 0.50  # Taxa maior para teste (50%)

    features_significant = ProcessedFeatures(
        raw_rssi=-60.0,  # Diferença de 20% do baseline
        rssi_normalized=0.4,
        rssi_smoothed=-60.0,
        rate_of_change=0.1,
        signal_energy=80.0,
        signal_variance=1.25,  # Diferença de 25% do baseline
        csi_mean_amplitude=8.0,
        csi_std_amplitude=1.0,
        instability_score=0.3,
        timestamp=2000.0,
    )

    with caplog.at_level(logging.INFO):
        calibration_service.update_baseline_adaptive(
            features_significant, no_presence_duration=360
        )

    # Deve ter logado atualização significativa
    # Com taxa 0.5: novo RSSI = 0.5 * (-50) + 0.5 * (-60) = -55
    # Mudança = |-55 - (-50)| / |-50| * 100 = 10%
    assert "Baseline atualizado significativamente" in caplog.text
    assert "RSSI:" in caplog.text
    assert "Variância:" in caplog.text


def test_baseline_adaptive_ema_calculation(calibration_service, baseline_data):
    """Testa que o cálculo de EMA está correto."""
    calibration_service.set_baseline(baseline_data)

    features = ProcessedFeatures(
        raw_rssi=-52.0,
        rssi_normalized=0.5,
        rssi_smoothed=-52.0,
        rate_of_change=0.1,
        signal_energy=100.0,
        signal_variance=1.2,
        csi_mean_amplitude=10.0,
        csi_std_amplitude=1.0,
        instability_score=0.2,
        timestamp=2000.0,
    )

    calibration_service.update_baseline_adaptive(features, no_presence_duration=360)

    # Verifica cálculo EMA
    # Nova média RSSI = 0.99 * (-50.0) + 0.01 * (-52.0) = -50.02
    expected_rssi = 0.99 * (-50.0) + 0.01 * (-52.0)
    assert calibration_service.baseline.mean_rssi == pytest.approx(expected_rssi, abs=0.001)

    # Nova média variância = 0.99 * 1.0 + 0.01 * 1.2 = 1.002
    expected_variance = 0.99 * 1.0 + 0.01 * 1.2
    assert calibration_service.baseline.mean_variance == pytest.approx(
        expected_variance, abs=0.0001
    )


def test_baseline_adaptive_no_baseline_set(calibration_service, features_normal):
    """Testa que não há erro quando baseline não está definido."""
    # Não define baseline
    assert calibration_service.baseline is None

    # Não deve lançar exceção
    calibration_service.update_baseline_adaptive(features_normal, no_presence_duration=360)

    # Baseline continua None
    assert calibration_service.baseline is None


def test_baseline_adaptive_zero_division_protection(calibration_service):
    """Testa proteção contra divisão por zero."""
    # Baseline com valores zero
    baseline_zero = BaselineData(
        mean_rssi=0.0,
        std_rssi=0.0,
        mean_variance=0.0,
        std_variance=0.0,
        noise_floor=0.0,
        samples_count=1,
        timestamp=1000.0,
        profile_name="test_zero",
    )
    calibration_service.set_baseline(baseline_zero)

    features = ProcessedFeatures(
        raw_rssi=-50.0,
        rssi_normalized=0.5,
        rssi_smoothed=-50.0,
        rate_of_change=0.1,
        signal_energy=100.0,
        signal_variance=1.0,
        csi_mean_amplitude=10.0,
        csi_std_amplitude=1.0,
        instability_score=0.2,
        timestamp=2000.0,
    )

    # Não deve lançar exceção de divisão por zero
    calibration_service.update_baseline_adaptive(features, no_presence_duration=360)

    # Baseline deve ter sido atualizado
    assert calibration_service.baseline.mean_rssi != 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
