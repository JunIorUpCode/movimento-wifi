# 📚 Documentação Backend - WiFiSense

## 📖 Índice de Documentos

### Guias de Configuração
- [📱 Guia Telegram Bot](GUIA_TELEGRAM_BOT.md) - Como criar bot GRATUITO (5 minutos)
- [⚙️ Configuração PostgreSQL](CONFIGURACAO_POSTGRESQL.md) - Setup do banco
- [✅ Validação PostgreSQL](VALIDACAO_POSTGRESQL.md) - Status e testes
- [📝 Resumo Configuração](RESUMO_CONFIGURACAO.md) - Resumo geral

### Guias de Uso
- [🌐 URLs do Sistema](URLS_DO_SISTEMA.md) - Todas as rotas disponíveis
- [📝 Resumo para Testar](RESUMO_PARA_TESTAR.md) - Como testar o sistema
- [🚀 Instalação Rápida](INSTALACAO_RAPIDA.md) - Setup rápido

---

## 🎯 Por Onde Começar?

### 1. Configurar Banco de Dados
1. Leia: [Configuração PostgreSQL](CONFIGURACAO_POSTGRESQL.md)
2. Execute: `python test_db_connection.py`
3. Valide: [Validação PostgreSQL](VALIDACAO_POSTGRESQL.md)

### 2. Configurar Notificações (Telegram)
1. Leia: [Guia Telegram Bot](GUIA_TELEGRAM_BOT.md)
2. Crie seu bot (5 minutos, GRATUITO)
3. Teste: `python test_telegram_notification.py`

### 3. Testar o Sistema
1. Veja todas as URLs: [URLs do Sistema](URLS_DO_SISTEMA.md)
2. Acesse: http://localhost:8000/docs
3. Teste os endpoints

---

## 📱 Acesso Rápido

### APIs Principais
- **Documentação**: http://localhost:8000/docs
- **Status**: http://localhost:8000/api/status
- **Notificações**: http://localhost:8000/api/notifications/config
- **Logs**: http://localhost:8000/api/notifications/logs

### Scripts de Teste
```bash
# Testar conexão PostgreSQL
python test_db_connection.py

# Testar notificação Telegram
python test_telegram_notification.py

# Aplicar migrações
python run_migrations.py upgrade
```

---

## 🔧 Comandos Úteis

### Iniciar Servidor
```bash
uvicorn app.main:app --reload
```

### Testar Conexão
```bash
python test_db_connection.py
```

### Migrações
```bash
python run_migrations.py upgrade
python run_migrations.py downgrade
```

---

## 💡 Dicas

- **Telegram é GRATUITO!** Não precisa de cartão de crédito
- **Use /docs** para testar as APIs visualmente
- **PostgreSQL** está configurado e funcionando
- **Logs** ficam em `logs/wifisense.log`
