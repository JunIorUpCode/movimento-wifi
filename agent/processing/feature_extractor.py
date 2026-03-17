# -*- coding: utf-8 -*-
"""
Extrator de Features Locais
Processa sinais capturados e extrai features para transmissão
"""

import sys
import os
from typing import Dict, Any

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.capture.base import SignalData
from app.processing.signal_processor import SignalProcessor, ProcessedFeatures


class FeatureExtractor:
    """
    Extrator de features locais.
    Reutiliza o SignalProcessor do backend para processar sinais.
    """
    
    def __init__(
        self,
        window_size: int = 50,
        smoothing_window: int = 5,
        rssi_min: float = -100.0,
        rssi_max: float = -20.0
    ):
        """
        Inicializa o extrator de features.
        
        Args:
            window_size: Tamanho da janela temporal para cálculo de features
            smoothing_window: Tamanho da janela para suavização
            rssi_min: Valor mínimo de RSSI para normalização
            rssi_max: Valor máximo de RSSI para normalização
        """
        self.processor = SignalProcessor(
            window_size=window_size,
            smoothing_window=smoothing_window,
            rssi_min=rssi_min,
            rssi_max=rssi_max
        )
    
    def extract_features(self, signal: SignalData) -> Dict[str, Any]:
        """
        Extrai features de um sinal capturado.
        
        Args:
            signal: Dados do sinal capturado
        
        Returns:
            Dict contendo features processadas:
                - rssi_normalized: RSSI normalizado [0, 1]
                - rssi_smoothed: RSSI suavizado
                - signal_energy: Energia média do CSI
                - signal_variance: Variância do CSI
                - rate_of_change: Taxa de variação do RSSI
                - instability_score: Score de instabilidade [0, 1]
                - csi_mean_amplitude: Amplitude média das subportadoras
                - csi_std_amplitude: Desvio padrão das amplitudes
                - raw_rssi: RSSI bruto original
                - timestamp: Timestamp da amostra
                - provider: Nome do provider usado
        """
        # Processa o sinal usando o SignalProcessor do backend
        features: ProcessedFeatures = self.processor.process(signal)
        
        # Converte para dicionário para transmissão
        return {
            "rssi_normalized": features.rssi_normalized,
            "rssi_smoothed": features.rssi_smoothed,
            "signal_energy": features.signal_energy,
            "signal_variance": features.signal_variance,
            "rate_of_change": features.rate_of_change,
            "instability_score": features.instability_score,
            "csi_mean_amplitude": features.csi_mean_amplitude,
            "csi_std_amplitude": features.csi_std_amplitude,
            "raw_rssi": features.raw_rssi,
            "timestamp": features.timestamp,
            "provider": signal.provider,
            "has_csi": len(signal.csi_amplitude) > 0
        }
    
    def reset(self) -> None:
        """Reseta os buffers internos do processador"""
        self.processor.reset()
