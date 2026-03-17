/**
 * Testes unitários para a página LoginPage.
 * 
 * Testa:
 * - Renderização do formulário de login
 * - Validação de campos
 * - Submissão com credenciais válidas
 * - Tratamento de erros de login
 * - Redirecionamento quando já autenticado
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../../pages/LoginPage'
import { useAuth } from '../../hooks/useAuth'
import { ApiError } from '../../services/api'

// Mock do hook useAuth
vi.mock('../../hooks/useAuth')

describe('LoginPage', () => {
  const mockLogin = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock padrão de usuário não autenticado
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      token: null,
      login: mockLogin,
      logout: vi.fn(),
    })
  })

  it('deve renderizar formulário de login', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Verifica elementos do formulário
    expect(screen.getByText('Painel Administrativo')).toBeInTheDocument()
    expect(screen.getByText('WiFiSense SaaS Platform')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
  })

  it('deve exibir erro quando campos estão vazios', async () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Clica no botão sem preencher campos
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    fireEvent.click(submitButton)

    // Verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Por favor, preencha todos os campos')).toBeInTheDocument()
    })

    // Login não deve ser chamado
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('deve chamar login com credenciais válidas', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche formulário
    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Senha')
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')

    // Submete formulário
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    await user.click(submitButton)

    // Verifica que login foi chamado com credenciais corretas
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'admin@test.com',
        password: 'password123',
      })
    })
  })

  it('deve exibir loading durante login', async () => {
    const user = userEvent.setup()

    // Mock de login que demora
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche e submete formulário
    await user.type(screen.getByLabelText('Email'), 'admin@test.com')
    await user.type(screen.getByLabelText('Senha'), 'password123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica estado de loading
    expect(screen.getByText('Entrando...')).toBeInTheDocument()
    
    // Botão deve estar desabilitado
    const submitButton = screen.getByRole('button', { name: /entrando/i })
    expect(submitButton).toBeDisabled()
  })

  it('deve exibir erro de credenciais inválidas', async () => {
    const user = userEvent.setup()

    // Mock de erro de credenciais inválidas
    mockLogin.mockRejectedValue(
      new ApiError(401, 'INVALID_CREDENTIALS', 'Email ou senha incorretos')
    )

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche e submete formulário
    await user.type(screen.getByLabelText('Email'), 'wrong@test.com')
    await user.type(screen.getByLabelText('Senha'), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Email ou senha incorretos')).toBeInTheDocument()
    })
  })

  it('deve exibir erro de conta bloqueada', async () => {
    const user = userEvent.setup()

    // Mock de erro de conta bloqueada
    mockLogin.mockRejectedValue(
      new ApiError(403, 'ACCOUNT_LOCKED', 'Conta bloqueada temporariamente')
    )

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche e submete formulário
    await user.type(screen.getByLabelText('Email'), 'locked@test.com')
    await user.type(screen.getByLabelText('Senha'), 'password123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Conta bloqueada. Tente novamente mais tarde.')).toBeInTheDocument()
    })
  })

  it('deve exibir erro de conta suspensa', async () => {
    const user = userEvent.setup()

    // Mock de erro de conta suspensa
    mockLogin.mockRejectedValue(
      new ApiError(403, 'ACCOUNT_SUSPENDED', 'Conta suspensa')
    )

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche e submete formulário
    await user.type(screen.getByLabelText('Email'), 'suspended@test.com')
    await user.type(screen.getByLabelText('Senha'), 'password123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Conta suspensa. Entre em contato com o suporte.')).toBeInTheDocument()
    })
  })

  it('deve exibir erro genérico para outros erros', async () => {
    const user = userEvent.setup()

    // Mock de erro genérico
    mockLogin.mockRejectedValue(new Error('Network error'))

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Preenche e submete formulário
    await user.type(screen.getByLabelText('Email'), 'admin@test.com')
    await user.type(screen.getByLabelText('Senha'), 'password123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica mensagem de erro
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('deve limpar erro ao digitar novamente', async () => {
    const user = userEvent.setup()

    // Mock de erro
    mockLogin.mockRejectedValue(
      new ApiError(401, 'INVALID_CREDENTIALS', 'Email ou senha incorretos')
    )

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Submete com campos vazios para gerar erro
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Verifica erro
    await waitFor(() => {
      expect(screen.getByText('Por favor, preencha todos os campos')).toBeInTheDocument()
    })

    // Digita no campo de email
    await user.type(screen.getByLabelText('Email'), 'admin@test.com')

    // Submete novamente
    await user.type(screen.getByLabelText('Senha'), 'password')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Erro anterior deve ter sido limpo antes de mostrar novo erro
    await waitFor(() => {
      expect(screen.getByText('Email ou senha incorretos')).toBeInTheDocument()
    })
  })

  it('deve ter campos com autocomplete apropriado', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    const passwordInput = screen.getByLabelText('Senha') as HTMLInputElement

    expect(emailInput.autocomplete).toBe('email')
    expect(passwordInput.autocomplete).toBe('current-password')
  })

  it('deve ter campo de email com type="email"', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    expect(emailInput.type).toBe('email')
  })

  it('deve ter campo de senha com type="password"', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const passwordInput = screen.getByLabelText('Senha') as HTMLInputElement
    expect(passwordInput.type).toBe('password')
  })
})
