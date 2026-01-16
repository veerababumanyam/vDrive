import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api/v1/onboarding': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/api/v1/galleries': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api/v1/public': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api/v1/ws': {
        target: 'ws://localhost:8004',
        changeOrigin: true,
        ws: true,
      },
      '/api/v1/files': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
      '/api/v1/uploads': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
    },
  },
})
