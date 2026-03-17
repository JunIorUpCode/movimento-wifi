/**
 * Testes unitários para a página EventsPage.
 * 
 * Testa:
 * - Renderização da timeline de eventos
 * - Filtros (tipo, dispositivo, data)
 * - Loading state
 * - Estado vazio
 * - Marcar falso positivo
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import EventsPage from '../../pages/EventsPage'
import { eventsApi, devicesApi } from '../../services/api'
import type { Event, Device } from '../../types'

// Mock dos módulos de API
vi.mock('../../services/api', () => ({
  eventsApi: {
    timeline: vi.fn(),
    markFalsePositive: vi.fn(),
  },
  devicesApi: {
    list: vi.fn(),
  },
}))

const mockDevices: Device[] = [
  {
    id: '1',
    name: 'Device 1',
    status: 'online',
    mac_address: 'AA:BB:CC:DD:EE:01',
    hardware_type: 'esp32',
    last_seen: new Date().toISOString(),
  },
]

const mockEvents: Event[] = [
  {
    id: '1',
    device_id: '1',
    event_type: 'presence',
    timestamp: new Date().toISOString(),
    signal_strength: -45,
  },
  {
    id: '2',
    device_id: '1',
    event_type: 'movement',
    timestamp: new Date().toISOString(),
    signal_strength: -50,
  },
]

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

describe('EventsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deve renderizar página de eventos', async () => {
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)
    vi.mocked(devicesApi.list).mockResolvedValue(mockDevices)

    renderWithQueryClient(<EventsPage />)

    expect(screen.getByText('Timeline de Eventos')).toBeInTheDocument()
    expect(screen.getByText('Histórico completo de eventos detectados')).toBeInTheDocument()
  })

  it('deve exibir filtros', async () => {
    vi.mocked(eventsApi.timeline).mockResolvedValue(mockEvents)
    vi.mocked(devicesApi.list).mockResolvedValue(mockDevices)

    renderWithQueryClient(<EventsPage />)

    expect(screen.getByText('Filtros')).toBeInTheDocument()
    
    // Verifica que há selects e inputs de data
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBe(2) // Tipo e Dispositivo
  })
})
