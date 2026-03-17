"""
MLDetector — Detector baseado em Machine Learning.

Usa modelo RandomForestClassifier treinado para classificar eventos.
Implementa buffer de 10 segundos para extração de features de janela.
Fallback para HeuristicDetector quando modelo não está disponível.

Implementa Tarefa 8.1:
- Herda de DetectorBase
- Carrega modelo e scaler do diretório models/
- Implementa detect() com buffer de 10 segundos
- Extrai 18 features de janela
- Fallback para HeuristicDetector
- Logging de confiança do modelo

Requisitos: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7
"""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.detection.base import DetectionResult, DetectorBase, EventType
from app.detection.heuristic_detector import HeuristicDetector, ThresholdConfig
from app.processing.signal_processor import ProcessedFeatures


logger = logging.getLogger(__name__)


class MLDetector(DetectorBase):
    """Detector baseado em Machine Learning com fallback heurístico."""

    def __init__(
        self,
        model_path: str | Path = "models/classifier.pkl",
        fallback_config: Optional[ThresholdConfig] = None,
    ) -> None:
        """
        Inicializa MLDetector.

        Args:
            model_path: Caminho para o modelo .pkl treinado
            fallback_config: Configuração para HeuristicDetector fallback

        Raises:
            FileNotFoundError: Se modelo ou scaler não forem encontrados
        """
        self._model_path = Path(model_path)
        self._scaler_path = Path(str(model_path).replace(".pkl", "_scaler.pkl"))

        # Buffer de 10 segundos para features de janela
        self._feature_buffer: deque[ProcessedFeatures] = deque(maxlen=10)

        # Tenta carregar modelo e scaler
        self._model = None
        self._scaler = None
        self._model_loaded = False

        try:
            self._load_model()
        except Exception as e:
            logger.warning(
                f"Não foi possível carregar modelo ML: {e}. "
                f"Usando HeuristicDetector como fallback."
            )

        # Fallback para HeuristicDetector
        self._fallback_detector = HeuristicDetector(fallback_config)

        # Mapeamento de classes para EventType
        self._class_to_event_map = {
            "no_presence": EventType.NO_PRESENCE,
            "presence_still": EventType.PRESENCE_STILL,
            "presence_moving": EventType.PRESENCE_MOVING,
            "fall_suspected": EventType.FALL_SUSPECTED,
            "prolonged_inactivity": EventType.PROLONGED_INACTIVITY,
        }

    def _load_model(self) -> None:
        """
        Carrega modelo e scaler do disco.

        Raises:
            FileNotFoundError: Se arquivos não existirem
            Exception: Se houver erro ao carregar
        """
        if not self._model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {self._model_path}")

        if not self._scaler_path.exists():
            raise FileNotFoundError(f"Scaler não encontrado: {self._scaler_path}")

        self._model = joblib.load(self._model_path)
        self._scaler = joblib.load(self._scaler_path)
        self._model_loaded = True

        logger.info(f"✓ Modelo ML carregado: {self._model_path}")
        logger.info(f"✓ Scaler carregado: {self._scaler_path}")
        logger.info(f"  Classes: {self._model.classes_}")
        logger.info(f"  Features: {self._model.n_features_in_}")

    def detect(self, features: ProcessedFeatures) -> DetectionResult:
        """
        Detecta eventos usando modelo ML ou fallback heurístico.

        Args:
            features: Features processadas do sinal

        Returns:
            DetectionResult com evento detectado e confiança
        """
        # Adiciona features ao buffer
        self._feature_buffer.append(features)

        # Se modelo não está carregado, usa fallback
        if not self._model_loaded:
            return self._fallback_detector.detect(features)

        # Se buffer não está completo (< 10 segundos), usa fallback
        if len(self._feature_buffer) < 10:
            logger.debug(
                f"Buffer incompleto ({len(self._feature_buffer)}/10), "
                f"usando fallback heurístico"
            )
            return self._fallback_detector.detect(features)

        # Extrai features de janela (18 dimensões)
        try:
            X = self._extract_window_features()
            X_scaled = self._scaler.transform([X])

            # Predição do modelo
            proba = self._model.predict_proba(X_scaled)[0]
            predicted_class_idx = np.argmax(proba)
            confidence = float(proba[predicted_class_idx])
            predicted_class_name = self._model.classes_[predicted_class_idx]

            # Converte classe para EventType
            event_type = self._class_to_event(predicted_class_name)

            # Logging de confiança
            logger.debug(
                f"ML Prediction: {event_type.value} "
                f"(confidence: {confidence:.3f}, "
                f"probabilities: {dict(zip(self._model.classes_, proba))})"
            )

            return DetectionResult(
                event_type=event_type,
                confidence=confidence,
                details={
                    "model": "ml",
                    "probabilities": {
                        cls: float(prob)
                        for cls, prob in zip(self._model.classes_, proba)
                    },
                },
            )

        except Exception as e:
            logger.error(f"Erro na predição ML: {e}. Usando fallback heurístico.")
            return self._fallback_detector.detect(features)

    def _extract_window_features(self) -> list[float]:
        """
        Extrai features estatísticas da janela de 10 segundos.

        Calcula média e desvio padrão de 9 features básicas,
        resultando em 18 features totais.

        Returns:
            Lista com 18 features: [9 médias, 9 desvios padrão]
        """
        # Extrai valores de cada feature do buffer
        rssi_norm_values = [f.rssi_normalized for f in self._feature_buffer]
        rssi_smooth_values = [f.rssi_smoothed for f in self._feature_buffer]
        roc_values = [f.rate_of_change for f in self._feature_buffer]
        energy_values = [f.signal_energy for f in self._feature_buffer]
        variance_values = [f.signal_variance for f in self._feature_buffer]
        csi_mean_values = [f.csi_mean_amplitude for f in self._feature_buffer]
        csi_std_values = [f.csi_std_amplitude for f in self._feature_buffer]
        instability_values = [f.instability_score for f in self._feature_buffer]
        raw_rssi_values = [f.raw_rssi for f in self._feature_buffer]

        # Agrupa todas as features
        all_feature_arrays = [
            rssi_norm_values,
            rssi_smooth_values,
            roc_values,
            energy_values,
            variance_values,
            csi_mean_values,
            csi_std_values,
            instability_values,
            raw_rssi_values,
        ]

        # Calcula média e desvio padrão de cada feature
        features_18d = []

        # Primeiro adiciona todas as médias (9 features)
        for values in all_feature_arrays:
            features_18d.append(float(np.mean(values)))

        # Depois adiciona todos os desvios padrão (9 features)
        for values in all_feature_arrays:
            features_18d.append(float(np.std(values)))

        return features_18d

    def _class_to_event(self, class_name: str) -> EventType:
        """
        Converte nome da classe do modelo para EventType.

        Args:
            class_name: Nome da classe predita pelo modelo

        Returns:
            EventType correspondente
        """
        # Tenta mapeamento direto
        if class_name in self._class_to_event_map:
            return self._class_to_event_map[class_name]

        # Fallback: tenta converter string para EventType
        try:
            return EventType(class_name)
        except ValueError:
            logger.warning(
                f"Classe desconhecida '{class_name}', "
                f"usando NO_PRESENCE como fallback"
            )
            return EventType.NO_PRESENCE

    # Diretório seguro onde os modelos são permitidos
    # Definido como atributo de classe para facilitar testes
    _MODELS_DIR: Path = Path(__file__).parent.parent.parent / "models"

    def reload_model(self, new_model_path: str | Path) -> bool:
        """
        Recarrega o modelo ML a partir de um novo caminho.

        Valida o caminho para prevenir path traversal antes de carregar.
        Realiza um swap atômico dos atributos internos, garantindo que
        o loop de monitoramento nunca veja um estado parcial.
        Limpa o buffer de features para evitar predições com dados
        de um modelo diferente.

        Args:
            new_model_path: Nome do arquivo .pkl (ex: 'classifier.pkl').
                Caminhos com '../' ou separadores de diretório são rejeitados.

        Returns:
            True se o modelo foi recarregado com sucesso, False caso contrário
        """
        import os
        import re

        # Extrai apenas o nome do arquivo — descarta qualquer diretório informado
        model_filename = os.path.basename(str(new_model_path))

        # Valida o nome: apenas letras, números, hífen, underscore e ponto
        if not re.match(r'^[a-zA-Z0-9_\-]+\.pkl$', model_filename):
            logger.error(
                f"Nome de modelo inválido rejeitado (path traversal ou caracteres não permitidos): "
                f"'{new_model_path}'"
            )
            return False

        # Constrói caminhos dentro do diretório seguro
        new_path = self._MODELS_DIR / model_filename
        new_scaler_path = self._MODELS_DIR / model_filename.replace(".pkl", "_scaler.pkl")

        # Verifica que os caminhos resolvidos não escapam do diretório seguro
        try:
            resolved_model = new_path.resolve()
            resolved_scaler = new_scaler_path.resolve()
            models_dir_resolved = self._MODELS_DIR.resolve()

            if not str(resolved_model).startswith(str(models_dir_resolved)):
                logger.error(f"Tentativa de path traversal detectada: '{new_model_path}'")
                return False
            if not str(resolved_scaler).startswith(str(models_dir_resolved)):
                logger.error(f"Tentativa de path traversal no scaler: '{new_model_path}'")
                return False
        except Exception as e:
            logger.error(f"Erro ao resolver caminho do modelo: {e}")
            return False

        try:
            # Carrega os novos artefatos antes de substituir os antigos
            new_model = joblib.load(new_path)
            new_scaler = joblib.load(new_scaler_path)
        except FileNotFoundError as e:
            logger.error(f"Arquivo de modelo não encontrado: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar novo modelo '{new_path}': {e}")
            return False

        # Swap atômico — o GIL garante que atribuições simples são indivisíveis
        # no contexto do event loop asyncio (single-threaded)
        self._model_path = new_path
        self._scaler_path = new_scaler_path
        self._model = new_model
        self._scaler = new_scaler
        self._model_loaded = True

        # Limpa buffer: amostras antigas são incompatíveis com o novo scaler
        self._feature_buffer.clear()

        logger.info(
            f"✓ Modelo ML recarregado com sucesso: {new_path} "
            f"| classes: {new_model.classes_} "
            f"| features: {new_model.n_features_in_}"
        )
        return True

    def reset(self) -> None:
        """Reseta estado interno do detector."""
        self._feature_buffer.clear()
        self._fallback_detector.reset()
        logger.debug("MLDetector resetado")

    def is_model_loaded(self) -> bool:
        """
        Verifica se modelo ML está carregado.

        Returns:
            True se modelo está carregado, False caso contrário
        """
        return self._model_loaded

    def get_model_info(self) -> dict:
        """
        Retorna informações sobre o modelo carregado.

        Returns:
            Dicionário com informações do modelo
        """
        if not self._model_loaded:
            return {
                "loaded": False,
                "fallback": "HeuristicDetector",
            }

        return {
            "loaded": True,
            "model_path": str(self._model_path),
            "scaler_path": str(self._scaler_path),
            "classes": list(self._model.classes_),
            "n_features": self._model.n_features_in_,
            "n_estimators": getattr(self._model, "n_estimators", None),
            "fallback": "HeuristicDetector",
        }
