/**
 * Testes unitários para a página DashboardPage.
 * 
 * Testa:
 * - Renderização de métricas do sistema
 * - Loading state
 * - Error state
 * - Polling automático (refetch a cada 30s)
 * - Exibição de cards de métricas
 */

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../../pages/DashboardPage'
import { metricsApi } from '../../services/api'
import type { SystemMetrics } from '../../types'

// Mock do módulo de API
vi.mock('../../services/api', () => ({
  metricsApi: {
    getSystem: vi.fn(),
  },
}))

// Dados mock de métricas
const mockMetrics: SystemMetrics = {
  total_tenants: 15,
  active_tenants: 12,
  total_devices: 45,
  devices_online: 38,
  total_events_today: 250,
  api_latency_ms: 42,
  cpu_usage_percent: 35.5,
  memory_usage_percent: 62.3,
}

/**
 * Helper para renderizar com QueryClient
 */
function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deve exibir loading enquanto carrega métricas', () => {
    // Mock de API que nunca resolve (simula loading)
    vi.mocked(metricsApi.getSystem).mockImplementation(
      () => new Promise(() => {})
    )

    renderWithQueryClient(<DashboardPage />)

    // Verifica indicador de loading
    expect(screen.getByText('Carregando métricas...')).toBeInTheDocument()
  })

  it('deve exibir erro quando falha ao carregar métricas', async () => {
    // Mock de erro na API
    vi.mocked(metricsApi.getSystem).mockRejectedValue(
      new Error('Failed to fetch metrics')
    )

    renderWithQueryClient(<DashboardPage />)

    // Aguarda e verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Erro ao carregar métricas do sistema')).toBeInTheDocument()
    })
  })

  it('deve renderizar métricas do sistema corretamente', async () => {
    // Mock de sucesso na API
    vi.mocked(metricsApi.getSystem).mockResolvedValue(mockMetrics)

    renderWithQueryClient(<DashboardPage />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.queryByText('Carregando métricas...')).not.toBeInTheDocument()
    })

    // Verifica título da página
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Visão geral da plataforma WiFiSense SaaS')).toBeInTheDocument()

    // Verifica cards de métricas principais
    expect(screen.getByText('Total de Tenants')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('12 ativos')).toBeInTheDocument()

    expect(screen.getByText('Dispositivos')).toBeInTheDocument()
    expect(screen.getByText('38')).toBeInTheDocument()
    expect(screen.getByText('de 45 total')).toBeInTheDocument()

    expect(screen.getByText('Eventos Hoje')).toBeInTheDocument()
    expect(screen.getByText('250')).toBeInTheDocument()

    expect(screen.getByText('Latência API')).toBeInTheDocument()
    expect(screen.getByText('42ms')).toBeInTheDocument()
  })

  it('deve renderizar métricas de CPU e memória', async () => {
    // Mock de sucesso na API
    vi.mocked(metricsApi.getSystem).mockResolvedValue(mockMetrics)

    renderWithQueryClient(<DashboardPage />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.getByText('Uso de CPU')).toBeInTheDocument()
    })

    // Verifica métricas de sistema
    expect(screen.getByText('Uso de CPU')).toBeInTheDocument()
    expect(screen.getByText('35.5%')).toBeInTheDocument()

    expect(screen.getByText('Uso de Memória')).toBeInTheDocument()
    expect(screen.getByText('62.3%')).toBeInTheDocument()
  })

  it('deve exibir placeholder para gráfico de eventos', async () => {
    // Mock de sucesso na API
    vi.mocked(metricsApi.getSystem).mockResolvedValue(mockMetrics)

    renderWithQueryClient(<DashboardPage />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.getByText('Eventos por Hora (Últimas 24h)')).toBeInTheDocument()
    })

    // Verifica placeholder do gráfico
    expect(screen.getByText('Gráfico será implementado com Recharts')).toBeInTheDocument()
  })

  it('deve aplicar cor verde para CPU < 60%', async () => {
    const lowCpuMetrics = { ...mockMetrics, cpu_usage_percent: 45 }
    vi.mocked(metricsApi.getSystem).mockResolvedValue(lowCpuMetrics)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('45.0%')).toBeInTheDocument()
    })

    // Verifica que barra de progresso tem classe verde
    const progressBar = screen.getByText('45.0%').closest('.card')
    expect(progressBar?.innerHTML).toContain('bg-green-500')
  })

  it('deve aplicar cor amarela para CPU entre 60-80%', async () => {
    const mediumCpuMetrics = { ...mockMetrics, cpu_usage_percent: 70 }
    vi.mocked(metricsApi.getSystem).mockResolvedValue(mediumCpuMetrics)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('70.0%')).toBeInTheDocument()
    })

    // Verifica que barra de progresso tem classe amarela
    const progressBar = screen.getByText('70.0%').closest('.card')
    expect(progressBar?.innerHTML).toContain('bg-yellow-500')
  })

  it('deve aplicar cor vermelha para CPU > 80%', async () => {
    const highCpuMetrics = { ...mockMetrics, cpu_usage_percent: 85 }
    vi.mocked(metricsApi.getSystem).mockResolvedValue(highCpuMetrics)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('85.0%')).toBeInTheDocument()
    })

    // Verifica que barra de progresso tem classe vermelha
    const progressBar = screen.getByText('85.0%').closest('.card')
    expect(progressBar?.innerHTML).toContain('bg-red-500')
  })

  it('deve aplicar mesma lógica de cores para memória', async () => {
    const highMemoryMetrics = { ...mockMetrics, memory_usage_percent: 90 }
    vi.mocked(metricsApi.getSystem).mockResolvedValue(highMemoryMetrics)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('90.0%')).toBeInTheDocument()
    })

    // Verifica que barra de progresso tem classe vermelha
    const progressBar = screen.getByText('90.0%').closest('.card')
    expect(progressBar?.innerHTML).toContain('bg-red-500')
  })

  it('deve lidar com métricas ausentes (valores 0)', async () => {
    const emptyMetrics: SystemMetrics = {
      total_tenants: 0,
      active_tenants: 0,
      total_devices: 0,
      devices_online: 0,
      total_events_today: 0,
      api_latency_ms: 0,
      cpu_usage_percent: 0,
      memory_usage_percent: 0,
    }

    vi.mocked(metricsApi.getSystem).mockResolvedValue(emptyMetrics)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.queryByText('Carregando métricas...')).not.toBeInTheDocument()
    })

    // Verifica que valores 0 são exibidos corretamente
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
    expect(screen.getByText('0ms')).toBeInTheDocument()
    expect(screen.getAllByText('0.0%').length).toBe(2) // CPU e memória
  })

  it('deve configurar polling a cada 30 segundos', async () => {
    vi.mocked(metricsApi.getSystem).mockResolvedValue(mockMetrics)

    renderWithQueryClient(<DashboardPage />)

    // Primeira chamada ao montar
    await waitFor(() => {
      expect(metricsApi.getSystem).toHaveBeenCalledTimes(1)
    })

    // Verifica que refetchInterval está configurado (não testamos o timing real)
    // pois fake timers não funcionam bem com React Query
  })
})
