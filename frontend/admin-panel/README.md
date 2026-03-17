# WiFiSense - Painel Administrativo

Painel administrativo React + TypeScript para gerenciamento da plataforma WiFiSense SaaS.

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
admin-panel/
├── src/
│   ├── components/      # Componentes reutilizáveis
│   │   ├── Layout.tsx
│   │   └── RequireAuth.tsx
│   ├── hooks/           # Custom hooks
│   │   └── useAuth.ts
│   ├── pages/           # Páginas da aplicação
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TenantsPage.tsx
│   │   ├── LicensesPage.tsx
│   │   ├── DevicesPage.tsx
│   │   └── AuditLogsPage.tsx
│   ├── services/        # Serviços de API
│   │   └── api.ts
│   ├── types/           # Definições TypeScript
│   │   └── index.ts
│   ├── App.tsx          # Componente raiz
│   ├── main.tsx         # Entry point
│   └── index.css        # Estilos globais
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## Instalação

```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento (porta 5174)
npm run dev

# Build para produção
npm run build

# Preview do build de produção
npm run preview
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
VITE_API_URL=http://localhost:8000/api
```

### Proxy de Desenvolvimento

O Vite está configurado para fazer proxy das requisições:
- `/api` → `http://localhost:8000`
- `/ws` → `ws://localhost:8000`

## Funcionalidades Implementadas

### ✅ Subtarefa 12.1 - Configuração do Projeto
- [x] Estrutura de pastas (components/, pages/, hooks/, services/)
- [x] TanStack Query configurado
- [x] Tailwind CSS configurado
- [x] React Router configurado

### ✅ Subtarefa 12.2 - Autenticação
- [x] Página de login com email/senha
- [x] Armazenamento de JWT token no localStorage
- [x] Hook useAuth() para gerenciar autenticação
- [x] Componente RequireAuth para proteger rotas

### ✅ Subtarefa 12.3 - Dashboard (Parcial)
- [x] Estrutura básica do dashboard
- [x] Cards de métricas globais
- [x] Métricas de sistema (CPU, memória)
- [x] Polling a cada 30 segundos
- [ ] Gráficos de eventos por hora (Recharts) - TODO

### 🚧 Subtarefa 12.4 - Gerenciamento de Tenants
- [ ] Página de listagem de tenants
- [ ] Filtros (status, plano)
- [ ] Formulário de criação
- [ ] Ações: suspender, ativar, deletar

### 🚧 Subtarefa 12.5 - Gerenciamento de Licenças
- [ ] Página de listagem de licenças
- [ ] Formulário de geração
- [ ] Copiar activation_key para clipboard
- [ ] Ações: revogar, estender

### 🚧 Subtarefa 12.6 - Monitoramento de Dispositivos
- [ ] Listagem de dispositivos
- [ ] Filtros por tenant, status, plano
- [ ] Métricas de saúde
- [ ] Indicador de last_seen

### 🚧 Subtarefa 12.7 - Audit Logs
- [ ] Página de logs
- [ ] Filtros (ação, recurso, data)
- [ ] Paginação e busca

### 🚧 Subtarefa 12.8 - Testes Unitários (OPCIONAL)
- [ ] Testes de componentes
- [ ] Testes de hooks
- [ ] Testes de integração com API

## Autenticação

O painel administrativo usa autenticação JWT:

1. Login via POST `/api/auth/login`
2. Token armazenado no localStorage
3. Token incluído automaticamente em todas as requisições
4. Verificação de role `admin` obrigatória

## API Endpoints

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

### Tenants
- `GET /api/admin/tenants` - Listar tenants
- `POST /api/admin/tenants` - Criar tenant
- `PUT /api/admin/tenants/:id` - Atualizar tenant
- `DELETE /api/admin/tenants/:id` - Deletar tenant
- `POST /api/admin/tenants/:id/suspend` - Suspender
- `POST /api/admin/tenants/:id/activate` - Ativar

### Licenças
- `GET /api/admin/licenses` - Listar licenças
- `POST /api/admin/licenses` - Gerar licença
- `PUT /api/admin/licenses/:id/revoke` - Revogar
- `PUT /api/admin/licenses/:id/extend` - Estender

### Dispositivos
- `GET /api/devices` - Listar dispositivos
- `GET /api/devices/:id` - Detalhes
- `GET /api/devices/:id/status` - Status em tempo real

### Audit Logs
- `GET /api/audit-logs` - Listar logs

### Métricas
- `GET /api/metrics` - Métricas do sistema

## Próximos Passos

1. Implementar gráficos com Recharts no dashboard
2. Implementar página completa de gerenciamento de tenants
3. Implementar página completa de gerenciamento de licenças
4. Implementar página completa de monitoramento de dispositivos
5. Implementar página completa de audit logs
6. Adicionar testes unitários (opcional)

## Notas de Desenvolvimento

- Todo código está 100% comentado em português
- Seguindo padrões de clean code
- Componentes reutilizáveis e modulares
- Tipagem forte com TypeScript
- Tratamento de erros centralizado
- Loading states e feedback visual
