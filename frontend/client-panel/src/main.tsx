/**
 * Ponto de entrada principal do painel do cliente WiFiSense.
 * 
 * Configura:
 * - React Query para gerenciamento de estado do servidor
 * - React Router para navegação
 * - Estilos globais com Tailwind CSS
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// Configuração do React Query
// staleTime: 5 minutos - dados considerados frescos por 5 min
// gcTime: 10 minutos - dados mantidos em cache por 10 min
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
