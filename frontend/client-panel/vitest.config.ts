/**
 * Configuração do Vitest para testes unitários.
 * 
 * Configurações:
 * - Ambiente jsdom para simular DOM do navegador
 * - Setup de testes com @testing-library/jest-dom
 * - Cobertura de código com v8
 * - Globals habilitados para describe/it/expect
 */

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    // Ambiente de teste (jsdom simula navegador)
    environment: 'jsdom',
    
    // Habilita globals (describe, it, expect, etc)
    globals: true,
    
    // Arquivo de setup executado antes dos testes
    setupFiles: ['./src/test/setup.ts'],
    
    // Configuração de cobertura
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      // Meta de cobertura mínima de 70%
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
