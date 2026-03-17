# 🚀 Instalação Rápida - PostgreSQL Configurado

Suas credenciais já estão configuradas! Siga estes passos:

## 1️⃣ Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

Isso vai instalar:
- `asyncpg` - Driver assíncrono para PostgreSQL
- `psycopg2-binary` - Driver síncrono (backup)
- `python-dotenv` - Carregador de variáveis de ambiente

## 2️⃣ Testar Conexão

```bash
python test_db_connection.py
```

Você deve ver:
```
✅ Conexão bem-sucedida!
📊 PostgreSQL Version: ...
📋 Tabelas encontradas (8):
   ✓ behavior_patterns
   ✓ calibration_profiles
   ✓ events
   ✓ ml_models
   ✓ notification_logs
   ✓ performance_metrics
   ✓ zones
```

## 3️⃣ Iniciar Sistema

```bash
python -m app.main
```

O sistema vai conectar automaticamente no PostgreSQL!

## ✅ Configuração Atual

```
Host: localhost
Port: 5432
Database: wifi_movimento
User: postgres
Password: ********** (configurada)
```

## 🔍 Verificar Dados no PostgreSQL

```bash
# Conectar ao banco
psql -U postgres -d wifi_movimento

# Ver tabelas
\dt

# Ver dados de uma tabela
SELECT * FROM events LIMIT 5;

# Sair
\q
```

## ⚠️ Troubleshooting

### Erro: "asyncpg not found"
```bash
pip install asyncpg
```

### Erro: "connection refused"
Verifique se PostgreSQL está rodando:
```bash
# Windows
# Abra Services e procure por PostgreSQL

# Linux
sudo systemctl status postgresql
```

### Erro: "password authentication failed"
Verifique o arquivo `.env` - senha deve estar correta

## 🎉 Pronto!

Seu sistema está configurado para usar PostgreSQL!
