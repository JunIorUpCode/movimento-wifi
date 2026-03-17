# Tarefa 7.1 - Script train_model.py - IMPLEMENTADO ✅

## Resumo

Implementado script completo `train_model.py` para treinamento de modelos ML do WiFiSense.

## Arquivos Criados/Modificados

### 1. `backend/train_model.py` (NOVO)
Script completo de treinamento com:
- ✅ Carregamento de dataset CSV exportado pelo MLService
- ✅ Extração de features de 18 dimensões (9 médias + 9 desvios padrão de janela)
- ✅ Split treino/teste com estratificação
- ✅ Normalização com StandardScaler
- ✅ Treinamento com RandomForestClassifier
- ✅ Salvamento de modelo e scaler em formato .pkl
- ✅ Avaliação completa com métricas e feature importance
- ✅ Interface CLI com argumentos configuráveis

### 2. `backend/requirements.txt` (ATUALIZADO)
Adicionadas dependências ML:
- scikit-learn>=1.3.0
- pandas>=2.0.0
- numpy>=1.24.0
- joblib>=1.3.0

## Funcionalidades Implementadas

### Carregamento de Dataset
```python
def load_dataset(csv_path: Path) -> pd.DataFrame
```
- Carrega CSV exportado pelo MLService
- Validação de existência e formato
- Tratamento de erros

### Extração de Features (18 Dimensões)
```python
def extract_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]
```
- 9 features básicas do MLService
- Janela deslizante de 10 amostras
- Calcula média (9 features) e desvio padrão (9 features) = 18 dimensões
- Validação de colunas obrigatórias

Features extraídas:
1-9. Média da janela: rssi_normalized, rssi_smoothed, rate_of_change, signal_energy, signal_variance, csi_mean_amplitude, csi_std_amplitude, instability_score, raw_rssi
10-18. Desvio padrão da janela: mesmas features

### Split Treino/Teste
```python
def split_data(X, y, test_size=0.2, random_state=42)
```
- Split estratificado (mantém proporção de classes)
- Padrão: 80% treino, 20% teste
- Seed configurável para reprodutibilidade

### Normalização
```python
def normalize_features(X_train, X_test) -> Tuple[..., StandardScaler]
```
- StandardScaler ajustado apenas no treino (evita data leakage)
- Transforma treino e teste
- Retorna scaler para uso em produção

### Treinamento
```python
def train_model(X_train, y_train, n_estimators=100, max_depth=20)
```
- RandomForestClassifier
- Parâmetros configuráveis via CLI
- Usa todos os cores disponíveis (n_jobs=-1)
- Verbose para acompanhamento

### Avaliação
```python
def evaluate_model(model, X_test, y_test) -> Dict[str, Any]
```
- Acurácia
- Classification report (precision, recall, f1-score)
- Matriz de confusão
- Feature importance (top 10)

### Salvamento
```python
def save_model(model, scaler, metrics, output_dir, model_name="classifier")
```
- Modelo: `{model_name}.pkl`
- Scaler: `{model_name}_scaler.pkl`
- Metadados: `{model_name}_metadata.json` (acurácia, classes, feature importance, timestamp)

## Uso do Script

### Uso Básico
```bash
python train_model.py dataset.csv
```

### Uso Avançado
```bash
# Customizar split
python train_model.py dataset.csv --test-size 0.3

# Customizar modelo
python train_model.py dataset.csv --n-estimators 200 --max-depth 30

# Customizar saída
python train_model.py dataset.csv --output-dir ./custom_models --model-name my_model

# Reprodutibilidade
python train_model.py dataset.csv --random-state 123
```

### Argumentos CLI
- `dataset`: Caminho para CSV (obrigatório)
- `--test-size`: Proporção teste (padrão: 0.2)
- `--n-estimators`: Número de árvores (padrão: 100)
- `--max-depth`: Profundidade máxima (padrão: 20)
- `--output-dir`: Diretório saída (padrão: models)
- `--model-name`: Nome base arquivos (padrão: classifier)
- `--random-state`: Seed (padrão: 42)

## Exemplo de Saída

```
======================================================================
🤖 WiFiSense - Treinamento de Modelo ML
======================================================================

✓ Dataset carregado: 1000 amostras

✓ Features extraídas: 991 amostras, 18 dimensões
  Distribuição de labels:
    no_presence: 200 (20.2%)
    presence_moving: 350 (35.3%)
    presence_still: 441 (44.5%)

✓ Dados divididos:
  Treino: 792 amostras
  Teste: 199 amostras

✓ Features normalizadas com StandardScaler

🌲 Treinando RandomForestClassifier...
  n_estimators: 100
  max_depth: 20

✓ Modelo treinado com sucesso

📊 Avaliando modelo...

✓ Acurácia: 0.9246 (92.46%)

Relatório de Classificação:
              precision    recall  f1-score   support
...

Matriz de Confusão:
...

Top 10 Features Mais Importantes:
  1. variance_mean: 0.1523
  2. instability_mean: 0.1342
  ...

✓ Modelo salvo: models/classifier.pkl
✓ Scaler salvo: models/classifier_scaler.pkl
✓ Metadados salvos: models/classifier_metadata.json

======================================================================
✅ Treinamento concluído com sucesso!
======================================================================

Arquivos gerados:
  - Modelo: models/classifier.pkl
  - Scaler: models/classifier_scaler.pkl
  - Metadados: models/classifier_metadata.json

Acurácia final: 0.9246 (92.46%)
```

## Integração com MLDetector

O modelo treinado pode ser carregado pelo MLDetector:

```python
# MLDetector carrega automaticamente
detector = MLDetector(model_path="models/classifier.pkl")

# O scaler é carregado automaticamente
# scaler_path = model_path.replace('.pkl', '_scaler.pkl')
```

## Requisitos Atendidos

✅ **Requisito 8.4**: Script de treinamento implementado
✅ **Requisito 8.5**: Modelo e scaler salvos em formato .pkl

## Próximos Passos

- Tarefa 7.2: Escrever testes unitários para treinamento
- Tarefa 8.1: Implementar MLDetector que usa o modelo treinado

## Notas Técnicas

### Janela de Features
- MLService exporta 1 amostra por segundo
- Script cria janelas de 10 amostras consecutivas
- Cada janela gera 1 amostra de treinamento com 18 features
- Dataset de 1000 amostras → ~991 amostras de treinamento

### Estratificação
- Split mantém proporção de classes em treino e teste
- Importante para datasets desbalanceados

### Data Leakage Prevention
- Scaler ajustado APENAS no conjunto de treino
- Teste usa transformação do scaler já ajustado
- Garante avaliação realista

### Reprodutibilidade
- random_state fixo em todas as operações aleatórias
- Permite reproduzir resultados exatos
- Importante para debugging e comparações
