# 🌐 WiFiSense Local - Sistema de Detecção de Movimento via Wi-Fi

Sistema de monitoramento de presença e detecção de quedas usando análise de sinal Wi-Fi (RSSI).

## 🚀 Acesso Rápido

### Frontend (Interface Visual)
```
http://localhost:5173/
```
👉 **Abra esta URL para ver o dashboard!**

### Backend (API)
```
http://localhost:8000/docs
```
👉 **Documentação interativa das APIs**

---

## 📊 Status Atual

- ✅ Backend rodando em `http://localhost:8000`
- ✅ Frontend rodando em `http://localhost:5173`
- ✅ PostgreSQL conectado (`wifi_movimento`)
- ✅ Sistema de notificações implementado
- ✅ Machine Learning integrado

---

## 🎯 Funcionalidades

### Detecção
- 🚶 Movimento detectado
- 🛑 Inatividade prolongada
- ⚠️ Queda suspeita
- 📊 Anomalias no padrão

### Notificações
- 📱 Telegram (GRATUITO)
- 💬 WhatsApp (via Twilio - pago)
- 🌐 Webhooks (HTTP POST)

### Machine Learning
- 🧠 Classificação de eventos
- 📈 Aprendizado de padrões
- 🎯 Detecção de anomalias
- ⚡ Calibração adaptativa

---

## 📁 Estrutura do Projeto

```
movimento wifi/
├── backend/              # API FastAPI + PostgreSQL
│   ├── app/             # Código da aplicação
│   ├── docs/            # 📚 Documentação do backend
│   ├── migrations/      # Migrações do banco
│   └── models/          # Modelos ML treinados
├── frontend/            # Interface React + TypeScript
│   └── src/            # Código do frontend
├── docs/                # 📚 Documentação geral
└── logs/                # Logs do sistema
```

---

## 📚 Documentação

### Guias Principais
- [🚀 Guia Rápido](docs/GUIA_RAPIDO.md)
- [🏗️ Arquitetura](docs/ARQUITETURA.md)
- [🔧 Integração Hardware](docs/INTEGRACAO_HARDWARE.md)

### Backend
- [📱 Guia Telegram Bot](backend/docs/GUIA_TELEGRAM_BOT.md) - Como criar bot GRATUITO
- [🌐 URLs do Sistema](backend/docs/URLS_DO_SISTEMA.md) - Todas as rotas
- [✅ Validação PostgreSQL](backend/docs/VALIDACAO_POSTGRESQL.md)
- [⚙️ Configuração PostgreSQL](backend/docs/CONFIGURACAO_POSTGRESQL.md)
- [📝 Resumo para Testar](backend/docs/RESUMO_PARA_TESTAR.md)

### Melhorias e Ajustes
- [💡 Melhorias Sugeridas](docs/MELHORIAS_SUGERIDAS.md)
- [🎯 Ajuste Detecção Movimento](docs/AJUSTE_DETECCAO_MOVIMENTO.md)
- [📡 Captura Wi-Fi Real](docs/CAPTURA_WIFI_REAL.md)

---

## 🔧 Comandos Úteis

### Iniciar Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### Iniciar Frontend
```bash
cd frontend
npm run dev
```

### Testar Conexão PostgreSQL
```bash
cd backend
python test_db_connection.py
```

### Testar Notificação Telegram
```bash
cd backend
python test_telegram_notification.py
```

---

## 🎯 Próximos Passos

1. ✅ Acesse o frontend: `http://localhost:5173/`
2. 📱 Configure o Telegram (veja `backend/docs/GUIA_TELEGRAM_BOT.md`)
3. 🧪 Teste as notificações
4. 📊 Explore o dashboard

---

## 💰 Custos

### Telegram
- ✅ **GRATUITO**
- ✅ Ilimitado
- ✅ Sem cartão de crédito

### WhatsApp (Twilio)
- ❌ **PAGO** (~$0.005/msg)
- ❌ Precisa de conta Twilio

**Recomendação**: Use Telegram!

---

## 🆘 Suporte

### Problemas Comuns

**Frontend não abre?**
```bash
cd frontend
npm install
npm run dev
```

**Backend não conecta?**
```bash
cd backend
python test_db_connection.py
```

**Erro 404 nas APIs?**
- Use `/api/` antes das rotas
- Exemplo: `http://localhost:8000/api/status`

---

## � Contato

Para dúvidas ou suporte, consulte a documentação em `/docs` ou `/backend/docs`.

---

## 🎉 Sistema Pronto!

O WiFiSense está rodando e pronto para uso. Acesse o frontend e explore! 🚀
