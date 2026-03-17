"""
Detector de anomalias usando Isolation Forest.

Detecta padrões anormais automaticamente treinando com dados normais
e calculando scores de anomalia para novos dados.
"""

from __future__ import annotations

from typing import List, Optional

from sklearn.ensemble import IsolationForest

from app.processing.signal_processor import ProcessedFeatures


class AnomalyDetector:
    """Detector de anomalias usando Isolation Forest."""

    def __init__(self, contamination: float = 0.1) -> None:
        """
        Inicializa o detector de anomalias.

        Args:
            contamination: Proporção esperada de anomalias nos dados (padrão: 0.1)
        """
        self._model = IsolationForest(contamination=contamination, random_state=42)
        self._is_trained = False

    def train(self, normal_data: List[ProcessedFeatures]) -> None:
        """
        Treina o modelo com dados normais (sem presença).

        Args:
            normal_data: Lista de features processadas de dados normais
        """
        if not normal_data:
            raise ValueError("normal_data não pode estar vazio")

        X = [self._features_to_array(f) for f in normal_data]
        self._model.fit(X)
        self._is_trained = True

    def detect_anomaly(self, features: ProcessedFeatures) -> tuple[bool, float]:
        """
        Detecta se as features são anômalas.

        Args:
            features: Features processadas para análise

        Returns:
            Tupla (is_anomaly: bool, score: float)
            - is_anomaly: True se for anomalia
            - score: Score de anomalia normalizado [0, 100]

        Raises:
            RuntimeError: Se o modelo não foi treinado
        """
        if not self._is_trained:
            raise RuntimeError("Modelo não foi treinado. Chame train() primeiro.")

        X = [self._features_to_array(features)]
        prediction = self._model.predict(X)[0]
        score_raw = self._model.score_samples(X)[0]

        is_anomaly = bool(prediction == -1)

        # Normaliza score para [0, 100]
        # score_samples retorna valores negativos, quanto mais negativo, mais anômalo
        # Valores típicos: -0.5 (normal) a -1.0 (muito anômalo)
        anomaly_score = abs(score_raw) * 100

        # Garante que está no intervalo [0, 100]
        anomaly_score = max(0.0, min(100.0, anomaly_score))

        return is_anomaly, anomaly_score

    def _features_to_array(self, features: ProcessedFeatures) -> List[float]:
        """
        Converte ProcessedFeatures para array de features.

        Args:
            features: Features processadas

        Returns:
            Lista de valores float para o modelo
        """
        return [
            features.rssi_normalized,
            features.signal_variance,
            features.rate_of_change,
            features.instability_score,
        ]
