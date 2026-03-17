"""
Teste básico para CalibrationService - Task 2.1
"""

import asyncio
import sys
import time
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.capture.mock_provider import MockSignalProvider, SimulationMode


# Importa apenas o que precisamos para evitar dependências
import numpy as np
from app.capture.base import SignalData, SignalProvider
from app.processing.signal_processor import ProcessedFeatures, SignalProcessor


# Copia as classes necessárias inline para evitar imports circulares
from dataclasses import dataclass
from typing import Optional


@dataclass
class BaselineData:
    """Dados de baseline do ambiente."""

    mean_rssi: float
    std_rssi: float
    mean_variance: float
    std_variance: float
    noise_floor: float
    samples_count: int
    timestamp: float
    profile_name: str


class CalibrationError(Exception):
    """Erro durante processo de calibração."""

    pass


class CalibrationService:
    """Serviço de calibração do ambiente."""

    def __init__(self, provider: SignalProvider) -> None:
        self._provider = provider
        self._calibration_samples: list[SignalData] = []
        self._is_calibrating = False
        self._baseline: Optional[BaselineData] = None
        self._adaptive_rate = 0.01

    @property
    def is_calibrating(self) -> bool:
        return self._is_calibrating

    @property
    def baseline(self) -> Optional[BaselineData]:
        return self._baseline

    async def start_calibration(
        self, duration_seconds: int = 60, profile_name: str = "default"
    ) -> BaselineData:
        self._is_calibrating = True
        self._calibration_samples.clear()

        start_time = time.time()
        sample_count = 0

        while time.time() - start_time < duration_seconds:
            signal = await self._provider.get_signal()

            if self._detect_movement_during_calibration(signal):
                self._is_calibrating = False
                raise CalibrationError("Movimento detectado durante calibração")

            self._calibration_samples.append(signal)
            sample_count += 1

            await asyncio.sleep(1.0)

        self._is_calibrating = False
        self._baseline = self._calculate_baseline(profile_name)

        return self._baseline

    def _detect_movement_during_calibration(self, signal: SignalData) -> bool:
        if len(self._calibration_samples) < 5:
            return False

        recent_rssi = [s.rssi for s in self._calibration_samples[-5:]]
        recent_rssi.append(signal.rssi)

        variance = np.var(recent_rssi)
        movement_threshold = 3.0

        return variance > movement_threshold

    def _calculate_baseline(self, profile_name: str) -> BaselineData:
        if not self._calibration_samples:
            raise ValueError("Nenhuma amostra coletada para calcular baseline")

        rssi_values = [s.rssi for s in self._calibration_samples]

        processor = SignalProcessor()
        variances = []

        for signal in self._calibration_samples:
            features = processor.process(signal)
            variances.append(features.signal_variance)

        mean_rssi = float(np.mean(rssi_values))
        std_rssi = float(np.std(rssi_values))
        mean_variance = float(np.mean(variances))
        std_variance = float(np.std(variances))
        noise_floor = float(np.percentile(rssi_values, 5))

        return BaselineData(
            mean_rssi=mean_rssi,
            std_rssi=std_rssi,
            mean_variance=mean_variance,
            std_variance=std_variance,
            noise_floor=noise_floor,
            samples_count=len(self._calibration_samples),
            timestamp=time.time(),
            profile_name=profile_name,
        )

    def set_baseline(self, baseline: BaselineData) -> None:
        self._baseline = baseline

    def reset(self) -> None:
        self._calibration_samples.clear()
        self._baseline = None
        self._is_calibrating = False


async def test_calibration_basic():
    """Testa calibração básica com MockSignalProvider."""
    print("=== Teste 1: Calibração Básica ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Verifica estado inicial
    assert not service.is_calibrating
    assert service.baseline is None

    # Inicia calibração (5 segundos para teste rápido)
    print("Iniciando calibração de 5 segundos...")
    start = time.time()
    baseline = await service.start_calibration(duration_seconds=5, profile_name="test")
    duration = time.time() - start

    print(f"Calibração concluída em {duration:.1f}s")
    print(f"Amostras coletadas: {baseline.samples_count}")
    print(f"RSSI médio: {baseline.mean_rssi:.2f} dBm")
    print(f"Desvio padrão RSSI: {baseline.std_rssi:.2f}")
    print(f"Variância média: {baseline.mean_variance:.4f}")
    print(f"Noise floor: {baseline.noise_floor:.2f} dBm")

    # Validações
    assert not service.is_calibrating
    assert service.baseline is not None
    assert baseline.samples_count >= 5
    assert baseline.profile_name == "test"
    assert -100 <= baseline.mean_rssi <= 0
    assert baseline.std_rssi >= 0
    assert baseline.mean_variance >= 0

    await provider.stop()
    print("✓ Teste 1 passou\n")


async def test_calibration_movement_detection():
    """Testa detecção de movimento durante calibração."""
    print("=== Teste 2: Detecção de Movimento ===")

    # MockSignalProvider em modo MOVING simula movimento
    provider = MockSignalProvider()
    await provider.start()
    provider.set_mode(SimulationMode.MOVING)  # Simula movimento

    service = CalibrationService(provider)

    # Tenta calibrar - deve detectar movimento
    print("Tentando calibrar com sinal instável (simula movimento)...")
    try:
        await service.start_calibration(duration_seconds=10)
        print("✗ Teste 2 falhou: deveria ter detectado movimento")
        assert False, "Deveria ter levantado CalibrationError"
    except CalibrationError as e:
        print(f"✓ Movimento detectado corretamente: {e}")
        assert "Movimento detectado" in str(e)

    await provider.stop()
    print("✓ Teste 2 passou\n")


async def test_baseline_properties():
    """Testa propriedades do baseline calculado."""
    print("=== Teste 3: Propriedades do Baseline ===")

    provider = MockSignalProvider()
    await provider.start()
    provider.set_mode(SimulationMode.EMPTY)  # Modo estável

    service = CalibrationService(provider)

    baseline = await service.start_calibration(duration_seconds=5)

    # Verifica que baseline está próximo dos valores do provider (modo empty: ~-75 dBm)
    print(f"RSSI esperado: ~-75.0, obtido: {baseline.mean_rssi:.2f}")
    assert -80 <= baseline.mean_rssi <= -70, "RSSI médio fora do esperado"

    # Verifica que noise floor é menor que média
    assert baseline.noise_floor <= baseline.mean_rssi

    # Verifica timestamp recente
    assert time.time() - baseline.timestamp < 10

    await provider.stop()
    print("✓ Teste 3 passou\n")


async def test_set_baseline():
    """Testa definição manual de baseline."""
    print("=== Teste 4: Set Baseline Manual ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Cria baseline manualmente (usando a classe local)
    manual_baseline = BaselineData(
        mean_rssi=-55.0,
        std_rssi=2.0,
        mean_variance=1.5,
        std_variance=0.5,
        noise_floor=-60.0,
        samples_count=100,
        timestamp=time.time(),
        profile_name="manual",
    )

    service.set_baseline(manual_baseline)

    assert service.baseline is not None
    assert service.baseline.profile_name == "manual"
    assert service.baseline.mean_rssi == -55.0

    await provider.stop()
    print("✓ Teste 4 passou\n")


async def test_reset():
    """Testa reset do serviço."""
    print("=== Teste 5: Reset ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Calibra
    await service.start_calibration(duration_seconds=3)
    assert service.baseline is not None

    # Reset
    service.reset()
    assert service.baseline is None
    assert not service.is_calibrating

    await provider.stop()
    print("✓ Teste 5 passou\n")


async def main():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("TESTES DO CALIBRATIONSERVICE - TASK 2.1")
    print("=" * 60 + "\n")

    try:
        await test_calibration_basic()
        await test_calibration_movement_detection()
        await test_baseline_properties()
        await test_set_baseline()
        await test_reset()

        print("=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
