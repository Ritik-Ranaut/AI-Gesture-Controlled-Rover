import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': 'http://127.0.0.1:8001',
      '/video_feed': 'http://127.0.0.1:8001',
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true
      }
    }
  }
})
