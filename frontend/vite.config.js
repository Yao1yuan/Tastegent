import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy all API requests to the local backend server
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '') // Optional: remove /api prefix
      },
      // Proxy specific paths if needed
      '/menu': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/token': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin/menu': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
       '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
