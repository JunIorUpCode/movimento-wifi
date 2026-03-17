# License Service

Serviço de gerenciamento de licenças para a plataforma WiFiSense SaaS.

## Funcionalidades

- **Geração de Licenças**: Cria chaves de ativação criptograficamente seguras (80 bits de entropia)
- **Validação de Licenças**: Valida chaves de ativação durante registro de dispositivos
- **Revogação de Licenças**: Permite revogar licenças ativas
- **Extensão de Licenças**: Estende data de expiração de licenças
- **Validação Periódica**: Valida todas as licenças a cada 24 horas

## Formato de Chave de Ativação

```
XXXX-XXXX-XXXX-XXXX
```

- 16 caracteres + 3 hífens = 19 caracteres total
- Base32 customizado sem caracteres ambíguos (0, O, I, 1, L removidos)
- 80 bits de entropia (10 bytes)
- Hash SHA256 armazenado no banco de dados

## Endpoints

### Administrativos (Admin Only)

- `POST /api/admin/licenses` - Gerar nova licença
- `GET /api/admin/licenses` - Listar licenças com filtros
- `GET /api/admin/licenses/{id}` - Detalhes da licença
- `PUT /api/admin/licenses/{id}/revoke` - Revogar licença
- `PUT /api/admin/licenses/{id}/extend` - Estender expiração

### Dispositivos

- `POST /api/licenses/validate` - Validar chave de ativação

## Estrutura

```
license-service/
├── models/
│   ├── __init__.py
│   └── license.py          # Modelo License
├── routes/
│   ├── __init__.py
│   └── license.py          # Endpoints HTTP
├── services/
│   ├── __init__.py
│   ├── license_generator.py    # Geração de chaves
│   ├── license_service.py      # Lógica de negócio
│   └── license_validator.py    # Validação periódica (24h)
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py  # Autenticação JWT
├── main.py                 # Aplicação FastAPI
├── requirements.txt
└── README.md
```

## Banco de Dados

Schema: `license_schema`

Tabela: `licenses`
- `id` (UUID) - Identificador único
- `tenant_id` (UUID) - Tenant proprietário
- `activation_key` (String) - Chave em texto claro
- `activation_key_hash` (String) - Hash SHA256 da chave
- `plan_type` (Enum) - basic ou premium
- `device_limit` (Integer) - Limite de dispositivos
- `expires_at` (DateTime) - Data de expiração
- `activated_at` (DateTime) - Data de ativação
- `device_id` (UUID) - Dispositivo que ativou
- `status` (Enum) - pending, activated, revoked, expired
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Validação Periódica

O serviço executa validação automática de todas as licenças ativas a cada 24 horas:

1. Busca todas as licenças com status `activated`
2. Verifica se expirou (`expires_at < now()`)
3. Atualiza status para `expired` se necessário
4. Registra logs de licenças expiradas

## Requisitos Implementados

- **4.1**: Endpoints de gerenciamento de licenças
- **4.2**: Geração de chaves com 80 bits de entropia
- **4.3**: Modelo License com todos os campos
- **4.4**: Ativação de licença com dispositivo
- **4.5**: Validação online a cada 24 horas
- **4.7**: Revogação e extensão de licenças
- **37.3**: Isolamento por schema PostgreSQL

## Executar

```bash
cd services/license-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

## Variáveis de Ambiente

Ver `shared/config.py` para configurações globais:

- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`
- `LOG_LEVEL`, `DEBUG`
