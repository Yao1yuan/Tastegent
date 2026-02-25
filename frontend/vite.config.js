import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { HttpsProxyAgent } from 'https-proxy-agent';

const proxyAgent = new HttpsProxyAgent('http://127.0.0.1:9000');

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/menu': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false, // In case of SSL certificate issues
        xfwd: true, // Add x-forwarded-for headers
        agent: proxyAgent,
      },
      '/token': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        agent: proxyAgent,
      },
      '/chat': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        agent: proxyAgent,
      },
      '/upload': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        agent: proxyAgent,
      },
      '/admin/menu': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        agent: proxyAgent,
      },
      '/uploads': {
        target: 'https://tastegent.onrender.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        agent: proxyAgent,
      }
    }
  }
})
