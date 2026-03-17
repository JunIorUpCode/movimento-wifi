/**
 * Testes unitários para a página DashboardPage.
 * 
 * Testa:
 * - Renderização de estatísticas
 * - Loading state
 * - Estado vazio (sem dispositivos)
 * - Exibição de dispositivos
 * - Exibição de eventos recentes
 */

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../../pages/DashboardPage'
import { devicesApi, eventsApi } from '../../services/api'
import type { Device, Event, DashboardStats } from '../../types'

// Mock dos módulos de API
vi.mock('../../services/api', () => ({
  devicesApi: {
    list: vi.fn(),
  },
  eventsApi: {
    stats: vi.fn(),
    timeline: vi.fn(),
  },
}))

// Dados mock
const mockDevices: Device[] = [
  {
    id: '1',
    name: 'Device 1',
    status: 'online',
    mac_address: 'AA:BB:CC:DD:EE:01',
    hardware_type: 'esp32',
    last_seen: new Date().toISOString(),
  },
  {
    id: '2',
    name: 'Device 2',
    status: 'offline',
    mac_address: 'AA:BB:CC:DD:EE:02',
    hardware_type: 'esp32',
    last_seen: new Date().toISOString(),
  },
]

const mockStats: DashboardStats = {
  events_today: 25,
  events_week: 150,
}

const mockEvents: Event[] = [
  {
    id: '1',
    device_id: '1',
    event_type: 'presence_detected',
    timestamp: new Date().toISOString(),
    signal_strength: -45,
  },
  {
    id: '2',
    device_id: '1',
    event_type: 'movement_detected',
    timestamp: new Date().toISOString(),
    signal_strength: -50,
  },
]

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

  it('deve exibir loading enquanto carrega dados', () => {
    vi.mocked(devicesApi.list).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(eventsApi.stats).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(eventsApi.timeline).mockImplementation(
      () => new Promise(() => {})
    )

    renderWithQueryClient(<DashboardPage />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('deve renderizar estatísticas corretamente', async () => {
    vi.mocked(devicesApi.list).mockResolvedValue(mockDevices)
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    expect(screen.getByText('Visão geral dos seus dispositivos e eventos')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Dispositivos Online')).toBeInTheDocument()
    })

    expect(screen.getByText('1/2')).toBeInTheDocument()
    expect(screen.getByText('Eventos Hoje')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
    expect(screen.getByText('Eventos Esta Semana')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('deve exibir mensagem quando não há dispositivos', async () => {
    vi.mocked(devicesApi.list).mockResolvedValue([])
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue([])

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Nenhum dispositivo registrado')).toBeInTheDocument()
    })

    expect(screen.getByText('Registre seu primeiro dispositivo para começar a monitorar')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /registrar dispositivo/i })).toBeInTheDocument()
  })

  it('deve exibir lista de dispositivos', async () => {
    vi.mocked(devicesApi.list).mockResolvedValue(mockDevices)
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Meus Dispositivos')).toBeInTheDocument()
    })

    expect(screen.getByText('Device 1')).toBeInTheDocument()
    expect(screen.getByText('Device 2')).toBeInTheDocument()
  })

  it('deve exibir nota sobre WebSocket quando há dispositivos online', async () => {
    vi.mocked(devicesApi.list).mockResolvedValue(mockDevices)
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText(/Atualização em tempo real ativa/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Os dados são atualizados automaticamente via WebSocket/i)).toBeInTheDocument()
  })

  it('não deve exibir nota sobre WebSocket quando não há dispositivos online', async () => {
    const offlineDevices = mockDevices.map(d => ({ ...d, status: 'offline' as const }))
    
    vi.mocked(devicesApi.list).mockResolvedValue(offlineDevices)
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue([])

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Device 1')).toBeInTheDocument()
    })

    expect(screen.queryByText(/Atualização em tempo real ativa/i)).not.toBeInTheDocument()
  })

  it('deve calcular corretamente dispositivos online', async () => {
    const mixedDevices = [
      { ...mockDevices[0], status: 'online' as const },
      { ...mockDevices[1], status: 'online' as const },
    ]
    
    vi.mocked(devicesApi.list).mockResolvedValue(mixedDevices)
    vi.mocked(eventsApi.stats).mockResolvedValue(mockStats)
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('2/2')).toBeInTheDocument()
    })
  })

  it('deve exibir 0 para estatísticas quando não há dados', async () => {
    vi.mocked(devicesApi.list).mockResolvedValue([])
    vi.mocked(eventsApi.stats).mockResolvedValue({
      events_today: 0,
      events_week: 0,
    })
    vi.mocked(eventsApi.timeline).mockResolvedValue([])

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('0/0')).toBeInTheDocument()
    })

    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
  })
})
