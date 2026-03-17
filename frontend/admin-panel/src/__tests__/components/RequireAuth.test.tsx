/**
 * Testes unitários para o componente RequireAuth.
 * 
 * Testa:
 * - Redirecionamento para login quando não autenticado
 * - Renderização de rotas filhas quando autenticado
 * - Exibição de loading durante verificação
 */

import { render, screen } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import RequireAuth from '../../components/RequireAuth'
import { useAuth } from '../../hooks/useAuth'

// Mock do hook useAuth
vi.mock('../../hooks/useAuth')

describe('RequireAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deve exibir loading enquanto verifica autenticação', () => {
    // Mock de estado loading
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Deve exibir indicador de loading
    expect(screen.getByText('Carregando...')).toBeInTheDocument()
    
    // Não deve exibir conteúdo protegido
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('deve redirecionar para /login quando não autenticado', () => {
    // Mock de estado não autenticado
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Deve redirecionar para login
    expect(screen.getByText('Login Page')).toBeInTheDocument()
    
    // Não deve exibir conteúdo protegido
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('deve renderizar rotas filhas quando autenticado', async () => {
    // Mock de estado autenticado
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
      logout: vi.fn(),
    })

    render(
      <BrowserRouter initialEntries={['/']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Aguarda renderização
    await screen.findByText('Protected Content')

    // Deve renderizar conteúdo protegido
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    
    // Não deve exibir página de login
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })

  it('deve renderizar múltiplas rotas filhas', async () => {
    // Mock de estado autenticado
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
      logout: vi.fn(),
    })

    render(
      <BrowserRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/dashboard" element={<div>Dashboard Page</div>} />
            <Route path="/tenants" element={<div>Tenants Page</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    )

    // Aguarda renderização
    await screen.findByText('Dashboard Page')

    // Deve renderizar a rota correspondente
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
  })
})
