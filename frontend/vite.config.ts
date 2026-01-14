import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1/onboarding': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
    },
  },
})
