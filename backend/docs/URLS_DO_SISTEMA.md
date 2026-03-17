# 🌐 URLs do Sistema WiFiSense

## ✅ Servidor Rodando em: http://localhost:8000

## 📍 Rotas Disponíveis

### 1. Status do Sistema
```
http://localhost:8000/api/status
```
**O que retorna**: Status do monitoramento, eventos, confiança, etc.

### 2. Documentação Interativa (Swagger)
```
http://localhost:8000/docs
```
**O que é**: Interface visual para testar todas as APIs!
👉 **ACESSE ESTA URL NO NAVEGADOR!** É a melhor forma de testar!

### 3. Documentação Alternativa (ReDoc)
```
http://localhost:8000/redoc
```
**O que é**: Documentação bonita e organizada de todas as APIs

### 4. Configuração de Notificações
```
GET  http://localhost:8000/api/notifications/config
PUT  http://localhost:8000/api/notifications/config
```

### 5. Logs de Notificações
```
GET http://localhost:8000/api/notifications/logs
```
Filtros disponíveis:
- `?channel=telegram` - Filtrar por canal
- `?success=true` - Apenas sucessos
- `?limit=10` - Limitar resultados
- `?offset=0` - Paginação

### 6. Testar Notificação
```
POST http://localhost:8000/api/notifications/test
```

### 7. Eventos Detectados
```
GET http://localhost:8000/api/events
GET http://localhost:8000/api/events/{id}
```

### 8. Monitoramento
```
POST http://localhost:8000/api/monitor/start
POST http://localhost:8000/api/monitor/stop
GET  http://localhost:8000/api/monitor/status
```

### 9. Configuração Geral
```
GET http://localhost:8000/api/config
PUT http://localhost:8000/api/config
```

---

## 🎯 Como Testar Agora

### Opção 1: Navegador (MAIS FÁCIL!)

Abra no navegador:
```
http://localhost:8000/docs
```

Você vai ver uma interface linda com TODAS as APIs!
Pode testar clicando em "Try it out" em cada endpoint!

### Opção 2: PowerShell

```powershell
# Status
Invoke-WebRequest http://localhost:8000/api/status

# Configuração de notificações
Invoke-WebRequest http://localhost:8000/api/notifications/config

# Logs
Invoke-WebRequest http://localhost:8000/api/notifications/logs
```

### Opção 3: Python

```python
import requests

# Status
response = requests.get("http://localhost:8000/api/status")
print(response.json())

# Configuração
response = requests.get("http://localhost:8000/api/notifications/config")
print(response.json())
```

---

## ⚠️ IMPORTANTE

### ❌ NÃO FUNCIONA:
```
http://localhost:8000/          ← Retorna 404
http://localhost:8000/status    ← Retorna 404
```

### ✅ FUNCIONA:
```
http://localhost:8000/api/status           ← Correto!
http://localhost:8000/docs                 ← Interface visual!
http://localhost:8000/api/notifications/config
```

**Sempre use `/api/` antes das rotas!**

---

## 🚀 Teste Rápido Agora

1. Abra o navegador
2. Cole esta URL:
   ```
   http://localhost:8000/docs
   ```
3. Explore todas as APIs visualmente!

Ou teste o status:
```
http://localhost:8000/api/status
```

---

## 📱 Próximo Passo: Telegram

Depois de explorar as APIs, configure o Telegram:
1. Leia: `GUIA_TELEGRAM_BOT.md`
2. Crie seu bot (5 minutos)
3. Me passe as credenciais
4. Testamos as notificações!

**O sistema está 100% funcional!** 🎉
