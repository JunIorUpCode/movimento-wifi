# 🔍 Diagnóstico: Por Que a Queda Não Foi Detectada

## 📊 Execute Este Comando:

```bash
python monitorar_valores_tempo_real.py
```

Este script mostra os valores em tempo real enquanto você se movimenta.

---

## 🎯 O Que Você Vai Ver:

```
🟢 Taxa: 2.50 dB/s (max: 5.30) | 🟢 Energia: 12.50 (max: 15.20) | Var: 1.20 | presence_moving
```

**Legenda:**
- **Taxa**: Taxa de mudança do sinal (precisa > 8.0 para queda)
- **Energia**: Energia do sinal (precisa > 20.0 para queda)
- **Var**: Variância (indica movimento)
- **max**: Valor máximo detectado até agora

---

## 🚨 Quando Detecta Queda:

Você verá:
```
🔴 QUEDA! Taxa: 10.50 dB/s (max: 10.50) | 🟢 Energia: 15.20 (max: 15.20) | Var: 3.50 | fall_suspected
```

---

## 💡 Como Usar:

### 1. Execute o script:
```bash
python monitorar_valores_tempo_real.py
```

### 2. Faça movimentos e observe:
- Ande devagar → Taxa: 1-3 dB/s
- Ande rápido → Taxa: 3-6 dB/s
- Movimento brusco → Taxa: 6-10 dB/s
- **Queda simulada → Taxa: > 8 dB/s** ✅

### 3. Quando terminar, pressione Ctrl+C

Você verá um resumo:
```
RESUMO
======
Máxima taxa de mudança detectada: 5.30 dB/s
Máxima energia detectada: 15.20

⚠️  PROBLEMA: Valores não atingiram limiares de queda!

Soluções:
1. Faça movimentos MAIS BRUSCOS
2. Fique MAIS PRÓXIMO do roteador
3. Ou reduza os limiares:
   - Taxa: 8.0 → 4.2 dB/s
   - Energia: 20.0 → 12.2
```

---

## 🔧 Soluções

### Solução 1: Movimentos Mais Bruscos

**Tente:**
- Pular próximo ao roteador
- Agachar MUITO rápido
- Correr em direção ao roteador
- Movimento de "queda" real (joelhos no chão)

### Solução 2: Ficar Mais Próximo

**Distância ideal:**
- 0.5 - 2 metros do roteador
- Quanto mais perto, melhor

### Solução 3: Reduzir Limiares (Se Necessário)

Se mesmo com movimentos bruscos não detectar, edite:

**Arquivo:** `backend/app/detection/heuristic_detector.py`

**Linha ~20:**
```python
# Valores atuais
fall_rate_spike: float = 8.0
fall_energy_spike: float = 20.0

# Reduza para (baseado no seu máximo):
fall_rate_spike: float = 5.0  # Mais sensível
fall_energy_spike: float = 15.0  # Mais sensível
```

Depois reinicie o backend.

---

## 📈 Valores Típicos

### Ambiente Normal:
```
Parado:           Taxa: 0-1 dB/s,   Energia: 5-10
Andando devagar:  Taxa: 1-3 dB/s,   Energia: 8-15
Andando rápido:   Taxa: 3-6 dB/s,   Energia: 12-18
Movimento brusco: Taxa: 6-10 dB/s,  Energia: 15-25
Queda real:       Taxa: 10-20 dB/s, Energia: 20-40
```

### Seu Ambiente (Exemplo):
```
Execute o script e anote seus valores:

Parado:           Taxa: ___ dB/s,   Energia: ___
Andando:          Taxa: ___ dB/s,   Energia: ___
Movimento brusco: Taxa: ___ dB/s,   Energia: ___
Máximo atingido:  Taxa: ___ dB/s,   Energia: ___
```

---

## 🎯 Próximos Passos

1. **Execute o script de monitoramento**
2. **Faça movimentos e anote os valores máximos**
3. **Se não atingir 8.0 dB/s:**
   - Tente movimentos mais bruscos
   - Ou reduza os limiares para seus valores máximos

4. **Teste novamente**
5. **Quando detectar, você receberá no Telegram!**

---

## 📱 Mensagem Esperada no Telegram:

```
🚨 ALERTA: Queda Detectada

📊 Confiança: 95%
🕐 Horário: 22:50:15

⚠️ Ação recomendada:
Verifique imediatamente o local

📋 Detalhes:
  • Taxa de mudança: 10.5 dB/s
```

---

**Execute o script agora e veja os valores em tempo real!** 🔍
