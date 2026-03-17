# 🧪 Como Testar o Sistema REAL

## 📋 O Que Este Teste Faz

Este teste usa o sistema COMPLETO:
- ✅ Captura sinais Wi-Fi REAIS do seu ambiente
- ✅ Processa e detecta eventos (movimento, queda, inatividade)
- ✅ Envia alertas REAIS para seu Telegram
- ✅ Você pode simular eventos movimentando-se no ambiente

---

## 🚀 Passo a Passo

### 1. Certifique-se que o Backend está Rodando

```bash
cd backend
uvicorn app.main:app --reload
```

Deve aparecer:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Execute o Script de Inicialização

Em outro terminal:

```bash
cd backend
python iniciar_sistema_completo.py
```

### 3. O Que Vai Acontecer

O script vai:

1. **Configurar o Telegram** com suas credenciais
2. **Enviar mensagem de teste** (você receberá no Telegram)
3. **Iniciar monitoramento** de Wi-Fi
4. **Mostrar status em tempo real** na tela

Você verá algo assim:
```
🟢 Presença parada | Confiança: 75% | RSSI: -45.3 dBm
```

### 4. Como Testar Detecções

#### 🚶 Testar Movimento
- Ande pelo ambiente
- Movimente-se próximo ao roteador
- Sistema detectará: `🔵 Movimento`

#### 🛋️ Testar Inatividade
- Fique parado por 30 segundos
- Sistema detectará: `🟡 Inatividade`
- Se ficar muito tempo, receberá alerta no Telegram

#### 🚨 Testar Queda (Simulação)
- Movimento brusco próximo ao roteador
- Ou afaste-se rapidamente
- Sistema pode detectar: `🔴 QUEDA SUSPEITA`
- Você receberá alerta IMEDIATO no Telegram

---

## 📱 Tipos de Alertas que Você Receberá

### 1. Queda Suspeita (Confiança ≥ 70%)
```
🚨 ALERTA: Queda suspeita
⏰ 14/03/2026 18:30:45
📊 Confiança: 95%
📝 Detalhes: Taxa de mudança: 15.5 dB/s
```

### 2. Inatividade Prolongada (Confiança ≥ 70%)
```
⏰ ALERTA: Inatividade prolongada
⏰ 14/03/2026 18:30:45
📊 Confiança: 85%
📝 Detalhes: Sem movimento há 30 minutos
```

### 3. Movimento (Confiança ≥ 70%)
```
🚶 ALERTA: Movimento detectado
⏰ 14/03/2026 18:30:45
📊 Confiança: 75%
📝 Detalhes: Variância: 3.5
```

---

## ⚙️ Configurações Atuais

- **Confiança mínima**: 70% (só envia alerta se confiança ≥ 70%)
- **Cooldown**: 60 segundos (1 minuto entre alertas do mesmo tipo)
- **Quiet hours**: Nenhum (alertas 24/7)
- **Canais**: Telegram

---

## 🎯 Casos de Uso Reais

### 1. Monitoramento de Idosos
- Sistema detecta quedas e inatividade
- Família recebe alertas imediatos
- Pode salvar vidas

### 2. Segurança Residencial
- Pessoa viaja e deixa casa vazia
- Sistema detecta movimento suspeito
- Proprietário é alertado no Telegram
- Alternativa a câmeras (mais privacidade)

### 3. Monitoramento de Escritório
- Detecta presença fora do horário
- Alerta sobre atividade não autorizada

---

## 🔧 Ajustar Sensibilidade

Se estiver recebendo muitos/poucos alertas, você pode ajustar:

### Via API (enquanto sistema está rodando):

```bash
curl -X PUT "http://localhost:8000/api/notifications/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "channels": ["telegram"],
    "telegram_bot_token": "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA",
    "telegram_chat_ids": ["2085218769"],
    "min_confidence": 0.8,
    "cooldown_seconds": 300
  }'
```

Ajuste:
- `min_confidence`: 0.7 (70%) a 0.95 (95%)
  - Menor = mais alertas (mais sensível)
  - Maior = menos alertas (menos sensível)
- `cooldown_seconds`: 60 a 600 (1 a 10 minutos)
  - Menor = mais alertas frequentes
  - Maior = menos alertas (evita spam)

---

## 📊 Visualizar no Frontend

Enquanto o sistema está rodando, acesse:

```
http://localhost:5173/
```

Você verá:
- Gráficos em tempo real
- Histórico de eventos
- Status atual do sistema
- Radar Wi-Fi

---

## ⏹️ Parar o Sistema

Pressione `Ctrl+C` no terminal onde está rodando o script.

O sistema para automaticamente e salva todos os dados.

---

## 🐛 Problemas Comuns

### "Backend não está rodando"
```bash
cd backend
uvicorn app.main:app --reload
```

### "Telegram não está enviando"
- Verifique se você deu `/start` no bot
- Confirme que o Chat ID está correto
- Teste com: `python test_telegram_direto.py`

### "Não está detectando movimento"
- Aproxime-se do roteador Wi-Fi
- Faça movimentos mais bruscos
- Sistema usa RSSI (força do sinal)
- Quanto mais próximo do roteador, melhor a detecção

---

## 📈 Próximos Passos

Depois de testar, você pode:

1. **Ajustar limiares** de detecção
2. **Configurar horários de silêncio** (quiet hours)
3. **Adicionar WhatsApp** como canal adicional
4. **Treinar modelo ML** com seus dados reais
5. **Integrar com seu SaaS** de cuidadores de idosos

---

## 💡 Dicas

- Sistema funciona melhor em ambientes fechados
- Quanto mais próximo do roteador, melhor
- Paredes e obstáculos afetam o sinal
- Teste em diferentes horários do dia
- Calibre o sistema para seu ambiente específico

---

## ✅ Sistema Pronto!

Agora você tem um sistema COMPLETO de detecção por Wi-Fi funcionando!

**Tudo é REAL:**
- ✅ Captura de sinais Wi-Fi
- ✅ Detecção de eventos
- ✅ Alertas no Telegram
- ✅ Histórico no banco de dados
- ✅ Visualização no frontend

**Pronto para produção!** 🚀
