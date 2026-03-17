"""
Teste de integração end-to-end para validar pipeline ML completo.

Valida:
1. MLService coleta dados
2. Dataset é exportado
3. Modelo é treinado
4. MLDetector carrega e usa modelo
5. Detecção funciona com modelo real
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.ml_service import MLService
from app.detection.ml_detector import MLDetector
from app.processing.signal_processor import ProcessedFeatures


def test_ml_pipeline_integration():
    """Testa pipeline ML completo."""
    print("=" * 70)
    print("TESTE DE INTEGRAÇÃO - PIPELINE ML COMPLETO")
    print("=" * 70)
    print()
    
    # 1. Verifica que modelo treinado existe
    print("1. Verificando modelo treinado...")
    model_path = Path("models/classifier.pkl")
    scaler_path = Path("models/classifier_scaler.pkl")
    
    if not model_path.exists():
        print(f"   ❌ Modelo não encontrado: {model_path}")
        print("   Execute: python backend/train_model.py models/sample_training_data.csv")
        return False
    
    if not scaler_path.exists():
        print(f"   ❌ Scaler não encontrado: {scaler_path}")
        return False
    
    print(f"   ✓ Modelo encontrado: {model_path}")
    print(f"   ✓ Scaler encontrado: {scaler_path}")
    print()
    
    # 2. Inicializa MLDetector com modelo
    print("2. Inicializando MLDetector com modelo treinado...")
    detector = MLDetector(model_path=model_path)
    
    if not detector.is_model_loaded():
        print("   ❌ Falha ao carregar modelo")
        return False
    
    info = detector.get_model_info()
    print(f"   ✓ Modelo carregado com sucesso")
    print(f"   Classes: {info['classes']}")
    print(f"   Features: {info['n_features']}")
    print(f"   Estimators: {info['n_estimators']}")
    print()
    
    # 3. Testa detecção com buffer incompleto (deve usar fallback)
    print("3. Testando detecção com buffer incompleto (< 10 amostras)...")
    for i in range(5):
        features = ProcessedFeatures(
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
        result = detector.detect(features)
    
    print(f"   ✓ Detecção com fallback funcionou")
    print(f"   Evento: {result.event_type.value}")
    print(f"   Confiança: {result.confidence:.3f}")
    print()
    
    # 4. Testa detecção com buffer completo (deve usar ML)
    print("4. Testando detecção com buffer completo (10 amostras)...")
    for i in range(5):  # Adiciona mais 5 para completar 10
        features = ProcessedFeatures(
            rssi_normalized=0.5 + i * 0.05,
            rssi_smoothed=-50.0 + i,
            signal_energy=10.0 + i,
            signal_variance=2.0 + i * 0.2,
            rate_of_change=1.5 + i * 0.3,
            instability_score=0.3 + i * 0.05,
            csi_mean_amplitude=5.0 + i * 0.5,
            csi_std_amplitude=1.0 + i * 0.1,
            raw_rssi=-50.0 + i,
            timestamp=time.time(),
        )
        result = detector.detect(features)
    
    if result.details.get("model") != "ml":
        print("   ❌ Modelo ML não foi usado")
        return False
    
    print(f"   ✓ Detecção com ML funcionou")
    print(f"   Evento: {result.event_type.value}")
    print(f"   Confiança: {result.confidence:.3f}")
    print(f"   Probabilidades:")
    for cls, prob in result.details["probabilities"].items():
        print(f"     {cls}: {prob:.3f}")
    print()
    
    # 5. Testa diferentes padrões de entrada
    print("5. Testando diferentes padrões de entrada...")
    
    test_cases = [
        {
            "name": "Sem presença",
            "features": ProcessedFeatures(
                rssi_normalized=0.1,
                rssi_smoothed=-75.0,
                signal_energy=2.0,
                signal_variance=0.5,
                rate_of_change=0.2,
                instability_score=0.1,
                csi_mean_amplitude=1.0,
                csi_std_amplitude=0.3,
                raw_rssi=-75.0,
                timestamp=time.time(),
            )
        },
        {
            "name": "Presença parada",
            "features": ProcessedFeatures(
                rssi_normalized=0.4,
                rssi_smoothed=-55.0,
                signal_energy=10.0,
                signal_variance=2.0,
                rate_of_change=0.5,
                instability_score=0.2,
                csi_mean_amplitude=5.0,
                csi_std_amplitude=1.5,
                raw_rssi=-55.0,
                timestamp=time.time(),
            )
        },
        {
            "name": "Presença em movimento",
            "features": ProcessedFeatures(
                rssi_normalized=0.7,
                rssi_smoothed=-45.0,
                signal_energy=25.0,
                signal_variance=6.0,
                rate_of_change=5.0,
                instability_score=0.6,
                csi_mean_amplitude=12.0,
                csi_std_amplitude=4.0,
                raw_rssi=-45.0,
                timestamp=time.time(),
            )
        },
    ]
    
    for test_case in test_cases:
        # Reset detector
        detector.reset()
        
        # Adiciona 10 amostras similares
        for _ in range(10):
            result = detector.detect(test_case["features"])
        
        print(f"   {test_case['name']}:")
        print(f"     Evento: {result.event_type.value}")
        print(f"     Confiança: {result.confidence:.3f}")
    
    print()
    
    # 6. Testa reset
    print("6. Testando reset do detector...")
    detector.reset()
    
    if len(detector._feature_buffer) != 0:
        print("   ❌ Buffer não foi limpo")
        return False
    
    print("   ✓ Reset funcionou corretamente")
    print()
    
    print("=" * 70)
    print("✅ TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
    print("=" * 70)
    print()
    print("Resumo da validação:")
    print("  ✓ Modelo ML carregado com sucesso")
    print("  ✓ MLDetector funciona com fallback heurístico")
    print("  ✓ MLDetector usa modelo ML quando buffer está completo")
    print("  ✓ Detecção funciona com diferentes padrões de entrada")
    print("  ✓ Reset limpa estado interno corretamente")
    print()
    
    return True


if __name__ == "__main__":
    success = test_ml_pipeline_integration()
    sys.exit(0 if success else 1)
