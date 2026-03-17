# Task 2.5: Baseline Adaptativo - Implementação Completa

## Resumo

Implementação do baseline adaptativo com EMA (Exponential Moving Average), detecção de mudanças abruptas e logging de atualizações significativas.

## Requisitos Implementados

### Requisito 2.1: Baseline Adaptativo Contínuo
✅ Sistema mantém baseline adaptativo que se atualiza continuamente

### Requisito 2.2: Atualização Gradual
✅ WHEN não há presença por >5 minutos, SHALL incorporar gradualmente novos valores ao baseline

### Requisito 2.3: Taxa de Aprendizado Configurável
✅ SHALL usar taxa de aprendizado configurável (padrão: 0.01)

### Requisito 2.4: Detecção de Mudanças Abruptas
✅ IF mudança abrupta no sinal (>30% em <1 minuto), THEN SHALL não atualizar baseline automaticamente

### Requisito 2.5: Logging de Atualizações Significativas
✅ SHALL registrar no log cada atualização significativa (>10% de mudança)

## Implementação

### Arquivo Modificado
- `backend/app/services/calibration_service.py`

### Método Implementado: `update_baseline_adaptive()`

```python
def update_baseline_adaptive(
    self, features: ProcessedFeatures, no_presence_duration: float
) -> None:
    """
    Atualiza baseline adaptativamente.

    Usa média móvel exponencial (EMA) para atualizar baseline gradualmente
    quando não há presença detectada por tempo suficiente.

    Implementa:
    - Atualização gradual com EMA (taxa configurável)
    - Detecção de mudanças abruptas (>30%)
    - Logging de atualizações significativas (>10%)

    Args:
        features: Features processadas do sinal atual
        no_presence_duration: Duração em segundos sem presença detectada
    """
```

### Funcionalidades Implementadas

#### 1. Atualização Gradual com EMA
- Usa média móvel exponencial para atualização suave
- Taxa de aprendizado configurável (padrão: 0.01)
- Fórmula: `novo_valor = (1 - taxa) * valor_antigo + taxa * valor_novo`

#### 2. Detecção de Mudanças Abruptas
- Calcula mudança percentual para RSSI e variância
- Se mudança >30%, não atualiza baseline
- Registra warning no log quando mudança abrupta é detectada

#### 3. Logging de Atualizações Significativas
- Calcula mudança total após atualização
- Se mudança >10%, registra log INFO com detalhes
- Inclui valores antigos e novos, e percentual de mudança

#### 4. Proteção Contra Divisão por Zero
- Verifica se valores base são zero antes de calcular percentuais
- Retorna 0% de mudança se valor base for zero

## Testes

### Arquivo de Testes
- `backend/test_task2_5_baseline_adaptive.py`

### Testes Implementados (8 testes, todos passando)

1. **test_baseline_adaptive_not_updated_before_5_minutes**
   - Verifica que baseline não é atualizado antes de 5 minutos sem presença

2. **test_baseline_adaptive_updated_after_5_minutes**
   - Verifica que baseline é atualizado após 5 minutos sem presença
   - Valida cálculo EMA correto

3. **test_baseline_adaptive_not_updated_on_abrupt_rssi_change**
   - Verifica que mudança abrupta de RSSI (>30%) não atualiza baseline
   - Valida logging de warning

4. **test_baseline_adaptive_not_updated_on_abrupt_variance_change**
   - Verifica que mudança abrupta de variância (>30%) não atualiza baseline
   - Valida logging de warning

5. **test_baseline_adaptive_logs_significant_update**
   - Verifica que atualizações significativas (>10%) são logadas
   - Valida conteúdo do log

6. **test_baseline_adaptive_ema_calculation**
   - Verifica que cálculo de EMA está correto
   - Valida fórmula matemática

7. **test_baseline_adaptive_no_baseline_set**
   - Verifica que não há erro quando baseline não está definido

8. **test_baseline_adaptive_zero_division_protection**
   - Verifica proteção contra divisão por zero

### Execução dos Testes

```bash
cd backend
python -m pytest test_task2_5_baseline_adaptive.py -v
```

**Resultado:** ✅ 8 passed in 0.83s

## Exemplo de Uso

```python
from app.services.calibration_service import CalibrationService
from app.processing.signal_processor import ProcessedFeatures

# Criar serviço de calibração
calibration_service = CalibrationService(provider=my_provider)

# Definir baseline inicial
baseline = await calibration_service.start_calibration(duration_seconds=60)

# Durante monitoramento, atualizar baseline adaptativamente
# quando não há presença por mais de 5 minutos
features = processor.process(signal)
no_presence_duration = 360  # 6 minutos

calibration_service.update_baseline_adaptive(features, no_presence_duration)
```

## Logs Gerados

### Mudança Abrupta Detectada
```
WARNING - Mudança abrupta detectada - baseline não atualizado. RSSI: 40.0%, Variância: 50.0%
```

### Atualização Significativa
```
INFO - Baseline atualizado significativamente. RSSI: -50.00 → -55.00 (10.0%), Variância: 1.00 → 1.25 (25.0%)
```

## Integração com Sistema

O método `update_baseline_adaptive()` deve ser chamado pelo `MonitorService` durante o loop de monitoramento:

1. Detectar eventos de presença
2. Calcular duração sem presença
3. Se duração >5 minutos, chamar `update_baseline_adaptive()`
4. Sistema automaticamente:
   - Verifica mudanças abruptas
   - Atualiza baseline gradualmente com EMA
   - Registra atualizações significativas

## Próximos Passos

- [ ] Integrar com MonitorService
- [ ] Adicionar endpoint REST para visualizar baseline atual
- [ ] Adicionar WebSocket para notificar frontend sobre atualizações de baseline
- [ ] Implementar testes de propriedade (Task 2.6)

## Referências

- Requisitos: `.kiro/specs/wifi-sense-evolution/requirements.md` (Requisito 2)
- Design: `.kiro/specs/wifi-sense-evolution/design.md` (CalibrationService)
- Tasks: `.kiro/specs/wifi-sense-evolution/tasks.md` (Task 2.5)
