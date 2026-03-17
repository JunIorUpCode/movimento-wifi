# Guia de Integração WebSocket no Frontend

## Visão Geral

Este guia mostra como integrar o WebSocket no frontend (admin-panel e client-panel) para receber eventos em tempo real.

## Passo 1: Copiar o Cliente WebSocket

Copie o arquivo `websocket_client_example.ts` para o seu projeto frontend:

```bash
# Para React (client-panel)
cp services/event-service/websocket_client_example.ts \
   frontend/client-panel/src/services/websocket.ts

# Para React (admin-panel)
cp services/event-service/websocket_client_example.ts \
   frontend/admin-panel/src/services/websocket.ts
```

## Passo 2: Criar Hook React

Crie um hook customizado para gerenciar o WebSocket:

```typescript
// frontend/client-panel/src/hooks/useWebSocket.ts

import { useEffect, useState, useCallback } from 'react';
import { WebSocketClient, EventData } from '../services/websocket';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<EventData[]>([]);
  const [client, setClient] = useState<WebSocketClient | null>(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem('jwt_token');
    
    if (!token) {
      console.error('JWT token não encontrado');
      return;
    }

    const wsClient = new WebSocketClient({
      url: import.meta.env.VITE_WS_URL || 'wss://api.wifisense.com/ws',
      token,
      onEvent: (event) => {
        setEvents(prev => [event, ...prev].slice(0, 100)); // Mantém últimos 100
      },
      onConnected: () => {
        setIsConnected(true);
      },
      onDisconnected: () => {
        setIsConnected(false);
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
      }
    });

    wsClient.connect();
    setClient(wsClient);
  }, []);

  const disconnect = useCallback(() => {
    if (client) {
      client.disconnect();
      setClient(null);
    }
  }, [client]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return { isConnected, events, connect, disconnect };
}
```

## Passo 3: Usar no Componente

### Exemplo: Dashboard com Eventos em Tempo Real

```typescript
// frontend/client-panel/src/pages/DashboardPage.tsx

import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { toast } from 'react-toastify';

export function DashboardPage() {
  const { isConnected, events } = useWebSocket();

  // Mostrar notificação quando novo evento chega
  React.useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[0];
      toast.info(`Novo evento: ${latestEvent.event_type}`, {
        position: 'top-right',
        autoClose: 5000
      });
    }
  }, [events]);

  return (
    <div className="dashboard">
      {/* Indicador de conexão */}
      <div className="connection-status">
        <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
        {isConnected ? 'Conectado' : 'Desconectado'}
      </div>

      {/* Lista de eventos em tempo real */}
      <div className="events-list">
        <h2>Eventos em Tempo Real</h2>
        {events.map(event => (
          <EventCard key={event.event_id} event={event} />
        ))}
      </div>
    </div>
  );
}
```

### Exemplo: Componente de Status de Conexão

```typescript
// frontend/client-panel/src/components/WebSocketStatus.tsx

import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export function WebSocketStatus() {
  const { isConnected } = useWebSocket();

  return (
    <div className="websocket-status">
      <div className={`status-indicator ${isConnected ? 'online' : 'offline'}`}>
        <span className="status-dot" />
        <span className="status-text">
          {isConnected ? 'Tempo Real Ativo' : 'Reconectando...'}
        </span>
      </div>
    </div>
  );
}
```

### CSS para Indicador de Status

```css
/* frontend/client-panel/src/styles/websocket.css */

.websocket-status {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-indicator.online .status-dot {
  background: #4caf50;
}

.status-indicator.offline .status-dot {
  background: #f44336;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
```

## Passo 4: Configurar Variáveis de Ambiente

Adicione a URL do WebSocket no arquivo `.env`:

```bash
# frontend/client-panel/.env

# Desenvolvimento
VITE_WS_URL=ws://localhost:8004/ws

# Produção
# VITE_WS_URL=wss://api.wifisense.com/ws
```

## Passo 5: Adicionar Notificações Toast

Instale react-toastify:

```bash
npm install react-toastify
```

Configure no App.tsx:

```typescript
// frontend/client-panel/src/App.tsx

import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <>
      <ToastContainer />
      {/* Resto da aplicação */}
    </>
  );
}
```

## Passo 6: Testar

1. Inicie o backend:
```bash
cd services/event-service
uvicorn main:app --reload --port 8004
```

2. Inicie o frontend:
```bash
cd frontend/client-panel
npm run dev
```

3. Faça login e observe:
   - Indicador de conexão deve mostrar "Conectado"
   - Quando um evento for detectado, deve aparecer na lista
   - Notificação toast deve aparecer

## Exemplo Completo: Context Provider

Para compartilhar o WebSocket em toda a aplicação:

```typescript
// frontend/client-panel/src/contexts/WebSocketContext.tsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { WebSocketClient, EventData } from '../services/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  events: EventData[];
  connect: () => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<EventData[]>([]);
  const [client, setClient] = useState<WebSocketClient | null>(null);

  const connect = () => {
    const token = localStorage.getItem('jwt_token');
    if (!token) return;

    const wsClient = new WebSocketClient({
      url: import.meta.env.VITE_WS_URL || 'wss://api.wifisense.com/ws',
      token,
      onEvent: (event) => {
        setEvents(prev => [event, ...prev].slice(0, 100));
      },
      onConnected: () => setIsConnected(true),
      onDisconnected: () => setIsConnected(false)
    });

    wsClient.connect();
    setClient(wsClient);
  };

  const disconnect = () => {
    client?.disconnect();
    setClient(null);
  };

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return (
    <WebSocketContext.Provider value={{ isConnected, events, connect, disconnect }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
}
```

Usar no App.tsx:

```typescript
import { WebSocketProvider } from './contexts/WebSocketContext';

function App() {
  return (
    <WebSocketProvider>
      {/* Resto da aplicação */}
    </WebSocketProvider>
  );
}
```

## Troubleshooting

### WebSocket não conecta
- Verificar se JWT token está válido
- Verificar URL do WebSocket (ws:// para dev, wss:// para prod)
- Verificar se event-service está rodando

### Eventos não aparecem
- Verificar se tenant_id do token corresponde aos eventos
- Verificar logs do backend
- Verificar se eventos têm confidence >= 0.7

### Reconexão não funciona
- Verificar console do browser para erros
- Verificar se exponential backoff está funcionando
- Verificar se token não expirou

## Conclusão

Com esta integração, o frontend receberá eventos em tempo real via WebSocket, proporcionando uma experiência de usuário mais responsiva e moderna.
