# WiFiSense Client Panel

Painel do cliente para a plataforma WiFiSense SaaS. Interface React para tenants visualizarem seus dispositivos, eventos e configurações.

## Tecnologias

- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **TanStack Query** - Gerenciamento de estado do servidor
- **React Router** - Roteamento
- **Tailwind CSS** - Estilização
- **Recharts** - Gráficos e visualizações
- **Lucide React** - Ícones

## Estrutura do Projeto

```
src/
├── components/       # Componentes reutilizáveis
│   ├── Layout.tsx
│   └── RequireAuth.tsx
├── hooks/           # Custom hooks
│   └── useAuth.ts
├── pages/           # Páginas da aplicação
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── EventsPage.tsx
│   ├── DevicesPage.tsx
│   ├── NotificationsPage.tsx
│   └── SubscriptionPage.tsx
├── services/        # Serviços de API
│   └── api.ts
├── types/           # Definições TypeScript
│   └── index.ts
├── App.tsx          # Componente raiz
├── main.tsx         # Ponto de entrada
└── index.css        # Estilos globais
```

## Funcionalidades

### Autenticação
- Login com email/senha
- JWT token armazenado no localStorage
- Proteção de rotas
- Logout

### Dashboard
- Status de todos os dispositivos (online/offline, last_seen)
- Gráficos de signal strength em tempo real
- Indicadores visuais de eventos recentes
- Atualização em tempo real via WebSocket

### Timeline de Eventos
- Listagem de eventos com timestamps, tipos, confidence
- Filtros por tipo, data, dispositivo
- Paginação infinita (scroll)
- Marcar falso positivo

### Gerenciamento de Dispositivos
- Listagem de dispositivos do tenant
- Formulário de registro (activation_key)
- Renomear, configurar, remover dispositivo
- Visualização de hardware_info e métricas de saúde

### Configuração de Notificações
- Configurar canais (Telegram, email, webhook)
- Wizard para criar bot Telegram
- Configurar min_confidence, quiet_hours, cooldown
- Testar canais
- Logs de notificações recentes

### Assinatura e Billing
- Exibir plano atual (BÁSICO/PREMIUM)
- Próxima data de cobrança e valor
- Upgrade de plano
- Histórico de faturas

## Desenvolvimento

### Pré-requisitos

- Node.js 18+
- npm ou yarn

### Instalação

```bash
# Instalar dependências
npm install

# Copiar arquivo de ambiente
cp .env.example .env
```

### Executar em Desenvolvimento

```bash
npm run dev
```

Acesse: http://localhost:5173

### Build para Produção

```bash
npm run build
```

Os arquivos otimizados serão gerados em `dist/`.

### Testes

```bash
# Executar testes
npm test

# Executar testes em modo watch
npm run test:watch

# Gerar relatório de cobertura
npm run test:coverage
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` baseado em `.env.example`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### API Backend

O painel se comunica com o backend via:
- **REST API**: `/api/*`
- **WebSocket**: `/ws`

Todas as requisições incluem JWT token no header `Authorization: Bearer <token>`.

## Autenticação

### Fluxo de Login

1. Usuário envia email/senha para `/api/auth/login`
2. Backend valida credenciais e retorna JWT token
3. Token é armazenado no localStorage
4. Token é incluído em todas as requisições subsequentes
5. Middleware `RequireAuth` protege rotas privadas

### Armazenamento

- **Token JWT**: `localStorage.getItem('auth_token')`
- **Dados do usuário**: `localStorage.getItem('auth_user')`

## Componentes Principais

### Layout
Estrutura base com sidebar, header e área de conteúdo.

### RequireAuth
Componente de proteção de rotas que verifica autenticação.

### useAuth Hook
Hook personalizado para gerenciar estado de autenticação.

## Estilização

### Tailwind CSS

Classes utilitárias personalizadas definidas em `index.css`:

- `.btn` - Botões base
- `.btn-primary` - Botão primário
- `.btn-secondary` - Botão secundário
- `.btn-danger` - Botão de perigo
- `.card` - Card container
- `.input` - Input de formulário
- `.label` - Label de formulário
- `.badge` - Badge/tag
- `.badge-success` - Badge verde
- `.badge-warning` - Badge amarelo
- `.badge-danger` - Badge vermelho
- `.badge-info` - Badge azul

### Cores

Paleta de cores primárias (verde):
- 50-900: Tons de verde para plano BÁSICO/PREMIUM

## Integração com Backend

### Endpoints Utilizados

```typescript
// Autenticação
POST /api/auth/login
POST /api/auth/logout

// Dispositivos
GET /api/devices
POST /api/devices/register
GET /api/devices/{id}
PUT /api/devices/{id}
DELETE /api/devices/{id}

// Eventos
GET /api/events
GET /api/events/timeline
GET /api/events/stats
POST /api/events/{id}/feedback

// Notificações
GET /api/notifications/config
PUT /api/notifications/config
POST /api/notifications/test
GET /api/notifications/logs

// Billing
GET /api/billing/subscription
POST /api/billing/upgrade
GET /api/billing/invoices
```

### WebSocket

Conexão WebSocket para atualizações em tempo real:

```typescript
const ws = new WebSocket('ws://localhost:8000/ws?token=<jwt>')

ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  // Processar eventos, status de dispositivos, etc.
}
```

## Licença

Propriedade de WiFiSense. Todos os direitos reservados.
