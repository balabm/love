import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/evolution': 'http://localhost:8000',
      '/neural': 'http://localhost:8000',
      '/intelligence': 'http://localhost:8000',
      '/emotional': 'http://localhost:8000',
      '/modern': 'http://localhost:8000',
      '/orchestrator': 'http://localhost:8000',
      '/voice': 'http://localhost:8000',
      '/settings': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    }
  }
})
