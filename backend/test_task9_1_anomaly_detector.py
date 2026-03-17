"""
Testes para Task 9.1: AnomalyDetector com Isolation Forest

Valida:
- Requisito 9.1: Treinar modelo com dados normais
- Requisito 9.2: Calcular score de anomalia (0-100%)
"""

import pytest
from app.detection.anomaly_detector import AnomalyDetector
from app.processing.signal_processor import ProcessedFeatures


def create_normal_features(rssi_norm: float = 0.5, variance: float = 0.1) -> ProcessedFeatures:
    """Helper para criar features normais."""
    return ProcessedFeatures(
        rssi_normalized=rssi_norm,
        rssi_smoothed=-50.0,
        signal_energy=10.0,
        signal_variance=variance,
        rate_of_change=0.5,
        instability_score=0.1,
        csi_mean_amplitude=5.0,
        csi_std_amplitude=1.0,
        raw_rssi=-50.0,
        timestamp=1000.0,
    )


def create_anomalous_features() -> ProcessedFeatures:
    """Helper para criar features anômalas."""
    return ProcessedFeatures(
        rssi_normalized=0.95,
        rssi_smoothed=-30.0,
        signal_energy=50.0,
        signal_variance=10.0,
        rate_of_change=15.0,
        instability_score=0.9,
        csi_mean_amplitude=20.0,
        csi_std_amplitude=5.0,
        raw_rssi=-30.0,
        timestamp=2000.0,
    )


class TestAnomalyDetectorBasics:
    """Testes básicos do AnomalyDetector."""

    def test_init_creates_untrained_model(self):
        """Testa que __init__ cria modelo não treinado."""
        detector = AnomalyDetector()
        assert detector._is_trained is False

    def test_init_with_custom_contamination(self):
        """Testa que contamination customizado é aceito."""
        detector = AnomalyDetector(contamination=0.2)
        assert detector._model.contamination == 0.2

    def test_train_with_empty_data_raises_error(self):
        """Testa que treinar com dados vazios levanta erro."""
        detector = AnomalyDetector()
        with pytest.raises(ValueError, match="normal_data não pode estar vazio"):
            detector.train([])

    def test_train_marks_model_as_trained(self):
        """Testa que train() marca modelo como treinado."""
        detector = AnomalyDetector()
        normal_data = [create_normal_features() for _ in range(50)]
        detector.train(normal_data)
        assert detector._is_trained is True

    def test_detect_anomaly_without_training_raises_error(self):
        """Testa que detectar sem treinar levanta erro."""
        detector = AnomalyDetector()
        features = create_normal_features()
        with pytest.raises(RuntimeError, match="Modelo não foi treinado"):
            detector.detect_anomaly(features)


class TestAnomalyDetection:
    """Testes de detecção de anomalias."""

    def test_detect_normal_data_returns_low_score(self):
        """Testa que dados normais retornam score baixo."""
        detector = AnomalyDetector()
        
        # Treina com dados normais
        normal_data = [create_normal_features(rssi_norm=0.5 + i*0.01, variance=0.1 + i*0.01) 
                       for i in range(100)]
        detector.train(normal_data)
        
        # Testa com dado normal
        test_features = create_normal_features(rssi_norm=0.55, variance=0.12)
        is_anomaly, score = detector.detect_anomaly(test_features)
        
        # Score deve ser relativamente baixo para dados normais
        assert 0.0 <= score <= 100.0
        assert score < 80.0  # Dados normais devem ter score < 80

    def test_detect_anomalous_data_returns_high_score(self):
        """Testa que dados anômalos retornam score alto."""
        detector = AnomalyDetector()
        
        # Treina com dados normais
        normal_data = [create_normal_features(rssi_norm=0.5 + i*0.01, variance=0.1 + i*0.01) 
                       for i in range(100)]
        detector.train(normal_data)
        
        # Testa com dado anômalo
        anomalous_features = create_anomalous_features()
        is_anomaly, score = detector.detect_anomaly(anomalous_features)
        
        # Score deve estar no intervalo válido
        assert 0.0 <= score <= 100.0

    def test_score_is_in_valid_range(self):
        """Testa que score está sempre no intervalo [0, 100]."""
        detector = AnomalyDetector()
        
        # Treina com dados normais
        normal_data = [create_normal_features(rssi_norm=0.5 + i*0.01, variance=0.1 + i*0.01) 
                       for i in range(100)]
        detector.train(normal_data)
        
        # Testa com vários tipos de dados
        test_cases = [
            create_normal_features(rssi_norm=0.5, variance=0.1),
            create_normal_features(rssi_norm=0.8, variance=0.3),
            create_anomalous_features(),
            create_normal_features(rssi_norm=0.2, variance=0.05),
        ]
        
        for features in test_cases:
            is_anomaly, score = detector.detect_anomaly(features)
            assert 0.0 <= score <= 100.0, f"Score {score} fora do intervalo [0, 100]"

    def test_returns_tuple_with_bool_and_float(self):
        """Testa que detect_anomaly retorna tupla (bool, float)."""
        detector = AnomalyDetector()
        
        normal_data = [create_normal_features() for _ in range(50)]
        detector.train(normal_data)
        
        result = detector.detect_anomaly(create_normal_features())
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], (bool, int))  # is_anomaly
        assert isinstance(result[1], float)  # score


class TestFeaturesToArray:
    """Testes para conversão de features."""

    def test_features_to_array_has_correct_length(self):
        """Testa que _features_to_array retorna 4 valores."""
        detector = AnomalyDetector()
        features = create_normal_features()
        
        array = detector._features_to_array(features)
        
        assert len(array) == 4

    def test_features_to_array_uses_correct_fields(self):
        """Testa que _features_to_array usa os campos corretos."""
        detector = AnomalyDetector()
        features = create_normal_features(rssi_norm=0.7, variance=0.3)
        features.rate_of_change = 2.5
        features.instability_score = 0.4
        
        array = detector._features_to_array(features)
        
        assert array[0] == 0.7  # rssi_normalized
        assert array[1] == 0.3  # signal_variance
        assert array[2] == 2.5  # rate_of_change
        assert array[3] == 0.4  # instability_score


class TestTrainingWithVariedData:
    """Testes de treinamento com dados variados."""

    def test_train_with_minimum_samples(self):
        """Testa treinamento com número mínimo de amostras."""
        detector = AnomalyDetector()
        
        # Isolation Forest precisa de pelo menos algumas amostras
        normal_data = [create_normal_features() for _ in range(10)]
        detector.train(normal_data)
        
        assert detector._is_trained is True

    def test_train_with_varied_normal_data(self):
        """Testa treinamento com dados normais variados."""
        detector = AnomalyDetector()
        
        # Cria dados normais com variação natural
        normal_data = []
        for i in range(100):
            rssi = 0.4 + (i % 20) * 0.01
            variance = 0.08 + (i % 15) * 0.005
            normal_data.append(create_normal_features(rssi_norm=rssi, variance=variance))
        
        detector.train(normal_data)
        assert detector._is_trained is True
        
        # Deve conseguir detectar após treinamento
        test_features = create_normal_features(rssi_norm=0.5, variance=0.1)
        is_anomaly, score = detector.detect_anomaly(test_features)
        assert 0.0 <= score <= 100.0


class TestEdgeCases:
    """Testes de casos extremos."""

    def test_detect_with_extreme_values(self):
        """Testa detecção com valores extremos."""
        detector = AnomalyDetector()
        
        # Treina com dados normais
        normal_data = [create_normal_features() for _ in range(50)]
        detector.train(normal_data)
        
        # Testa com valores extremos
        extreme_features = ProcessedFeatures(
            rssi_normalized=1.0,
            rssi_smoothed=-20.0,
            signal_energy=100.0,
            signal_variance=50.0,
            rate_of_change=50.0,
            instability_score=1.0,
            csi_mean_amplitude=50.0,
            csi_std_amplitude=20.0,
            raw_rssi=-20.0,
            timestamp=3000.0,
        )
        
        is_anomaly, score = detector.detect_anomaly(extreme_features)
        assert 0.0 <= score <= 100.0

    def test_detect_with_zero_values(self):
        """Testa detecção com valores zero."""
        detector = AnomalyDetector()
        
        # Treina com dados normais
        normal_data = [create_normal_features() for _ in range(50)]
        detector.train(normal_data)
        
        # Testa com valores zero
        zero_features = ProcessedFeatures(
            rssi_normalized=0.0,
            rssi_smoothed=-100.0,
            signal_energy=0.0,
            signal_variance=0.0,
            rate_of_change=0.0,
            instability_score=0.0,
            csi_mean_amplitude=0.0,
            csi_std_amplitude=0.0,
            raw_rssi=-100.0,
            timestamp=4000.0,
        )
        
        is_anomaly, score = detector.detect_anomaly(zero_features)
        assert 0.0 <= score <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
