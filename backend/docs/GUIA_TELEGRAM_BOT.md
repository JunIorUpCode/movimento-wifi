# 🤖 Guia Completo: Como Criar um Bot do Telegram (GRATUITO!)

## ✅ Por que Telegram?

- ✅ **100% GRATUITO** (sem custos)
- ✅ Fácil de configurar (5 minutos)
- ✅ Sem limites de mensagens
- ✅ API oficial e confiável
- ✅ Funciona em qualquer lugar do mundo

## 📱 Passo a Passo Completo

### Passo 1: Abrir o Telegram

1. Abra o aplicativo Telegram no seu celular ou computador
2. Se não tiver, baixe em: https://telegram.org/

### Passo 2: Encontrar o BotFather

1. Na barra de pesquisa do Telegram, digite: `@BotFather`
2. Clique no contato oficial (tem um check azul ✓)
3. Clique em **START** ou **INICIAR**

### Passo 3: Criar o Bot

1. Digite o comando: `/newbot`

2. O BotFather vai perguntar o **nome do bot**:
   ```
   Exemplo: WiFiSense Alertas
   ```
   (Pode ser qualquer nome que você quiser)

3. Depois ele pede o **username do bot** (deve terminar com "bot"):
   ```
   Exemplo: wifisense_alertas_bot
   ```
   (Deve ser único, se já existir, tente outro nome)

4. **PRONTO!** O BotFather vai te dar o **TOKEN**:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
   ```

### Passo 4: Copiar o Token

**IMPORTANTE**: Copie esse token e guarde bem! Você vai precisar dele.

Exemplo de token:
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
```

### Passo 5: Conseguir o Chat ID

Agora você precisa do seu **Chat ID** (identificador da conversa):

#### Opção A - Usando um Bot Helper (MAIS FÁCIL):

1. No Telegram, procure por: `@userinfobot`
2. Clique em **START**
3. Ele vai te mostrar seu **ID**:
   ```
   Id: 123456789
   ```
4. Copie esse número!

#### Opção B - Manualmente:

1. Envie uma mensagem qualquer para o seu bot (o que você acabou de criar)
2. Abra no navegador:
   ```
   https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
   ```
   (Substitua `<SEU_TOKEN>` pelo token que você copiou)

3. Procure por `"chat":{"id":123456789`
4. Esse número é seu Chat ID!

### Passo 6: Testar o Bot

Vamos testar se está funcionando! Abra um terminal e rode:

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<SEU_CHAT_ID>", "text": "Teste do WiFiSense! 🎉"}'
```

Se você receber a mensagem no Telegram, está funcionando! 🎉

---

## 🔧 Configurar no WiFiSense

Agora que você tem:
- ✅ Token do bot
- ✅ Chat ID

Vamos configurar no sistema!

### Método 1: Via API (Recomendado)

Use o Postman, Insomnia ou curl:

```bash
curl -X PUT "http://localhost:8000/api/notifications/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "bot_token": "SEU_TOKEN_AQUI",
        "chat_id": "SEU_CHAT_ID_AQUI"
      }
    ],
    "min_confidence": 0.7,
    "cooldown_seconds": 300
  }'
```

### Método 2: Testar Diretamente

Crie um arquivo `test_telegram.py`:

```python
import asyncio
import time
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig, TelegramChannelConfig

async def test():
    # Configurar
    config = NotificationConfig(
        enabled=True,
        channels=[
            TelegramChannelConfig(
                type="telegram",
                bot_token="SEU_TOKEN_AQUI",
                chat_id="SEU_CHAT_ID_AQUI"
            )
        ],
        min_confidence=0.7
    )
    
    service = NotificationService(config)
    
    # Criar alerta de teste
    alert = Alert(
        event_type="fall_suspected",
        confidence=0.95,
        timestamp=time.time(),
        message="🚨 TESTE: Queda detectada!",
        details={"rate_of_change": 15.5}
    )
    
    # Enviar
    print("Enviando alerta de teste...")
    await service.send_alert(alert)
    print("✓ Alerta enviado! Verifique seu Telegram!")

if __name__ == "__main__":
    asyncio.run(test())
```

Execute:
```bash
python test_telegram.py
```

---

## 📊 Exemplo de Mensagem que Você Vai Receber

```
🚨 ALERTA: Queda suspeita

⏰ 14/03/2026 18:00:45
📊 Confiança: 95%

📝 Detalhes:
• Taxa de mudança: 15.5 dB/s
```

---

## 🔒 Segurança

**IMPORTANTE**: 
- ❌ Nunca compartilhe seu token publicamente
- ❌ Não commite o token no Git
- ✅ Use variáveis de ambiente (.env)
- ✅ Mantenha o token seguro

---

## 💰 Custos

### Telegram Bot API:
- ✅ **GRATUITO**
- ✅ Sem limites de mensagens
- ✅ Sem custos mensais
- ✅ Sem necessidade de cartão de crédito

### WhatsApp (Twilio):
- ❌ **PAGO**
- 💵 ~$0.005 por mensagem
- 💵 Precisa de conta Twilio
- 💵 Precisa de cartão de crédito

**Recomendação**: Use Telegram para testes e produção inicial. É gratuito e funciona perfeitamente!

---

## 🆘 Problemas Comuns

### "Unauthorized" ou "401"
- ✅ Verifique se o token está correto
- ✅ Certifique-se de não ter espaços extras

### "Bad Request: chat not found"
- ✅ Verifique se o Chat ID está correto
- ✅ Envie uma mensagem para o bot primeiro

### "Forbidden: bot was blocked by the user"
- ✅ Desbloqueie o bot no Telegram
- ✅ Clique em START novamente

---

## 📞 Suporte

Se tiver problemas:
1. Verifique se o token e chat_id estão corretos
2. Teste manualmente com curl
3. Verifique os logs do sistema

---

## 🎯 Próximos Passos

Depois de configurar o Telegram:

1. ✅ Testar notificação manual
2. ✅ Configurar quiet hours (horários de silêncio)
3. ✅ Ajustar threshold de confiança
4. ✅ Testar com detecção real de movimento

**Pronto para começar!** 🚀
