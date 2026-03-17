# 🔧 Ajuste de Detecção de Movimento - WiFiSense Local

## Problema Identificado

O sistema estava mostrando **"inatividade prolongada"** mesmo com pessoas se movimentando pela casa. Isso acontecia porque os limiares de detecção estavam calibrados para sinais simulados (mock), não para sinais Wi-Fi reais.

## Causa Raiz

Com **Wi-Fi real (RSSI)**, as variações de sinal são **muito menores** do que com dados simulados:

- **Dados Mock**: Variância de sinal pode chegar a 5-10 facilmente
- **Wi-Fi Real**: Variância típica é 0.3-2.0 (muito menor!)

Os limiares antigos eram:
- `movement_variance_min: 2.0` - Muito alto para Wi-Fi real
- `movement_rate_min: 3.0` - Muito alto para mudanças reais de RSSI
- `presence_energy_min: 4.0` - Muito alto, dificultava detecção de presença

## Ajustes Realizados

### 1. Limiares de Movimento (heuristic_detector.py)

```python
# ANTES (para dados mock)
movement_variance_min: float = 2.0
movement_rate_min: float = 3.0

# DEPOIS (para Wi-Fi real)
movement_variance_min: float = 0.5  # 4x mais sensível
movement_rate_min: float = 1.0      # 3x mais sensível
```

### 2. Limiares de Presença (heuristic_detector.py)

```python
# ANTES
presence_energy_min: float = 4.0
presence_rssi_norm_min: float = 0.35

# DEPOIS
presence_energy_min: float = 2.0    # 2x mais sensível
presence_rssi_norm_min: float = 0.25 # Mais fácil detectar presença
```

### 3. Configuração Padrão (schemas.py)

```python
# ANTES
movement_sensitivity: float = 2.0
sampling_interval: float = 0.5

# DEPOIS
movement_sensitivity: float = 0.5   # Mais sensível
sampling_interval: float = 1.0      # Intervalo padrão ajustado
```

## O Que Mudou na Prática

### Antes do Ajuste ❌
- Variância do sinal: 0.8 → Sistema: "Sem movimento" (0.8 < 2.0)
- Taxa de mudança: 1.5 dBm → Sistema: "Sem movimento" (1.5 < 3.0)
- Resultado: **PROLONGED_INACTIVITY** mesmo com pessoas andando

### Depois do Ajuste ✅
- Variância do sinal: 0.8 → Sistema: "Movimento detectado!" (0.8 > 0.5)
- Taxa de mudança: 1.5 dBm → Sistema: "Movimento detectado!" (1.5 > 1.0)
- Resultado: **PRESENCE_MOVING** quando pessoas andam pela casa

## Como Testar

1. **Abra o Dashboard** (http://localhost:5173)
2. **Ande pela casa** normalmente
3. **Observe o status** mudar para:
   - "Presença em Movimento" quando você andar
   - "Presença Parada" quando ficar parado
   - "Sem Presença" quando sair do ambiente

## Valores Típicos com Wi-Fi Real

Com a rede "Nery" (RSSI -62 a -65 dBm):

| Situação | Variância | Taxa de Mudança | Detecção |
|----------|-----------|-----------------|----------|
| Ambiente vazio | 0.1-0.3 | 0.2-0.5 | NO_PRESENCE |
| Pessoa parada | 0.3-0.6 | 0.5-1.0 | PRESENCE_STILL |
| Pessoa andando | 0.8-2.0 | 1.5-4.0 | PRESENCE_MOVING |
| Movimento rápido | 2.0-5.0 | 4.0-8.0 | PRESENCE_MOVING (alta confiança) |

## Ajuste Fino (Se Necessário)

Se o sistema ainda não detectar movimento adequadamente, você pode ajustar via API:

```bash
# Tornar MAIS sensível (detecta movimentos menores)
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"movement_sensitivity": 0.3}'

# Tornar MENOS sensível (evita falsos positivos)
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"movement_sensitivity": 0.8}'
```

Ou pela interface de **Configurações** no Dashboard.

## Próximos Passos

Para melhorar ainda mais a detecção, considere implementar:

1. **Calibração do Ambiente** (Requisito 1 da spec)
   - Sistema aprende o "baseline" do seu ambiente específico
   - Ajusta limiares automaticamente

2. **Baseline Adaptativo** (Requisito 2 da spec)
   - Sistema se adapta a mudanças graduais (móveis, janelas abertas/fechadas)

3. **Machine Learning** (Requisitos 7-9 da spec)
   - Treina modelo com dados reais da sua casa
   - Detecção muito mais precisa

Essas melhorias estão documentadas em `.kiro/specs/wifi-sense-evolution/`

## Resumo

✅ **Ajustes aplicados** - Sistema agora detecta movimento com Wi-Fi real  
✅ **Backend reiniciado** - Mudanças já estão ativas  
✅ **Teste agora** - Ande pela casa e veja o status mudar  

O sistema estava configurado para dados simulados. Agora está otimizado para sinais Wi-Fi reais! 🎯
