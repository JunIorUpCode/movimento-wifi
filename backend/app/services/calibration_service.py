"""
CalibrationService — Serviço de calibração do ambiente.

Responsável por coletar amostras de sinal em ambiente vazio,
calcular baseline estatístico, e detectar movimento durante calibração.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.capture.base import SignalData, SignalProvider
from app.processing.signal_processor import ProcessedFeatures, SignalProcessor


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
        """
        Inicializa o serviço de calibração.

        Args:
            provider: Provider de captura de sinal a ser usado
        """
        self._provider = provider
        self._calibration_samples: list[SignalData] = []
        self._is_calibrating = False
        self._baseline: Optional[BaselineData] = None
        self._adaptive_rate = 0.01  # Taxa de aprendizado adaptativo

    @property
    def is_calibrating(self) -> bool:
        """Retorna True se calibração está em andamento."""
        return self._is_calibrating

    @property
    def baseline(self) -> Optional[BaselineData]:
        """Retorna baseline atual, se disponível."""
        return self._baseline

    async def start_calibration(
        self, duration_seconds: int = 60, profile_name: str = "default"
    ) -> BaselineData:
        """
        Inicia processo de calibração.

        Coleta amostras de sinal por duration_seconds e calcula baseline.
        Detecta movimento durante calibração e levanta exceção se detectado.

        Args:
            duration_seconds: Duração da calibração em segundos (padrão: 60)
            profile_name: Nome do perfil de calibração (padrão: "default")

        Returns:
            BaselineData calculado a partir das amostras

        Raises:
            CalibrationError: Se movimento for detectado durante calibração
        """
        self._is_calibrating = True
        self._calibration_samples.clear()

        # Coleta amostras por duration_seconds
        start_time = time.time()
        sample_count = 0

        while time.time() - start_time < duration_seconds:
            signal = await self._provider.get_signal()

            # Verifica movimento durante calibração
            if self._detect_movement_during_calibration(signal):
                self._is_calibrating = False
                raise CalibrationError("Movimento detectado durante calibração")

            self._calibration_samples.append(signal)
            sample_count += 1

            # Aguarda 1 segundo antes da próxima amostra
            await asyncio.sleep(1.0)

        self._is_calibrating = False
        self._baseline = self._calculate_baseline(profile_name)

        return self._baseline

    def _detect_movement_during_calibration(self, signal: SignalData) -> bool:
        """
        Detecta movimento durante calibração.

        Analisa variação do sinal para identificar movimento.
        Durante calibração, espera-se ambiente estável (sem pessoas).

        Args:
            signal: Sinal capturado

        Returns:
            True se movimento for detectado, False caso contrário
        """
        # Precisa de pelo menos 5 amostras para detectar movimento
        if len(self._calibration_samples) < 5:
            return False

        # Calcula variância das últimas 5 amostras
        recent_rssi = [s.rssi for s in self._calibration_samples[-5:]]
        recent_rssi.append(signal.rssi)

        variance = np.var(recent_rssi)

        # Limiar de movimento: variância > 3.0 indica movimento
        # (baseado em testes empíricos com ambiente vazio vs. com pessoas)
        movement_threshold = 3.0

        return variance > movement_threshold

    def _calculate_baseline(self, profile_name: str) -> BaselineData:
        """
        Calcula baseline a partir das amostras coletadas.

        Extrai estatísticas do sinal (média, desvio padrão, noise floor)
        e das features processadas (variância).

        Args:
            profile_name: Nome do perfil de calibração

        Returns:
            BaselineData com estatísticas calculadas
        """
        if not self._calibration_samples:
            raise ValueError("Nenhuma amostra coletada para calcular baseline")

        # Extrai valores de RSSI
        rssi_values = [s.rssi for s in self._calibration_samples]

        # Processa cada amostra para extrair variance
        processor = SignalProcessor()
        variances = []

        for signal in self._calibration_samples:
            features = processor.process(signal)
            variances.append(features.signal_variance)

        # Calcula estatísticas
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

    def update_baseline_adaptive(
        self, features: ProcessedFeatures, no_presence_duration: float
    ) -> None:
        """
        Atualiza baseline adaptativamente.

        Usa média móvel exponencial (EMA) para atualizar baseline gradualmente
        quando não há presença detectada por tempo suficiente.

        Implementa:
        - Atualização gradual com EMA (taxa configurável)
        - Detecção de mudanças abruptas (>30%)
        - Logging de atualizações significativas (>10%)

        Args:
            features: Features processadas do sinal atual
            no_presence_duration: Duração em segundos sem presença detectada
        """
        import logging

        logger = logging.getLogger(__name__)

        # Só atualiza se não houver presença por pelo menos 5 minutos
        if no_presence_duration < 300:  # 5 minutos
            return

        if self._baseline is None:
            return

        # Calcula mudança percentual para detectar mudanças abruptas
        rssi_change_percent = abs(
            (features.raw_rssi - self._baseline.mean_rssi) / self._baseline.mean_rssi
        ) * 100 if self._baseline.mean_rssi != 0 else 0

        variance_change_percent = abs(
            (features.signal_variance - self._baseline.mean_variance) / self._baseline.mean_variance
        ) * 100 if self._baseline.mean_variance != 0 else 0

        # Detecta mudança abrupta (>30%)
        # Se houver mudança abrupta, não atualiza baseline automaticamente
        if rssi_change_percent > 30 or variance_change_percent > 30:
            logger.warning(
                f"Mudança abrupta detectada - baseline não atualizado. "
                f"RSSI: {rssi_change_percent:.1f}%, Variância: {variance_change_percent:.1f}%"
            )
            return

        # Salva valores antigos para comparação
        old_mean_rssi = self._baseline.mean_rssi
        old_mean_variance = self._baseline.mean_variance

        # Atualização gradual usando média móvel exponencial (EMA)
        self._baseline.mean_rssi = (
            1 - self._adaptive_rate
        ) * self._baseline.mean_rssi + self._adaptive_rate * features.raw_rssi

        self._baseline.mean_variance = (
            1 - self._adaptive_rate
        ) * self._baseline.mean_variance + self._adaptive_rate * features.signal_variance

        # Calcula mudança total após atualização
        total_rssi_change = abs(
            (self._baseline.mean_rssi - old_mean_rssi) / old_mean_rssi
        ) * 100 if old_mean_rssi != 0 else 0

        total_variance_change = abs(
            (self._baseline.mean_variance - old_mean_variance) / old_mean_variance
        ) * 100 if old_mean_variance != 0 else 0

        # Registra atualizações significativas (>10%)
        if total_rssi_change > 10 or total_variance_change > 10:
            logger.info(
                f"Baseline atualizado significativamente. "
                f"RSSI: {old_mean_rssi:.2f} → {self._baseline.mean_rssi:.2f} "
                f"({total_rssi_change:.1f}%), "
                f"Variância: {old_mean_variance:.2f} → {self._baseline.mean_variance:.2f} "
                f"({total_variance_change:.1f}%)"
            )

    def set_baseline(self, baseline: BaselineData) -> None:
        """
        Define baseline manualmente.

        Args:
            baseline: Baseline a ser definido
        """
        self._baseline = baseline

    async def save_baseline(self, profile_name: str) -> None:
        """
        Salva baseline no banco de dados.

        Args:
            profile_name: Nome do perfil de calibração

        Raises:
            ValueError: Se não houver baseline para salvar
        """
        if self._baseline is None:
            raise ValueError("Nenhum baseline disponível para salvar")

        from app.db.database import async_session
        from app.models.models import CalibrationProfile
        from datetime import datetime
        import json
        from sqlalchemy import select

        # Prepara dados do baseline para JSON
        baseline_dict = {
            "mean_rssi": self._baseline.mean_rssi,
            "std_rssi": self._baseline.std_rssi,
            "mean_variance": self._baseline.mean_variance,
            "std_variance": self._baseline.std_variance,
            "noise_floor": self._baseline.noise_floor,
            "samples_count": self._baseline.samples_count,
            "timestamp": self._baseline.timestamp,
            "profile_name": profile_name,
        }

        async with async_session() as db:
            # Verifica se perfil já existe
            result = await db.execute(
                select(CalibrationProfile).where(CalibrationProfile.name == profile_name)
            )
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                # Atualiza perfil existente
                existing_profile.baseline_json = json.dumps(baseline_dict)
                existing_profile.updated_at = datetime.utcnow()
            else:
                # Cria novo perfil
                new_profile = CalibrationProfile(
                    name=profile_name,
                    baseline_json=json.dumps(baseline_dict),
                    created_at=datetime.utcnow(),
                    is_active=False,
                )
                db.add(new_profile)

            await db.commit()

    async def load_baseline(self, profile_name: str) -> BaselineData:
        """
        Carrega baseline do banco de dados.

        Args:
            profile_name: Nome do perfil de calibração

        Returns:
            BaselineData carregado do banco

        Raises:
            ValueError: Se perfil não for encontrado
        """
        from app.db.database import async_session
        from app.models.models import CalibrationProfile
        import json
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(
                select(CalibrationProfile).where(CalibrationProfile.name == profile_name)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                raise ValueError(f"Perfil '{profile_name}' não encontrado")

            # Deserializa JSON para BaselineData
            baseline_dict = json.loads(profile.baseline_json)
            baseline = BaselineData(**baseline_dict)

            # Atualiza baseline interno
            self._baseline = baseline

            return baseline

    def reset(self) -> None:
        """Limpa amostras e baseline."""
        self._calibration_samples.clear()
        self._baseline = None
        self._is_calibrating = False
