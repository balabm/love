import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// All API routes that the frontend calls — must preserve full path when proxying
const API_PREFIXES = [
  '/agi',
  '/chat',
  '/context',
  '/dashboard',
  '/day-summary',
  '/devices',
  '/docs',
  '/ecosystem',
  '/emotional',
  '/evolution',
  '/fitness',
  '/guardian',
  '/health',
  '/integrations',
  '/intelligence',
  '/learning',
  '/life',
  '/lifescore',
  '/modern',
  '/neural',
  '/notifications',
  '/orchestrator',
  '/settings',
  '/static',
  '/tunnel',
  '/voice',
  '/wave',
  '/wellness',
  '/work',
  '/vision',
]

const proxy = {}
for (const prefix of API_PREFIXES) {
  proxy[prefix] = {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path, // preserve full path — don't strip prefix
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy,
  }
})
