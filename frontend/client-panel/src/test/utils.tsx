/**
 * Utilitários para testes.
 * 
 * Fornece wrappers customizados para renderizar componentes
 * com providers necessários (Router, QueryClient, etc).
 */

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Cria um novo QueryClient para testes
 * com configurações que desabilitam retries e logs
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })
}

/**
 * Wrapper com todos os providers necessários
 */
interface AllProvidersProps {
  children: React.ReactNode
  queryClient?: QueryClient
}

function AllProviders({ children, queryClient }: AllProvidersProps) {
  const client = queryClient || createTestQueryClient()

  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

/**
 * Renderiza componente com todos os providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient, ...renderOptions } = options || {}

  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders queryClient={queryClient}>
        {children}
      </AllProviders>
    ),
    ...renderOptions,
  })
}

/**
 * Mock de resposta fetch bem-sucedida
 */
export function mockFetchSuccess<T>(data: T) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: async () => data,
  })
}

/**
 * Mock de resposta fetch com erro
 */
export function mockFetchError(status: number, code: string, message: string) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({
      error: {
        code,
        message,
      },
    }),
  })
}

/**
 * Aguarda até que uma condição seja verdadeira
 */
export async function waitFor(
  callback: () => boolean | Promise<boolean>,
  timeout = 1000
): Promise<void> {
  const startTime = Date.now()
  
  while (Date.now() - startTime < timeout) {
    if (await callback()) {
      return
    }
    await new Promise(resolve => setTimeout(resolve, 50))
  }
  
  throw new Error('Timeout waiting for condition')
}
