# 🚨 Como Simular uma Queda para Testar

## 🎯 O Que o Sistema Detecta Como Queda

O sistema detecta queda quando:
1. **Taxa de mudança** do sinal RSSI ≥ 8 dB/s (mudança brusca)
2. **OU** Energia do sinal ≥ 20 (pico súbito)

---

## 🧪 Formas de Simular uma Queda

### Método 1: Movimento Brusco Próximo ao Roteador (Mais Fácil)

**Como fazer:**
1. Fique próximo ao roteador Wi-Fi (1-2 metros)
2. Faça um movimento RÁPIDO e BRUSCO:
   - Agache rapidamente
   - Ou pule
   - Ou corra em direção ao roteador
   - Ou afaste-se rapidamente

**Por quê funciona:**
- Movimento brusco causa mudança rápida no sinal
- Sistema detecta como possível queda

---

### Método 2: Aproximar/Afastar Rapidamente do Roteador

**Como fazer:**
1. Comece longe do roteador (3-4 metros)
2. Corra em direção ao roteador
3. Ou: Fique perto e corra para longe rapidamente

**Por quê funciona:**
- Mudança rápida de distância = mudança rápida de RSSI
- Sistema interpreta como queda

---

### Método 3: Obstruir o Sinal Rapidamente

**Como fazer:**
1. Coloque seu corpo entre o roteador e o computador
2. Movimente-se rapidamente para bloquear/desbloquear o sinal
3. Faça isso de forma brusca

**Por quê funciona:**
- Obstrução rápida causa pico de mudança
- Sistema detecta como anomalia (possível queda)

---

### Método 4: Simular Queda Real (Mais Realista)

**Como fazer:**
1. Fique em pé próximo ao roteador
2. Agache rapidamente (simulando queda)
3. Fique no chão por alguns segundos

**Por quê funciona:**
- Movimento vertical rápido
- Mudança de altura = mudança de propagação do sinal
- Sistema detecta padrão de queda

---

## 📱 O Que Você Vai Receber no Telegram

Quando o sistema detectar uma queda, você receberá:

```
🚨 ALERTA: Queda Detectada

📊 Confiança: 95%
🕐 Horário: 22:30:15

⚠️ Ação recomendada:
Verifique imediatamente o local

📋 Detalhes:
  • Taxa de mudança: 15.5 dB/s
```

---

## ⚙️ Ajustes Feitos para Facilitar Teste

Reduzi os limiares de detecção:
- **Taxa de mudança**: 12 → 8 dB/s (mais sensível)
- **Energia**: 25 → 20 (mais sensível)

Agora é mais fácil simular uma queda!

---

## 🎬 Passo a Passo para Testar AGORA

### 1. Certifique-se que o Sistema Está Rodando
```
Verifique se está vendo no terminal:
🟢 Presença parada | Confiança: 75% | RSSI: -65.0 dBm
```

### 2. Posicione-se Próximo ao Roteador
```
Distância ideal: 1-3 metros do roteador
```

### 3. Faça um Movimento Brusco
```
Opções:
- Agache rapidamente
- Pule
- Corra em direção ao roteador
- Afaste-se rapidamente
```

### 4. Aguarde o Alerta
```
Você deve receber no Telegram em 1-3 segundos:
🚨 ALERTA: Queda Detectada
```

---

## 🔍 Verificar se Funcionou

Execute este comando para ver se a queda foi detectada:

```bash
python verificar_eventos_e_alertas.py
```

Você deve ver:
```
Eventos detectados:
  - fall_suspected: 1

Alertas enviados:
  - fall_suspected: 1
```

---

## 💡 Dicas para Melhor Detecção

### ✅ Faça:
- Movimentos RÁPIDOS e BRUSCOS
- Fique PRÓXIMO ao roteador (1-3m)
- Movimentos VERTICAIS (agachar, pular)
- Mudanças SÚBITAS de posição

### ❌ Evite:
- Movimentos lentos e suaves
- Ficar muito longe do roteador (>5m)
- Movimentos horizontais lentos
- Mudanças graduais

---

## 🎯 Sensibilidade Atual

Com os ajustes feitos:

**Muito Sensível (Detecta facilmente):**
- ✅ Agachar rapidamente
- ✅ Pular
- ✅ Correr em direção ao roteador

**Moderadamente Sensível:**
- ⚠️ Andar rápido
- ⚠️ Movimentos bruscos de braço

**Pouco Sensível (Pode não detectar):**
- ❌ Andar devagar
- ❌ Movimentos suaves
- ❌ Ficar muito longe

---

## 🔧 Se Não Detectar

### Opção 1: Reduzir Ainda Mais os Limiares

Edite `backend/app/detection/heuristic_detector.py`:

```python
# Linha ~20
fall_rate_spike: float = 5.0  # Muito sensível
fall_energy_spike: float = 15.0  # Muito sensível
```

Depois reinicie o backend.

### Opção 2: Verificar Logs

```bash
# Ver últimos eventos
python verificar_eventos_e_alertas.py

# Ver taxa de mudança atual
# (deve ser > 8 para detectar queda)
```

---

## 📊 Entendendo os Valores

### Taxa de Mudança (rate_of_change)
```
< 1 dB/s  = Parado
1-3 dB/s  = Movimento lento
3-8 dB/s  = Movimento normal
> 8 dB/s  = Movimento brusco (QUEDA!)
```

### Energia do Sinal
```
< 5       = Sem presença
5-15      = Presença normal
15-20     = Movimento
> 20      = Movimento brusco (QUEDA!)
```

---

## 🎉 Teste Agora!

1. ✅ Sistema rodando
2. ✅ Alertas de queda ativados
3. ✅ Limiares ajustados
4. ✅ Telegram configurado

**Faça um movimento brusco próximo ao roteador e veja o alerta chegar!** 🚨

---

## 📱 Exemplo Real

```
Você: *agacha rapidamente*
Sistema: Detecta mudança de 10 dB/s
Sistema: "Queda detectada!"
Telegram: 🚨 ALERTA: Queda Detectada
Você: Recebe notificação em 2 segundos
```

**Pronto para testar!** 🚀
