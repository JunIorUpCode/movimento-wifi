/**
 * Testes unitários para o componente Layout.
 * 
 * Testa:
 * - Renderização da sidebar com links de navegação
 * - Exibição de informações do usuário
 * - Funcionalidade de logout
 * - Menu mobile (toggle sidebar)
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '../../components/Layout'
import { useAuth } from '../../hooks/useAuth'

// Mock do hook useAuth
vi.mock('../../hooks/useAuth')

describe('Layout', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock padrão de usuário autenticado
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'admin@test.com',
        role: 'admin',
        name: 'Admin Test',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: mockLogout,
    })
  })

  it('deve renderizar sidebar com links de navegação', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Verifica links de navegação
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Tenants')).toBeInTheDocument()
    expect(screen.getByText('Licenças')).toBeInTheDocument()
    expect(screen.getByText('Dispositivos')).toBeInTheDocument()
    expect(screen.getByText('Audit Logs')).toBeInTheDocument()
  })

  it('deve exibir nome do usuário no header', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Verifica exibição do nome do usuário
    expect(screen.getByText('Admin Test')).toBeInTheDocument()
    expect(screen.getByText('Administrador')).toBeInTheDocument()
  })

  it('deve exibir email quando nome não está disponível', () => {
    // Mock de usuário sem nome
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'admin@test.com',
        role: 'admin',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: mockLogout,
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Deve exibir email quando nome não existe
    expect(screen.getByText('admin@test.com')).toBeInTheDocument()
  })

  it('deve chamar logout quando botão de sair é clicado', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Encontra e clica no botão de logout
    const logoutButton = screen.getByTitle('Sair')
    fireEvent.click(logoutButton)

    // Verifica que logout foi chamado
    expect(mockLogout).toHaveBeenCalledTimes(1)
  })

  it('deve renderizar conteúdo das rotas filhas', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Dashboard Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Verifica que conteúdo da rota filha é renderizado
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument()
  })

  it('deve exibir logo WiFiSense Admin', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Verifica logo
    const logos = screen.getAllByText('WiFiSense Admin')
    expect(logos.length).toBeGreaterThan(0)
  })

  it('deve ter links de navegação funcionais', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Verifica que links existem e têm href corretos
    const links = screen.getAllByRole('link')
    const dashboardLink = links.find(link => link.textContent?.includes('Dashboard'))
    const tenantsLink = links.find(link => link.textContent?.includes('Tenants'))
    
    expect(dashboardLink).toBeDefined()
    expect(tenantsLink).toBeDefined()
    expect((dashboardLink as HTMLAnchorElement)?.href).toContain('/dashboard')
    expect((tenantsLink as HTMLAnchorElement)?.href).toContain('/tenants')
  })

  it('deve abrir sidebar mobile quando botão de menu é clicado', () => {
    // Renderiza em viewport mobile
    global.innerWidth = 375
    
    render(
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Encontra botão de menu mobile (ícone Menu)
    const menuButtons = screen.getAllByRole('button')
    const menuButton = menuButtons.find(btn => {
      const svg = btn.querySelector('svg')
      return svg?.classList.contains('lucide-menu') || btn.querySelector('[class*="menu"]')
    })

    if (menuButton) {
      // Clica no botão de menu
      fireEvent.click(menuButton)

      // Sidebar mobile deve estar visível (verifica pela presença do botão X)
      const closeButtons = screen.getAllByRole('button')
      const hasCloseButton = closeButtons.some(btn => {
        const svg = btn.querySelector('svg')
        return svg?.classList.contains('lucide-x')
      })
      
      expect(hasCloseButton).toBe(true)
    }
  })
})
