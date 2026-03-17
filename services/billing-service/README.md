# Billing Service - Serviço de Faturamento

Microserviço responsável por gerenciar cobranças, faturas e integração com Stripe para pagamentos.

## Funcionalidades

### ✅ Cálculo de Cobrança Mensal (Task 15.2)
- Calcula valor baseado em dispositivos ativos e tipo de plano
- **Plano BÁSICO**: R$ 29,90 por dispositivo/mês
- **Plano PREMIUM**: R$ 79,90 por dispositivo/mês
- **Descontos por volume**:
  - 10% para 3+ dispositivos
  - 20% para 10+ dispositivos

### ✅ Geração Automática de Faturas (Task 15.3)
- Job cron executado no dia 1 de cada mês às 00:00 UTC
- Gera faturas para todos os tenants ativos (exceto trial)
- Vencimento: 7 dias após geração
- Armazena detalhamento por dispositivo

### ✅ Integração com Stripe (Task 15.4)
- Criação/recuperação de clientes Stripe
- Processamento de pagamentos via PaymentIntent
- Gerenciamento de métodos de pagamento
- Rastreamento de transações

### ✅ Tratamento de Falhas de Pagamento (Task 15.5)
- Retry automático após 3 dias
- Máximo de 3 tentativas
- Suspensão de conta após 3 falhas consecutivas
- Notificação ao tenant (via email)

### ✅ Endpoints de Billing (Task 15.6)
- `GET /api/billing/subscription` - Informações da assinatura
- `POST /api/billing/upgrade` - Upgrade de plano
- `POST /api/billing/payment-method` - Atualizar método de pagamento
- `GET /api/billing/invoices` - Histórico de faturas
- `GET /api/billing/usage` - Estatísticas de uso

## Estrutura do Projeto

```
billing-service/
├── models/
│   ├── __init__.py
│   └── invoice.py              # Modelo de fatura
├── schemas/
│   ├── __init__.py
│   └── invoice.py              # Schemas Pydantic
├── services/
│   ├── __init__.py
│   ├── billing_service.py      # Cálculo de cobrança
│   ├── stripe_service.py       # Integração Stripe
│   └── invoice_generator.py   # Geração de faturas
├── routes/
│   ├── __init__.py
│   └── billing.py              # Endpoints da API
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py      # Autenticação JWT
├── main.py                     # Aplicação FastAPI
├── cron_jobs.py                # Jobs agendados
├── test_billing_service.py     # Testes unitários
├── requirements.txt
├── Dockerfile
└── README.md
```

## Modelos de Dados

### Invoice (Fatura)
```python
{
    "id": UUID,
    "tenant_id": UUID,
    "amount": Decimal,
    "status": "pending|paid|failed|refunded",
    "due_date": DateTime,
    "paid_at": DateTime (nullable),
    "stripe_invoice_id": String (nullable),
    "line_items": JSON,
    "payment_attempts": Integer,
    "created_at": DateTime,
    "updated_at": DateTime
}
```

## Endpoints da API

### GET /api/billing/subscription
Retorna informações da assinatura atual do tenant.

**Response:**
```json
{
    "tenant_id": "uuid",
    "plan_type": "basic|premium",
    "status": "trial|active|suspended|expired",
    "active_devices": 3,
    "device_limit": 100,
    "monthly_cost": 80.73,
    "next_billing_date": "2024-02-01T00:00:00Z",
    "trial_ends_at": null,
    "payment_method_configured": true
}
```

### POST /api/billing/upgrade
Faz upgrade do plano do tenant.

**Request:**
```json
{
    "new_plan": "premium"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Plano atualizado para premium",
    "new_plan": "premium"
}
```

### POST /api/billing/payment-method
Atualiza o método de pagamento do tenant.

**Request:**
```json
{
    "stripe_payment_method_id": "pm_1234567890",
    "set_as_default": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Método de pagamento atualizado com sucesso"
}
```

### GET /api/billing/invoices
Lista faturas do tenant com paginação.

**Query Parameters:**
- `page`: Número da página (default: 1)
- `page_size`: Itens por página (default: 20)

**Response:**
```json
{
    "invoices": [
        {
            "id": "uuid",
            "tenant_id": "uuid",
            "amount": 80.73,
            "status": "paid",
            "due_date": "2024-01-08T00:00:00Z",
            "paid_at": "2024-01-05T10:30:00Z",
            "stripe_invoice_id": "pi_1234567890",
            "line_items": [...],
            "payment_attempts": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-05T10:30:00Z"
        }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20
}
```

### GET /api/billing/usage
Retorna estatísticas de uso do tenant no período atual.

**Response:**
```json
{
    "tenant_id": "uuid",
    "current_period_start": "2024-01-01T00:00:00Z",
    "current_period_end": "2024-02-01T00:00:00Z",
    "active_devices": 3,
    "total_events": 1250,
    "total_notifications": 45,
    "estimated_cost": 80.73,
    "breakdown": [
        {
            "device_id": "uuid",
            "device_name": "Living Room",
            "plan": "basic",
            "price": 29.90
        }
    ]
}
```

## Cron Jobs

### Geração de Faturas Mensais
Executar no dia 1 de cada mês às 00:00 UTC:

```bash
python cron_jobs.py generate_invoices
```

**Configuração crontab:**
```
0 0 1 * * cd /app && python cron_jobs.py generate_invoices
```

### Retry de Pagamentos Falhados
Executar diariamente às 02:00 UTC:

```bash
python cron_jobs.py retry_payments
```

**Configuração crontab:**
```
0 2 * * * cd /app && python cron_jobs.py retry_payments
```

## Variáveis de Ambiente

```env
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wifisense

# Stripe
STRIPE_API_KEY=sk_test_...

# JWT
JWT_SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO
```

## Executar Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov

# Executar todos os testes
pytest test_billing_service.py -v

# Executar com cobertura
pytest test_billing_service.py --cov=services --cov-report=html
```

## Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar serviço
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

```bash
# Build
docker build -t billing-service .

# Run
docker run -p 8007:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e STRIPE_API_KEY=sk_test_... \
  billing-service
```

## Requisitos Implementados

- ✅ **5.7**: Preços por plano (BÁSICO R$ 29,90, PREMIUM R$ 79,90)
- ✅ **11.6**: Endpoints de billing para painel do cliente
- ✅ **17.1**: Cálculo de cobrança mensal baseado em dispositivos e plano
- ✅ **17.2**: Geração automática de faturas no dia 1 de cada mês
- ✅ **17.3**: Integração com Stripe para pagamentos
- ✅ **17.4**: Retry de pagamentos falhados após 3 dias
- ✅ **17.5**: Suspensão de conta após 3 falhas consecutivas
- ✅ **17.7**: Atualização de método de pagamento
- ✅ **17.8**: Descontos por volume (10% para 3+, 20% para 10+)

## Testes Implementados

- ✅ Cálculo de cobrança com diferentes quantidades de dispositivos
- ✅ Aplicação de descontos por volume
- ✅ Geração de faturas para tenants ativos
- ✅ Integração com Stripe (mocked)
- ✅ Tratamento de falhas de pagamento
- ✅ Suspensão de conta após 3 falhas

## Próximos Passos

1. Integrar com notification-service para enviar emails de falha de pagamento
2. Implementar webhooks do Stripe para receber eventos de pagamento
3. Adicionar suporte a cupons de desconto
4. Implementar relatórios de receita para administradores
5. Adicionar testes de integração end-to-end
