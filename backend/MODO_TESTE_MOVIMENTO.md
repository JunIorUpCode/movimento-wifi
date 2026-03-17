# 🧪 MODO TESTE - Alertas de Movimento Ativados

## ✅ O Que Foi Configurado

O sistema agora está em **MODO TESTE** e enviará alertas no Telegram para:

### 📱 Tipos de Alertas Ativos

1. **🚶 Movimento Detectado**
   - Quando: Você se movimenta no ambiente
   - Confiança: ≥ 60%
   - Mensagem: "🚶 Movimento detectado no ambiente!"

2. **👤 Presença Parada**
   - Quando: Sistema detecta alguém parado no local
   - Confiança: ≥ 60%
   - Mensagem: "👤 Presença detectada no ambiente"

3. **🚨 Queda Suspeita**
   - Quando: Movimento brusco ou queda de sinal >15 dBm
   - Confiança: ≥ 60%
   - Mensagem: "🚨 Possível queda detectada!"

4. **⏰ Inatividade Prolongada**
   - Quando: Sem movimento por >30 segundos
   - Confiança: ≥ 60%
   - Mensagem: "⏰ Inatividade prolongada detectada"

---

## ⚙️ Configurações Atuais

- ✅ **Telegram**: Ativo
- ✅ **Confiança mínima**: 60% (mais sensível)
- ✅ **Cooldown**: 30 segundos (alertas mais frequentes)
- ✅ **Quiet hours**: Nenhum (24/7)

---

## 🧪 Como Testar AGORA

### 1. Certifique-se que o Sistema Está Rodando

Verifique se você vê no terminal:
```
🟢 Presença parada | Confiança: 75% | RSSI: -65.0 dBm
```

Se não estiver rodando:
```bash
python iniciar_sistema_completo.py
```

### 2. Teste de Movimento

**Ação**: Ande pelo ambiente, movimente-se próximo ao roteador

**Resultado esperado**:
- Terminal mostra: `🔵 Movimento | Confiança: 60%`
- **Você recebe no Telegram**: "🚶 Movimento detectado no ambiente! Confiança: 60%"

### 3. Teste de Presença Parada

**Ação**: Fique parado por alguns segundos

**Resultado esperado**:
- Terminal mostra: `🟢 Presença parada | Confiança: 75%`
- **Você recebe no Telegram**: "👤 Presença detectada no ambiente. Confiança: 75%"

### 4. Teste de Queda (Simulação)

**Ação**: Movimento brusco ou afaste-se rapidamente do roteador

**Resultado esperado**:
- Terminal mostra: `🔴 🚨 QUEDA SUSPEITA`
- **Você recebe no Telegram**: "🚨 Possível queda detectada! Confiança: 95%"

---

## 📊 Frequência de Alertas

Com cooldown de 30 segundos:
- Você receberá NO MÁXIMO 1 alerta de cada tipo a cada 30 segundos
- Exemplo: Se você ficar andando, receberá alertas de movimento a cada 30s

Isso evita spam mas permite testar rapidamente.

---

## 🎯 Casos de Uso Reais

### 1. Segurança Residencial (Casa Vazia)
```
Cenário: Você viaja e deixa casa vazia
Sistema: Detecta movimento
Alerta: "🚶 Movimento detectado no ambiente!"
Ação: Você verifica se é invasão ou não
```

### 2. Monitoramento de Idosos
```
Cenário: Idoso em casa sozinho
Sistema: Detecta queda
Alerta: "🚨 Possível queda detectada!"
Ação: Família verifica imediatamente
```

### 3. Segurança Empresarial
```
Cenário: Escritório fechado à noite
Sistema: Detecta presença fora do horário
Alerta: "👤 Presença detectada no ambiente"
Ação: Segurança verifica acesso não autorizado
```

---

## 🔧 Ajustar Sensibilidade

Se estiver recebendo **MUITOS** alertas:

```bash
# Aumentar confiança mínima para 70%
# Aumentar cooldown para 60 segundos
python -c "
import asyncio, httpx
async def update():
    async with httpx.AsyncClient() as c:
        await c.put('http://localhost:8000/api/notifications/config', 
            json={'enabled': True, 'channels': ['telegram'], 
                  'telegram_bot_token': '8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA',
                  'telegram_chat_ids': ['2085218769'],
                  'min_confidence': 0.7, 'cooldown_seconds': 60, 'quiet_hours': []})
asyncio.run(update())
"
```

Se estiver recebendo **POUCOS** alertas:

```bash
# Diminuir confiança mínima para 50%
# Diminuir cooldown para 15 segundos
python -c "
import asyncio, httpx
async def update():
    async with httpx.AsyncClient() as c:
        await c.put('http://localhost:8000/api/notifications/config', 
            json={'enabled': True, 'channels': ['telegram'], 
                  'telegram_bot_token': '8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA',
                  'telegram_chat_ids': ['2085218769'],
                  'min_confidence': 0.5, 'cooldown_seconds': 15, 'quiet_hours': []})
asyncio.run(update())
"
```

---

## 🔄 Voltar ao Modo Normal (Só Críticos)

Quando terminar os testes e quiser receber apenas alertas críticos:

```bash
python -c "
import asyncio, httpx
async def update():
    async with httpx.AsyncClient() as c:
        await c.put('http://localhost:8000/api/notifications/config', 
            json={'enabled': True, 'channels': ['telegram'], 
                  'telegram_bot_token': '8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA',
                  'telegram_chat_ids': ['2085218769'],
                  'min_confidence': 0.7, 'cooldown_seconds': 300, 'quiet_hours': []})
asyncio.run(update())
"
```

E modifique `backend/app/services/alert_service.py` removendo as linhas de movimento.

---

## 📈 Próximos Passos

Depois de validar que funciona:

### 1. Painel de Configuração (Frontend)
- Interface para escolher quais alertas ativar
- Ajustar sensibilidade por tipo de evento
- Configurar horários de silêncio

### 2. Multi-Tenant (SaaS)
- Cada usuário tem suas próprias configurações
- Bot do Telegram por família/empresa
- Perfis diferentes: "Casa Vazia", "Idoso", "Escritório"

### 3. Machine Learning
- Treinar modelo com seus dados reais
- Detecção mais precisa
- Menos falsos positivos

---

## ✅ Checklist de Teste

- [ ] Sistema rodando (terminal mostrando eventos)
- [ ] Recebeu mensagem de teste no Telegram
- [ ] Andou pelo ambiente
- [ ] Recebeu alerta de movimento no Telegram
- [ ] Ficou parado
- [ ] Recebeu alerta de presença no Telegram
- [ ] Fez movimento brusco
- [ ] Recebeu alerta de queda no Telegram (se detectou)

---

## 🐛 Problemas?

### "Não estou recebendo alertas"

1. Verifique se sistema está rodando:
   ```bash
   python iniciar_sistema_completo.py
   ```

2. Verifique configuração:
   ```bash
   curl http://localhost:8000/api/notifications/config
   ```

3. Verifique logs de notificação:
   ```bash
   python verificar_eventos_e_alertas.py
   ```

### "Recebendo muitos alertas"

- Aumente o cooldown (60s ou mais)
- Aumente a confiança mínima (70% ou mais)

### "Recebendo poucos alertas"

- Diminua o cooldown (15s)
- Diminua a confiança mínima (50%)
- Movimente-se mais próximo do roteador

---

## 🎉 Sistema Pronto para Produção!

Agora você tem um sistema completo de detecção por Wi-Fi com alertas configuráveis!

**Pronto para:**
- ✅ Segurança residencial
- ✅ Monitoramento de idosos
- ✅ Segurança empresarial
- ✅ Integração com seu SaaS

**Próximo passo**: Validar com clientes reais e coletar feedback! 🚀
