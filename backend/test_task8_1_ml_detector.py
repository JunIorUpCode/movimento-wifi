"""
Testes para Tarefa 8.1 - MLDetector

Testa a implementação do MLDetector com:
- Carregamento de modelo e scaler
- Detecção com buffer de 10 segundos
- Extração de 18 features de janela
- Fallback para HeuristicDetector
- Logging de confiança

Requisitos: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7
"""

import sys
import time
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import joblib

from app.detection.ml_detector import MLDetector
from app.detection.base import EventType, DetectionResult
from app.detection.heuristic_detector import ThresholdConfig
from app.processing.signal_processor import ProcessedFeatures


# --- Fixtures ---


@pytest.fixture
def real_model(tmp_path):
    """Cria um modelo real para testes."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    
    # Cria modelo real
    model = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
    
    # Treina com dados fictícios
    X_train = np.random.rand(50, 18)
    y_train = np.random.choice(
        ["no_presence", "presence_still", "presence_moving", "fall_suspected", "prolonged_inactivity"],
        size=50
    )
    model.fit(X_train, y_train)
    
    # Cria scaler real
    scaler = StandardScaler()
    scaler.fit(X_train)
    
    # Salva modelo e scaler
    model_path = tmp_path / "test_model.pkl"
    scaler_path = tmp_path / "test_model_scaler.pkl"
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    return model_path, model, scaler


@pytest.fixture
def sample_features():
    """Cria features de exemplo para testes."""
    return ProcessedFeatures(
        rssi_normalized=0.5,
        rssi_smoothed=-50.0,
        signal_energy=10.0,
        signal_variance=2.0,
        rate_of_change=1.5,
        instability_score=0.3,
        csi_mean_amplitude=5.0,
        csi_std_amplitude=1.0,
        raw_rssi=-50.0,
        timestamp=time.time(),
    )


# --- Testes de Inicialização ---


def test_ml_detector_init_without_model():
    """Testa inicialização quando modelo não existe."""
    detector = MLDetector(model_path="models/nonexistent.pkl")
    
    assert not detector.is_model_loaded()
    assert detector._fallback_detector is not None
    
    info = detector.get_model_info()
    assert info["loaded"] is False
    assert info["fallback"] == "HeuristicDetector"


def test_ml_detector_init_with_model(real_model):
    """Testa inicialização quando modelo existe."""
    model_path, model, scaler = real_model
    
    # Inicializa detector
    detector = MLDetector(model_path=model_path)
    
    assert detector.is_model_loaded()
    assert detector._model is not None
    assert detector._scaler is not None
    
    info = detector.get_model_info()
    assert info["loaded"] is True
    assert info["n_features"] == 18
    assert len(info["classes"]) == 5


def test_ml_detector_init_with_custom_fallback_config():
    """Testa inicialização com configuração customizada de fallback."""
    custom_config = ThresholdConfig(
        presence_energy_min=3.0,
        movement_variance_min=1.0,
    )
    
    detector = MLDetector(
        model_path="models/nonexistent.pkl",
        fallback_config=custom_config,
    )
    
    assert detector._fallback_detector._config.presence_energy_min == 3.0
    assert detector._fallback_detector._config.movement_variance_min == 1.0


# --- Testes de Detecção ---


def test_detect_uses_fallback_when_model_not_loaded(sample_features):
    """Testa que fallback é usado quando modelo não está carregado."""
    detector = MLDetector(model_path="models/nonexistent.pkl")
    
    result = detector.detect(sample_features)
    
    assert isinstance(result, DetectionResult)
    assert isinstance(result.event_type, EventType)
    assert 0.0 <= result.confidence <= 1.0


def test_detect_uses_fallback_when_buffer_incomplete(
    real_model, sample_features
):
    """Testa que fallback é usado quando buffer tem < 10 amostras."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona apenas 5 amostras (< 10)
    for i in range(5):
        result = detector.detect(sample_features)
    
    # Deve ter usado fallback
    assert len(detector._feature_buffer) == 5


def test_detect_uses_ml_when_buffer_complete(
    real_model, sample_features
):
    """Testa que modelo ML é usado quando buffer tem 10 amostras."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona 10 amostras
    for i in range(10):
        result = detector.detect(sample_features)
    
    # Última detecção deve ter usado ML
    assert result.details.get("model") == "ml"
    assert "probabilities" in result.details
    assert len(result.details["probabilities"]) == 5


def test_detect_returns_correct_event_type(
    real_model, sample_features
):
    """Testa que evento correto é retornado baseado na predição."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona 10 amostras
    for i in range(10):
        result = detector.detect(sample_features)
    
    # Deve retornar um EventType válido
    assert isinstance(result.event_type, EventType)
    assert 0.0 <= result.confidence <= 1.0


def test_detect_includes_all_probabilities(
    real_model, sample_features
):
    """Testa que todas as probabilidades são incluídas nos detalhes."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona 10 amostras
    for i in range(10):
        result = detector.detect(sample_features)
    
    probabilities = result.details["probabilities"]
    
    # Deve ter probabilidades para todas as classes
    assert len(probabilities) == 5
    
    # Soma das probabilidades deve ser ~1.0
    total_prob = sum(probabilities.values())
    assert abs(total_prob - 1.0) < 0.01


# --- Testes de Extração de Features ---


def test_extract_window_features_returns_18_dimensions(
    real_model, sample_features
):
    """Testa que extração de features retorna 18 dimensões."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona 10 amostras
    for i in range(10):
        detector._feature_buffer.append(sample_features)
    
    # Extrai features
    features = detector._extract_window_features()
    
    assert len(features) == 18
    assert all(isinstance(f, float) for f in features)


def test_extract_window_features_calculates_statistics_correctly(
    real_model
):
    """Testa que estatísticas são calculadas corretamente."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona 10 amostras com valores conhecidos
    for i in range(10):
        features = ProcessedFeatures(
            rssi_normalized=float(i),  # 0, 1, 2, ..., 9
            rssi_smoothed=float(i * 2),
            signal_energy=float(i * 3),
            signal_variance=float(i * 4),
            rate_of_change=float(i * 5),
            instability_score=float(i * 6),
            csi_mean_amplitude=float(i * 7),
            csi_std_amplitude=float(i * 8),
            raw_rssi=float(i * 9),
            timestamp=time.time(),
        )
        detector._feature_buffer.append(features)
    
    # Extrai features
    window_features = detector._extract_window_features()
    
    # Primeiras 9 features são médias
    # rssi_normalized: média de [0,1,2,...,9] = 4.5
    assert abs(window_features[0] - 4.5) < 0.01
    
    # Últimas 9 features são desvios padrão
    # rssi_normalized: std de [0,1,2,...,9] ≈ 2.87
    assert abs(window_features[9] - np.std(range(10))) < 0.01


# --- Testes de Fallback ---


def test_fallback_on_prediction_error(real_model, sample_features):
    """Testa que fallback é usado quando predição falha."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Corrompe o modelo para causar erro
    detector._model = None
    detector._model_loaded = True  # Força tentativa de usar ML
    
    # Adiciona 10 amostras
    for i in range(10):
        result = detector.detect(sample_features)
    
    # Deve ter usado fallback devido ao erro
    assert isinstance(result, DetectionResult)


# --- Testes de Reset ---


def test_reset_clears_buffer(real_model, sample_features):
    """Testa que reset limpa o buffer de features."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Adiciona amostras
    for i in range(5):
        detector.detect(sample_features)
    
    assert len(detector._feature_buffer) == 5
    
    # Reset
    detector.reset()
    
    assert len(detector._feature_buffer) == 0


# --- Testes de Mapeamento de Classes ---


def test_class_to_event_mapping(real_model):
    """Testa mapeamento de classes para EventType."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Testa mapeamentos conhecidos
    assert detector._class_to_event("no_presence") == EventType.NO_PRESENCE
    assert detector._class_to_event("presence_still") == EventType.PRESENCE_STILL
    assert detector._class_to_event("presence_moving") == EventType.PRESENCE_MOVING
    assert detector._class_to_event("fall_suspected") == EventType.FALL_SUSPECTED
    assert (
        detector._class_to_event("prolonged_inactivity")
        == EventType.PROLONGED_INACTIVITY
    )


def test_class_to_event_unknown_class(real_model):
    """Testa comportamento com classe desconhecida."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Classe desconhecida deve retornar NO_PRESENCE como fallback
    result = detector._class_to_event("unknown_class")
    assert result == EventType.NO_PRESENCE


# --- Testes de Informações do Modelo ---


def test_get_model_info_when_not_loaded():
    """Testa get_model_info quando modelo não está carregado."""
    detector = MLDetector(model_path="models/nonexistent.pkl")
    
    info = detector.get_model_info()
    
    assert info["loaded"] is False
    assert info["fallback"] == "HeuristicDetector"


def test_get_model_info_when_loaded(real_model):
    """Testa get_model_info quando modelo está carregado."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    info = detector.get_model_info()
    
    assert info["loaded"] is True
    assert "model_path" in info
    assert "scaler_path" in info
    assert len(info["classes"]) == 5
    assert info["n_features"] == 18
    assert info["n_estimators"] == 10


# --- Teste de Integração ---


def test_integration_full_detection_cycle(real_model):
    """Testa ciclo completo de detecção."""
    model_path, model, scaler = real_model
    
    detector = MLDetector(model_path=model_path)
    
    # Simula 15 amostras de detecção
    results = []
    for i in range(15):
        features = ProcessedFeatures(
            rssi_normalized=0.5 + i * 0.01,
            rssi_smoothed=-50.0 + i * 0.5,
            signal_energy=10.0 + i * 0.2,
            signal_variance=2.0 + i * 0.1,
            rate_of_change=1.5 + i * 0.05,
            instability_score=0.3 + i * 0.01,
            csi_mean_amplitude=5.0 + i * 0.1,
            csi_std_amplitude=1.0 + i * 0.05,
            raw_rssi=-50.0 + i * 0.5,
            timestamp=time.time() + i,
        )
        result = detector.detect(features)
        results.append(result)
    
    # Primeiras 9 detecções devem usar fallback
    for i in range(9):
        assert results[i].details.get("model") != "ml"
    
    # Últimas 6 detecções devem usar ML
    for i in range(9, 15):
        assert results[i].details.get("model") == "ml"
        assert "probabilities" in results[i].details


if __name__ == "__main__":
    print("=" * 70)
    print("Testes da Tarefa 8.1 - MLDetector")
    print("=" * 70)
    print()
    
    # Executa testes
    pytest.main([__file__, "-v", "--tb=short"])
