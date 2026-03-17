# -*- coding: utf-8 -*-
"""
Event Detector - Algoritmos de Detecção de Eventos
Implementa lógica de detecção baseada em RSSI e CSI
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionResult:
    """
    Resultado da detecção de evento.
    
    Attributes:
        event_type: Tipo do evento detectado
        confidence: Nível de confiança (0.0 a 1.0)
        metadata: Dados adicionais sobre a detecção
    """
    event_type: str
    confidence: float
    metadata: Dict[str, Any]


class EventDetector:
    """
    Detector de eventos baseado em sinais Wi-Fi.
    
    Implementa algoritmos de detecção para RSSI (plano BÁSICO)
    e CSI (plano PREMIUM).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o detector com configuração do tenant.
        
        Args:
            config: Configuração do tenant incluindo thresholds e min_confidence
        """
        self.config = config
        self.plan_type = config.get("plan_type", "basic")
        
        # Thresholds padrão para detecção RSSI
        self.presence_threshold = config.get("presence_threshold", 0.6)
        self.low_variance_threshold = config.get("low_variance_threshold", 0.2)
        self.high_variance_threshold = config.get("high_variance_threshold", 0.4)
        self.movement_threshold = config.get("movement_threshold", 0.5)
        self.fall_threshold = config.get("fall_threshold", 0.7)
        self.inactivity_threshold = config.get("inactivity_threshold", 300)  # 5 minutos
        
        logger.info(
            "EventDetector inicializado",
            plan_type=self.plan_type,
            presence_threshold=self.presence_threshold
        )
    
    def detect(self, features: Dict[str, Any], data_type: str) -> Optional[DetectionResult]:
        """
        Executa detecção de evento baseado nas features.
        
        Args:
            features: Features extraídas dos sinais Wi-Fi
            data_type: Tipo de dados (rssi ou csi)
        
        Returns:
            DetectionResult se evento detectado, None caso contrário
        """
        if data_type == "csi" and self.plan_type == "premium":
            return self._detect_with_csi(features)
        else:
            return self._detect_with_rssi(features)
    
    def _detect_with_rssi(self, features: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Detecção baseada em RSSI (plano BÁSICO).
        
        Usa heurísticas simples baseadas em:
        - rssi_normalized: Força do sinal normalizada
        - signal_variance: Variância do sinal
        - rate_of_change: Taxa de mudança do sinal
        - instability_score: Score de instabilidade
        
        Args:
            features: Features RSSI extraídas
        
        Returns:
            DetectionResult se evento detectado, None caso contrário
        """
        rssi_normalized = features.get("rssi_normalized", 0.0)
        signal_variance = features.get("signal_variance", 0.0)
        rate_of_change = features.get("rate_of_change", 0.0)
        instability_score = features.get("instability_score", 0.0)
        
        logger.debug(
            "Executando detecção RSSI",
            rssi_normalized=rssi_normalized,
            signal_variance=signal_variance,
            rate_of_change=rate_of_change
        )
        
        # Detecção de presença
        if rssi_normalized > self.presence_threshold:
            if signal_variance < self.low_variance_threshold:
                # Sinal forte mas baixa variância = sem presença
                return DetectionResult(
                    event_type="no_presence",
                    confidence=0.75,
                    metadata={
                        "reason": "low_signal_low_variance",
                        "rssi_normalized": rssi_normalized,
                        "signal_variance": signal_variance
                    }
                )
            else:
                # Sinal forte e alta variância = presença detectada
                return DetectionResult(
                    event_type="presence",
                    confidence=0.85,
                    metadata={
                        "reason": "high_signal_high_variance",
                        "rssi_normalized": rssi_normalized,
                        "signal_variance": signal_variance
                    }
                )
        
        # Detecção de movimento
        if rate_of_change > self.movement_threshold and signal_variance > self.high_variance_threshold:
            return DetectionResult(
                event_type="movement",
                confidence=0.80,
                metadata={
                    "reason": "high_rate_of_change",
                    "rate_of_change": rate_of_change,
                    "signal_variance": signal_variance
                }
            )
        
        # Detecção de inatividade prolongada
        if instability_score < 0.1 and rssi_normalized > self.presence_threshold:
            return DetectionResult(
                event_type="prolonged_inactivity",
                confidence=0.70,
                metadata={
                    "reason": "low_instability_with_presence",
                    "instability_score": instability_score,
                    "rssi_normalized": rssi_normalized
                }
            )
        
        # Nenhum evento detectado
        return None
    
    def _detect_with_csi(self, features: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Detecção baseada em CSI (plano PREMIUM).
        
        Usa features avançadas de CSI para detecção mais precisa:
        - csi_amplitude: Amplitude do CSI
        - csi_phase: Fase do CSI
        - csi_variance: Variância do CSI
        - doppler_shift: Deslocamento Doppler (para movimento)
        
        Args:
            features: Features CSI extraídas
        
        Returns:
            DetectionResult se evento detectado, None caso contrário
        """
        csi_amplitude = features.get("csi_amplitude", 0.0)
        csi_variance = features.get("csi_variance", 0.0)
        doppler_shift = features.get("doppler_shift", 0.0)
        
        logger.debug(
            "Executando detecção CSI",
            csi_amplitude=csi_amplitude,
            csi_variance=csi_variance,
            doppler_shift=doppler_shift
        )
        
        # Detecção de presença (mais precisa com CSI)
        if csi_amplitude > 0.7 and csi_variance > 0.3:
            return DetectionResult(
                event_type="presence",
                confidence=0.92,
                metadata={
                    "reason": "csi_high_amplitude_variance",
                    "csi_amplitude": csi_amplitude,
                    "csi_variance": csi_variance
                }
            )
        
        # Detecção de movimento (usando Doppler)
        if abs(doppler_shift) > 0.5:
            return DetectionResult(
                event_type="movement",
                confidence=0.88,
                metadata={
                    "reason": "doppler_shift_detected",
                    "doppler_shift": doppler_shift
                }
            )
        
        # Detecção de queda (padrão específico no CSI)
        # Queda geralmente causa pico súbito seguido de estabilização
        if csi_variance > 0.8 and doppler_shift > 0.7:
            return DetectionResult(
                event_type="fall_suspected",
                confidence=0.85,
                metadata={
                    "reason": "sudden_csi_change_pattern",
                    "csi_variance": csi_variance,
                    "doppler_shift": doppler_shift
                }
            )
        
        # Detecção de inatividade prolongada
        if csi_variance < 0.15 and csi_amplitude > 0.6:
            return DetectionResult(
                event_type="prolonged_inactivity",
                confidence=0.78,
                metadata={
                    "reason": "low_csi_variance_with_presence",
                    "csi_variance": csi_variance,
                    "csi_amplitude": csi_amplitude
                }
            )
        
        # Nenhum evento detectado
        return None
