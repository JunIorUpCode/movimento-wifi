"""
conftest.py — Fixtures compartilhadas para Fase 5.
"""

import sys
import time
from pathlib import Path

# Garante que o diretório backend está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.capture.base import SignalData
from app.processing.signal_processor import ProcessedFeatures


@pytest.fixture
def stable_signal():
    """Sinal estável sem presença (ambiente vazio)."""
    return SignalData(
        rssi=-75.0,
        csi_amplitude=[1.0] * 30,
        timestamp=time.time(),
        provider="mock",
    )


@pytest.fixture
def moving_signal():
    """Sinal com movimento intenso."""
    return SignalData(
        rssi=-45.0,
        csi_amplitude=[5.0 + i * 0.5 for i in range(30)],
        timestamp=time.time(),
        provider="mock",
    )


@pytest.fixture
def fall_signal():
    """Sinal simulando queda brusca (alta energia + alta variação)."""
    return SignalData(
        rssi=-30.0,
        csi_amplitude=[10.0 + i for i in range(30)],
        timestamp=time.time(),
        provider="mock",
    )


@pytest.fixture
def low_energy_features():
    """Features de baixa energia (sem presença)."""
    return ProcessedFeatures(
        rssi_normalized=0.1,
        rssi_smoothed=-90.0,
        signal_energy=0.5,
        signal_variance=0.1,
        rate_of_change=0.1,
        instability_score=0.05,
        csi_mean_amplitude=0.5,
        csi_std_amplitude=0.1,
        raw_rssi=-90.0,
        timestamp=time.time(),
    )


@pytest.fixture
def high_energy_features():
    """Features de alta energia (presença em movimento)."""
    return ProcessedFeatures(
        rssi_normalized=0.7,
        rssi_smoothed=-45.0,
        signal_energy=15.0,
        signal_variance=5.0,
        rate_of_change=6.0,
        instability_score=0.8,
        csi_mean_amplitude=8.0,
        csi_std_amplitude=2.0,
        raw_rssi=-45.0,
        timestamp=time.time(),
    )


@pytest.fixture
def fall_features():
    """Features com padrão de queda (rate_of_change alto)."""
    return ProcessedFeatures(
        rssi_normalized=0.9,
        rssi_smoothed=-30.0,
        signal_energy=30.0,
        signal_variance=10.0,
        rate_of_change=15.0,
        instability_score=0.95,
        csi_mean_amplitude=12.0,
        csi_std_amplitude=4.0,
        raw_rssi=-30.0,
        timestamp=time.time(),
    )


@pytest.fixture
def still_features():
    """Features de presença parada (energia média, baixa variância)."""
    return ProcessedFeatures(
        rssi_normalized=0.5,
        rssi_smoothed=-55.0,
        signal_energy=3.0,
        signal_variance=0.2,
        rate_of_change=0.3,
        instability_score=0.1,
        csi_mean_amplitude=3.0,
        csi_std_amplitude=0.3,
        raw_rssi=-55.0,
        timestamp=time.time(),
    )
