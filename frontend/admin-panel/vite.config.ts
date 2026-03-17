import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuração do Vite para o painel administrativo
// Porta 5174 para não conflitar com o client-panel (5173)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      // Proxy para API backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy para WebSocket
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
