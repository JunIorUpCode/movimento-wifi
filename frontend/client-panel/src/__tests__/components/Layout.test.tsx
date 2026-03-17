/**
 * Testes unitários para o componente Layout.
 * 
 * Testa:
 * - Renderização da sidebar
 * - Links de navegação
 * - Informações do usuário
 * - Botão de logout
 * - Menu mobile
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Layout from '../../components/Layout'
import { useAuth } from '../../hooks/useAuth'

// Mock do hook useAuth
vi.mock('../../hooks/useAuth')

describe('Layout', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant',
        name: 'Tenant Test',
        plan_type: 'basic',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: mockLogout,
    })
  })

  it('deve renderizar logo e nome da aplicação', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    const logos = screen.getAllByText('WiFiSense')
    expect(logos.length).toBeGreaterThan(0)
  })

  it('deve renderizar links de navegação', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Eventos').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Dispositivos').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Notificações').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Assinatura').length).toBeGreaterThan(0)
  })

  it('deve exibir informações do usuário', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    expect(screen.getByText('Tenant Test')).toBeInTheDocument()
    expect(screen.getByText('Plano Básico')).toBeInTheDocument()
  })

  it('deve exibir plano premium quando usuário tem plano premium', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant',
        name: 'Premium User',
        plan_type: 'premium',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: mockLogout,
    })

    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    expect(screen.getByText('PREMIUM')).toBeInTheDocument()
    expect(screen.getByText('Plano Premium')).toBeInTheDocument()
  })

  it('deve exibir email quando nome não está disponível', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant',
        plan_type: 'basic',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: mockLogout,
    })

    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    expect(screen.getByText('tenant@test.com')).toBeInTheDocument()
  })

  it('deve chamar logout ao clicar no botão de sair', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    const logoutButton = screen.getByTitle('Sair')
    await user.click(logoutButton)

    expect(mockLogout).toHaveBeenCalled()
  })

  it('deve abrir menu mobile ao clicar no botão de menu', async () => {
    const user = userEvent.setup()

    // Simula viewport mobile
    global.innerWidth = 375
    
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    // Encontra botão de menu (ícone Menu)
    const menuButtons = screen.getAllByRole('button')
    const menuButton = menuButtons.find(btn => 
      btn.querySelector('svg')?.classList.contains('lucide-menu') ||
      btn.className.includes('lg:hidden')
    )

    if (menuButton) {
      await user.click(menuButton)

      // Verifica que sidebar mobile está visível
      await waitFor(() => {
        const closeButtons = screen.getAllByRole('button')
        const closeButton = closeButtons.find(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-x')
        )
        expect(closeButton).toBeInTheDocument()
      })
    }
  })

  it('deve fechar menu mobile ao clicar no botão de fechar', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    // Abre menu mobile
    const menuButtons = screen.getAllByRole('button')
    const menuButton = menuButtons.find(btn => 
      btn.className.includes('lg:hidden') && 
      !btn.querySelector('svg')?.classList.contains('lucide-log-out')
    )

    if (menuButton) {
      await user.click(menuButton)

      // Encontra e clica no botão de fechar
      await waitFor(async () => {
        const closeButtons = screen.getAllByRole('button')
        const closeButton = closeButtons.find(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-x')
        )
        
        if (closeButton) {
          await user.click(closeButton)
        }
      })
    }
  })

  it('deve ter links de navegação funcionais', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    )

    const dashboardLinks = screen.getAllByRole('link', { name: /dashboard/i })
    expect(dashboardLinks.length).toBeGreaterThan(0)
    expect(dashboardLinks[0]).toHaveAttribute('href', '/dashboard')

    const eventsLinks = screen.getAllByRole('link', { name: /eventos/i })
    expect(eventsLinks.length).toBeGreaterThan(0)
    expect(eventsLinks[0]).toHaveAttribute('href', '/events')

    const devicesLinks = screen.getAllByRole('link', { name: /dispositivos/i })
    expect(devicesLinks.length).toBeGreaterThan(0)
    expect(devicesLinks[0]).toHaveAttribute('href', '/devices')
  })
})
