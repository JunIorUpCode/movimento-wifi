# Implementação da Tarefa 8.1 - MLDetector

## Resumo

Implementação completa do MLDetector, um detector baseado em Machine Learning que herda de DetectorBase e usa modelos RandomForestClassifier treinados para classificar eventos de presença e movimento.

## Arquivos Criados

### 1. `backend/app/detection/ml_detector.py`
Classe principal MLDetector com:
- Herança de DetectorBase
- Carregamento de modelo e scaler (.pkl)
- Buffer de 10 segundos para features de janela
- Extração de 18 features (9 médias + 9 desvios padrão)
- Fallback automático para HeuristicDetector
- Logging de confiança do modelo

### 2. `backend/test_task8_1_ml_detector.py`
Suite completa de testes com 17 casos:
- Testes de inicialização (com/sem modelo)
- Testes de detecção (fallback, ML, buffer)
- Testes de extração de features
- Testes de mapeamento de classes
- Testes de reset e informações do modelo
- Teste de integração completo

## Funcionalidades Implementadas

### Inicialização
- Carrega modelo e scaler do diretório models/
- Fallback automático para HeuristicDetector se modelo não existir
- Validação de arquivos .pkl e _scaler.pkl

### Detecção
- Buffer de 10 segundos (deque com maxlen=10)
- Usa fallback se buffer < 10 amostras
- Extrai 18 features de janela quando buffer completo
- Normaliza features com StandardScaler
- Predição com predict_proba do modelo
- Retorna DetectionResult com confiança e probabilidades

### Extração de Features (18 dimensões)
9 features básicas (média da janela):
1. rssi_normalized
2. rssi_smoothed
3. rate_of_change
4. signal_energy
5. signal_variance
6. csi_mean_amplitude
7. csi_std_amplitude
8. instability_score
9. raw_rssi

9 features de variabilidade (desvio padrão da janela):
10-18. Desvio padrão de cada feature básica


### Fallback Heurístico
- Usa HeuristicDetector quando:
  - Modelo não está carregado
  - Buffer tem < 10 amostras
  - Erro durante predição ML
- Configuração customizável via ThresholdConfig

### Logging
- Logging de carregamento de modelo
- Logging de confiança em cada predição
- Logging de erros e fallback

### Mapeamento de Classes
- Converte classes do modelo para EventType
- Suporta 5 tipos de eventos:
  - no_presence
  - presence_still
  - presence_moving
  - fall_suspected
  - prolonged_inactivity

## Requisitos Atendidos

✅ **Requisito 8.1**: Implementar MLDetector herdando de DetectorBase
✅ **Requisito 8.2**: Carregar modelo treinado do diretório models/
✅ **Requisito 8.3**: Usar modelo para classificação ao invés de heurísticas
✅ **Requisito 8.4**: Extrair features de janela de 10 segundos
✅ **Requisito 8.6**: Fallback automático para HeuristicDetector
✅ **Requisito 8.7**: Logging de confiança do modelo

## Testes

Todos os 17 testes passando:
```
backend/test_task8_1_ml_detector.py::test_ml_detector_init_without_model PASSED
backend/test_task8_1_ml_detector.py::test_ml_detector_init_with_model PASSED
backend/test_task8_1_ml_detector.py::test_ml_detector_init_with_custom_fallback_config PASSED
backend/test_task8_1_ml_detector.py::test_detect_uses_fallback_when_model_not_loaded PASSED
backend/test_task8_1_ml_detector.py::test_detect_uses_fallback_when_buffer_incomplete PASSED
backend/test_task8_1_ml_detector.py::test_detect_uses_ml_when_buffer_complete PASSED
backend/test_task8_1_ml_detector.py::test_detect_returns_correct_event_type PASSED
backend/test_task8_1_ml_detector.py::test_detect_includes_all_probabilities PASSED
backend/test_task8_1_ml_detector.py::test_extract_window_features_returns_18_dimensions PASSED
backend/test_task8_1_ml_detector.py::test_extract_window_features_calculates_statistics_correctly PASSED
backend/test_task8_1_ml_detector.py::test_fallback_on_prediction_error PASSED
backend/test_task8_1_ml_detector.py::test_reset_clears_buffer PASSED
backend/test_task8_1_ml_detector.py::test_class_to_event_mapping PASSED
backend/test_task8_1_ml_detector.py::test_class_to_event_unknown_class PASSED
backend/test_task8_1_ml_detector.py::test_get_model_info_when_not_loaded PASSED
backend/test_task8_1_ml_detector.py::test_get_model_info_when_loaded PASSED
backend/test_task8_1_ml_detector.py::test_integration_full_detection_cycle PASSED

17 passed in 8.31s
```

## Uso

### Exemplo Básico
```python
from app.detection.ml_detector import MLDetector
from app.processing.signal_processor import ProcessedFeatures

# Inicializa detector (fallback automático se modelo não existir)
detector = MLDetector(model_path="models/classifier.pkl")

# Verifica se modelo está carregado
if detector.is_model_loaded():
    print("Modelo ML carregado com sucesso")
else:
    print("Usando HeuristicDetector como fallback")

# Detecta eventos
for signal in signal_stream:
    features = processor.process(signal)
    result = detector.detect(features)
    
    print(f"Evento: {result.event_type.value}")
    print(f"Confiança: {result.confidence:.2f}")
    
    if result.details.get("model") == "ml":
        print(f"Probabilidades: {result.details['probabilities']}")
```

### Exemplo com Configuração Customizada
```python
from app.detection.ml_detector import MLDetector
from app.detection.heuristic_detector import ThresholdConfig

# Configuração customizada para fallback
fallback_config = ThresholdConfig(
    presence_energy_min=3.0,
    movement_variance_min=1.0,
    fall_rate_spike=15.0
)

detector = MLDetector(
    model_path="models/classifier.pkl",
    fallback_config=fallback_config
)
```

## Integração com Sistema

O MLDetector pode ser usado diretamente no MonitorService substituindo o HeuristicDetector:

```python
# Em monitor_service.py
from app.detection.ml_detector import MLDetector

class MonitorService:
    def __init__(self):
        # Usa MLDetector com fallback automático
        self._detector = MLDetector(model_path="models/classifier.pkl")
```

## Próximos Passos

1. Treinar modelo com dados reais usando `train_model.py`
2. Integrar MLDetector no MonitorService
3. Implementar coleta de dados para retreinamento
4. Adicionar métricas de performance do modelo
5. Implementar versionamento de modelos

## Dependências

- joblib >= 1.3.0 (para carregar modelos .pkl)
- scikit-learn >= 1.3.0 (para RandomForestClassifier)
- numpy >= 1.24.0 (para operações numéricas)

## Notas Técnicas

- O buffer de 10 segundos é implementado com `deque(maxlen=10)`
- Features são extraídas calculando média e desvio padrão da janela
- O scaler deve estar no mesmo diretório com sufixo `_scaler.pkl`
- Fallback é transparente e automático
- Logging usa o módulo logging padrão do Python

## Status

✅ **Implementação Completa**
✅ **Testes Passando (17/17)**
✅ **Documentação Completa**
✅ **Pronto para Integração**
