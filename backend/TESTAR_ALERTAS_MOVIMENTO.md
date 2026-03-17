# 🎯 COMO TESTAR ALERTAS DE MOVIMENTO

## ✅ O Que Foi Feito

1. ✅ Modificado `AlertService` para alertar em movimento
2. ✅ Configurado Telegram com confiança 60% e cooldown 30s
3. ⚠️  **FALTA**: Reiniciar o backend para aplicar mudanças

---

## 🚀 PASSO A PASSO PARA TESTAR

### 1. Parar o Backend Atual

No terminal onde o backend está rodando, pressione:
```
Ctrl+C
```

### 2. Reiniciar o Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Aguarde aparecer:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. Iniciar o Sistema de Monitoramento

Em OUTRO terminal:

```bash
cd backend
python iniciar_sistema_completo.py
```

Você verá:
```
✅ Telegram configurado com sucesso!
✅ Mensagem de teste enviada!
✅ Monitoramento iniciado!
```

### 4. TESTAR MOVIMENTO

**Agora ande pelo ambiente!**

Você deve:
- Ver no terminal: `🔵 Movimento | Confiança: 60%`
- **RECEBER NO TELEGRAM**: "🚶 Movimento detectado no ambiente! Confiança: 60%"

### 5. TESTAR PRESENÇA PARADA

**Fique parado por alguns segundos**

Você deve:
- Ver no terminal: `🟢 Presença parada | Confiança: 75%`
- **RECEBER NO TELEGRAM**: "👤 Presença detectada no ambiente. Confiança: 75%"

---

## ⏱️ Cooldown de 30 Segundos

Você receberá alertas a cada 30 segundos:
- Movimento às 10:00:00
- Movimento às 10:00:30
- Movimento às 10:01:00
- etc.

Isso evita spam mas permite testar rapidamente.

---

## 📱 Mensagens que Você Receberá

### Movimento
```
🚶 Movimento detectado no ambiente! Confiança: 60%
```

### Presença Parada
```
👤 Presença detectada no ambiente. Confiança: 75%
```

### Queda (se detectar)
```
🚨 Possível queda detectada! Confiança: 95%
```

### Inatividade (após 30s parado)
```
⏰ Inatividade prolongada detectada. Confiança: 80%
```

---

## 🔍 Verificar se Está Funcionando

Execute:
```bash
python verificar_eventos_e_alertas.py
```

Você deve ver:
```
Alertas enviados:
  - presence_moving: X
  - presence_still: Y
  - fall_suspected: Z
```

Se não aparecer alertas de movimento, o backend não foi reiniciado.

---

## ✅ Checklist

- [ ] Backend reiniciado (Ctrl+C e uvicorn novamente)
- [ ] Sistema de monitoramento rodando (iniciar_sistema_completo.py)
- [ ] Andou pelo ambiente
- [ ] Recebeu alerta de movimento no Telegram
- [ ] Ficou parado
- [ ] Recebeu alerta de presença no Telegram

---

## 🎉 Sucesso!

Quando receber os alertas no Telegram, você terá validado:
- ✅ Captura de Wi-Fi funcionando
- ✅ Detecção de eventos funcionando
- ✅ Telegram funcionando
- ✅ Sistema completo end-to-end

**Pronto para produção!** 🚀

---

## 💡 Próximos Passos

1. **Testar casos de uso reais**:
   - Saia de casa e veja se detecta quando voltar
   - Deixe casa vazia e peça alguém entrar
   - Simule queda (movimento brusco)

2. **Ajustar sensibilidade**:
   - Se muitos alertas: aumentar confiança para 70%
   - Se poucos alertas: diminuir para 50%

3. **Implementar painel de configuração**:
   - Frontend para escolher quais alertas
   - Perfis: "Casa Vazia", "Idoso", "Escritório"
   - Horários de silêncio

4. **Multi-tenant para SaaS**:
   - Cada cliente tem suas configurações
   - Bot do Telegram por cliente
   - Dashboard personalizado
