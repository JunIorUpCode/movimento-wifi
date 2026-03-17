/**
 * Arquivo de setup para testes.
 * 
 * Executado antes de todos os testes.
 * Configura matchers do @testing-library/jest-dom.
 */

import '@testing-library/jest-dom'

// Mock do localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

global.localStorage = localStorageMock as any

// Mock do fetch global
global.fetch = vi.fn()

// Limpa mocks antes de cada teste
beforeEach(() => {
  vi.clearAllMocks()
  localStorageMock.getItem.mockReturnValue(null)
})
