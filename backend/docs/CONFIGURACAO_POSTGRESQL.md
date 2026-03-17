# Guia de Configuração do PostgreSQL para WiFiSense

## 📋 Pré-requisitos

- PostgreSQL instalado e rodando em localhost
- Credenciais de acesso (usuário e senha)
- Python 3.11+ com pip

## 🔧 Passo 1: Instalar Driver PostgreSQL

Instale o driver `psycopg2` para conectar Python ao PostgreSQL:

```bash
cd backend
pip install psycopg2-binary
```

Ou adicione ao `requirements.txt`:
```
psycopg2-binary>=2.9.9
```

## 🗄️ Passo 2: Criar Banco de Dados

### Opção A: Via psql (linha de comando)

```bash
# Conectar ao PostgreSQL como superusuário
psql -U postgres

# Criar banco de dados
CREATE DATABASE wifisense;

# Criar usuário (opcional, se não quiser usar postgres)
CREATE USER wifisense_user WITH PASSWORD 'sua_senha_aqui';

# Dar permissões
GRANT ALL PRIVILEGES ON DATABASE wifisense TO wifisense_user;

# Sair
\q
```

### Opção B: Via pgAdmin

1. Abra o pgAdmin
2. Clique com botão direito em "Databases"
3. Selecione "Create" > "Database"
4. Nome: `wifisense`
5. Clique em "Save"

## 📊 Passo 3: Executar Script SQL

Execute o script SQL para criar todas as tabelas:

```bash
# Via psql
psql -U postgres -d wifisense -f setup_postgresql.sql

# Ou se criou usuário específico
psql -U wifisense_user -d wifisense -f setup_postgresql.sql
```

Você deve ver a saída confirmando a criação das 8 tabelas:
- events
- calibration_profiles
- behavior_patterns
- zones
- performance_metrics
- ml_models
- notification_logs

## ⚙️ Passo 4: Configurar String de Conexão

### Opção A: Variável de Ambiente (RECOMENDADO)

Crie um arquivo `.env` na pasta `backend/`:

```bash
# backend/.env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/wifisense
```

Substitua:
- `usuario`: seu usuário PostgreSQL (ex: `postgres` ou `wifisense_user`)
- `senha`: sua senha
- `localhost`: endereço do servidor (mantenha se for local)
- `5432`: porta padrão do PostgreSQL
- `wifisense`: nome do banco de dados

**Exemplo real:**
```
DATABASE_URL=postgresql://postgres:minhasenha123@localhost:5432/wifisense
```

### Opção B: Modificar database.py Diretamente

Edite o arquivo `backend/app/db/database.py`:

```python
# Antes (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./wifisense.db"

# Depois (PostgreSQL)
SQLALCHEMY_DATABASE_URL = "postgresql://usuario:senha@localhost:5432/wifisense"
```

## 🔐 Passo 5: Configurar Leitura de Variáveis de Ambiente

Instale python-dotenv:

```bash
pip install python-dotenv
```

Modifique `backend/app/db/database.py`:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Carregar variáveis de ambiente
load_dotenv()

# Usar DATABASE_URL do .env ou fallback para SQLite
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./wifisense.db"  # Fallback
)

# Configuração específica para PostgreSQL
connect_args = {}
if not SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    connect_args = {"check_same_thread": False}  # Apenas para SQLite

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para obter sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## ✅ Passo 6: Testar Conexão

Crie um script de teste `backend/test_db_connection.py`:

```python
"""Testa conexão com PostgreSQL."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"🔗 Testando conexão com: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 PostgreSQL Version: {version}")
        
        # Listar tabelas
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        print(f"\n📋 Tabelas encontradas ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
            
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
```

Execute:
```bash
python test_db_connection.py
```

## 🚀 Passo 7: Iniciar Aplicação

Agora você pode iniciar o sistema normalmente:

```bash
cd backend
python -m app.main
```

O sistema vai conectar automaticamente no PostgreSQL!

## 📝 Estrutura de Arquivos

```
backend/
├── .env                          # Credenciais (NÃO commitar!)
├── setup_postgresql.sql          # Script de criação das tabelas
├── test_db_connection.py         # Script de teste
├── app/
│   ├── db/
│   │   └── database.py          # Configuração do banco
│   └── models/
│       └── models.py            # Modelos SQLAlchemy
└── requirements.txt             # Dependências
```

## 🔒 Segurança

**IMPORTANTE:** Adicione `.env` ao `.gitignore`:

```bash
# .gitignore
.env
*.env
```

Nunca commite suas credenciais no Git!

## 🐛 Troubleshooting

### Erro: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Erro: "password authentication failed"
- Verifique usuário e senha no `.env`
- Confirme que o usuário tem permissões no banco

### Erro: "could not connect to server"
- Verifique se PostgreSQL está rodando: `sudo systemctl status postgresql`
- Confirme a porta (padrão: 5432)
- Verifique firewall

### Erro: "database does not exist"
```bash
psql -U postgres -c "CREATE DATABASE wifisense;"
```

### Erro: "relation does not exist"
Execute o script SQL novamente:
```bash
psql -U postgres -d wifisense -f setup_postgresql.sql
```

## 📊 Comandos Úteis PostgreSQL

```bash
# Conectar ao banco
psql -U postgres -d wifisense

# Listar tabelas
\dt

# Descrever tabela
\d events

# Ver dados de uma tabela
SELECT * FROM events LIMIT 10;

# Contar registros
SELECT COUNT(*) FROM notification_logs;

# Sair
\q
```

## 🔄 Migração de SQLite para PostgreSQL (Opcional)

Se você já tem dados no SQLite e quer migrar:

```bash
# Instalar ferramenta de migração
pip install pgloader

# Migrar dados
pgloader sqlite:///./wifisense.db postgresql://usuario:senha@localhost/wifisense
```

## ✨ Pronto!

Seu sistema WiFiSense agora está configurado para usar PostgreSQL! 🎉

Para qualquer dúvida, consulte:
- Documentação PostgreSQL: https://www.postgresql.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/
