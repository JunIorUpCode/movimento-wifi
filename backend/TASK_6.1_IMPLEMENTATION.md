# Tarefa 6.1 - MLService: Estrutura Básica

## Resumo

Implementação completa do **MLService** para coleta de dados rotulados e preparação de datasets para treinamento de modelos de Machine Learning.

## Arquivos Criados

### 1. `backend/app/services/ml_service.py`
Serviço principal de Machine Learning com as seguintes funcionalidades:

#### Classe `LabeledSample`
Dataclass que representa uma amostra rotulada contendo:
- **Features RSSI**: `rssi_normalized`, `rssi_smoothed`, `rate_of_change`
- **Features de sinal**: `signal_energy`, `signal_variance`, `csi_mean_amplitude`, `csi_std_amplitude`
- **Features temporais**: `instability_score`
- **Metadados**: `timestamp`, `raw_rssi`, `label`, `system_config`, `environmental_conditions`

#### Classe `MLService`
Serviço singleton com os seguintes métodos:

**1. `start_data_collection()`** ✅ Requisito 7.1
- Ativa modo de coleta de dados
- Limpa buffers anteriores
- Prepara sistema para receber features

**2. `label_event(label, window_seconds, system_config, environmental_conditions)`** ✅ Requisito 7.2
- Rotula eventos em tempo real
- Associa rótulo aos últimos N segundos de features
- Valida rótulos (no_presence, presence_still, presence_moving, fall_suspected, prolonged_inactivity)
- Inclui metadados de configuração e condições ambientais ✅ Requisito 7.5

**3. `export_dataset(filename, include_metadata)`** ✅ Requisito 7.3
- Exporta dataset em formato CSV
- Compatível com scikit-learn e PyTorch
- Opção de incluir/excluir metadados
- Adiciona extensão .csv automaticamente

**Métodos Auxiliares:**
- `add_features()`: Adiciona features ao buffer circular
- `stop_data_collection()`: Para coleta mantendo amostras
- `get_label_distribution()`: Retorna distribuição de rótulos
- `clear_samples()`: Limpa todas as amostras
- `get_collection_stats()`: Retorna estatísticas da coleta

**Características Técnicas:**
- Buffer circular de 10 segundos para features pendentes
- Singleton pattern para instância global
- Logging estruturado de todas as operações
- Validação de rótulos
- Serialização JSON de metadados

### 2. `backend/test_task6_1_ml_service.py`
Suite completa de testes unitários com 23 testes organizados em 4 classes:

#### `TestMLServiceBasicFunctionality` (5 testes)
- Inicialização do serviço
- Ativação/desativação da coleta
- Adição de features

#### `TestLabelEvent` (7 testes)
- Rotulação básica de eventos
- Rotulação com metadados
- Validação de rótulos inválidos
- Janelas maiores que buffer
- Múltiplos eventos

#### `TestExportDataset` (6 testes)
- Exportação básica
- Conteúdo do CSV
- Exportação com/sem metadados
- Validação de extensão .csv
- Tratamento de erros

#### `TestUtilityMethods` (3 testes)
- Distribuição de rótulos
- Limpeza de amostras
- Estatísticas de coleta

#### `TestBufferManagement` (2 testes)
- Limite do buffer circular
- Comportamento FIFO

**Resultado:** ✅ **23/23 testes passando**

### 3. Atualização de `backend/app/services/__init__.py`
- Exportação de `MLService`, `LabeledSample` e `ml_service`
- Integração com módulo de serviços

## Requisitos Atendidos

✅ **Requisito 7.1**: Sistema de coleta de dados para ML
- Modo de coleta ativável via `start_data_collection()`
- Salva features extraídas em buffer

✅ **Requisito 7.2**: Rotulação em tempo real
- Método `label_event()` para rotular eventos
- Associa rótulo aos últimos N segundos
- Validação de rótulos

✅ **Requisito 7.3**: Exportação de datasets
- Método `export_dataset()` gera CSV
- Formato compatível com scikit-learn/PyTorch

✅ **Requisito 7.5**: Metadados
- Timestamp em cada amostra
- Configuração do sistema
- Condições ambientais
- Serialização JSON

## Estrutura do CSV Exportado

### Colunas Principais
```
timestamp, rssi_normalized, rssi_smoothed, rate_of_change,
signal_energy, signal_variance, csi_mean_amplitude, csi_std_amplitude,
instability_score, raw_rssi, label
```

### Colunas de Metadados (opcional)
```
system_config, environmental_conditions
```

## Exemplo de Uso

```python
from app.services.ml_service import ml_service
from app.processing.signal_processor import ProcessedFeatures

# 1. Iniciar coleta
ml_service.start_data_collection()

# 2. Adicionar features durante monitoramento
for signal in signals:
    features = processor.process(signal)
    ml_service.add_features(features)

# 3. Rotular evento quando ocorrer
ml_service.label_event(
    label="presence_moving",
    window_seconds=10,
    system_config={"sensitivity": 2.0},
    environmental_conditions={"temperature": 22.5}
)

# 4. Exportar dataset
output_path = await ml_service.export_dataset(
    "training_data.csv",
    include_metadata=True
)

# 5. Ver estatísticas
stats = ml_service.get_collection_stats()
print(f"Total samples: {stats['total_samples']}")
print(f"Label distribution: {stats['label_distribution']}")
```

## Integração com Sistema Existente

O MLService está pronto para integração com:
- **SignalProcessor**: Recebe `ProcessedFeatures` diretamente
- **MonitorService**: Pode ser chamado durante pipeline de monitoramento
- **API REST**: Endpoints podem ser criados para controlar coleta
- **Frontend**: Interface pode exibir status de coleta e estatísticas

## Próximos Passos (Tarefas Futuras)

1. **Tarefa 6.2**: Criar endpoints REST para controle do MLService
2. **Tarefa 6.3**: Implementar interface no frontend para rotulação
3. **Tarefa 6.4**: Script de treinamento de modelos
4. **Tarefa 6.5**: Implementar MLDetector que usa modelos treinados

## Notas Técnicas

- **Singleton Pattern**: Garante única instância do serviço
- **Buffer Circular**: Mantém últimos 10 segundos de features
- **Logging Estruturado**: Todas as operações são logadas
- **Type Hints**: Código totalmente tipado
- **Async Support**: Método `export_dataset()` é assíncrono
- **Validação**: Rótulos são validados antes de aceitar

## Conclusão

A Tarefa 6.1 foi implementada com sucesso, fornecendo uma base sólida para o sistema de Machine Learning do WiFiSense. O MLService permite coleta eficiente de dados rotulados, essencial para treinar modelos de detecção inteligentes que superarão as limitações das regras heurísticas atuais.
