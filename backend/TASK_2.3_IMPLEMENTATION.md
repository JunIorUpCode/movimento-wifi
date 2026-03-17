# Task 2.3 - Implementação de Persistência de Baseline

## Resumo

Implementação dos métodos `save_baseline()` e `load_baseline()` no `CalibrationService` para persistir baselines de calibração no banco de dados SQLite.

## Métodos Implementados

### `save_baseline(profile_name: str) -> None`

Salva o baseline atual no banco de dados usando o modelo `CalibrationProfile`.

**Funcionalidades:**
- Serializa o `BaselineData` para JSON
- Cria novo perfil se não existir
- Atualiza perfil existente se já houver um com o mesmo nome
- Atualiza o campo `updated_at` em atualizações

**Validações:**
- Levanta `ValueError` se não houver baseline calculado

### `load_baseline(profile_name: str) -> BaselineData`

Carrega um baseline do banco de dados e o define como baseline ativo no serviço.

**Funcionalidades:**
- Busca perfil por nome no banco
- Deserializa JSON para `BaselineData`
- Define o baseline carregado como baseline ativo do serviço
- Retorna o `BaselineData` carregado

**Validações:**
- Levanta `ValueError` se o perfil não for encontrado

## Estrutura de Dados

O baseline é salvo como JSON no campo `baseline_json` do modelo `CalibrationProfile`:

```json
{
  "mean_rssi": -75.0,
  "std_rssi": 2.5,
  "mean_variance": 1.8,
  "std_variance": 0.5,
  "noise_floor": -78.0,
  "samples_count": 60,
  "timestamp": 1234567890.0,
  "profile_name": "default"
}
```

## Casos de Uso

### 1. Salvar Baseline Após Calibração

```python
service = CalibrationService(provider)
baseline = await service.start_calibration(duration_seconds=60)
await service.save_baseline("perfil_dia")
```

### 2. Carregar Baseline Salvo

```python
service = CalibrationService(provider)
baseline = await service.load_baseline("perfil_dia")
# baseline agora está ativo no serviço
```

### 3. Múltiplos Perfis

```python
# Criar perfis para diferentes condições
await service.start_calibration(60, "dia")
await service.save_baseline("perfil_dia")

await service.start_calibration(60, "noite")
await service.save_baseline("perfil_noite")

# Alternar entre perfis
await service.load_baseline("perfil_dia")
# ou
await service.load_baseline("perfil_noite")
```

## Testes

Todos os testes em `test_task2_3_persistence.py` passaram com sucesso:

✓ Teste 1: Salvar Baseline
✓ Teste 2: Carregar Baseline
✓ Teste 3: Atualizar Perfil Existente
✓ Teste 4: Carregar Perfil Inexistente (validação de erro)
✓ Teste 5: Salvar Sem Baseline (validação de erro)
✓ Teste 6: Múltiplos Perfis

## Requisitos Atendidos

- **Requisito 1.4**: Sistema persiste dados de calibração no banco de dados
- **Design**: Implementação conforme especificado no documento de design técnico
- **Task 2.3**: Métodos `save_baseline()` e `load_baseline()` implementados e testados

## Arquivos Modificados

- `backend/app/services/calibration_service.py`: Adicionados métodos de persistência
- `backend/test_task2_3_persistence.py`: Testes completos de persistência (novo)
- `backend/TASK_2.3_IMPLEMENTATION.md`: Documentação (novo)
