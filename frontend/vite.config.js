import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Forward API paths to Uvicorn, which dev.sh starts in the same
    // container. The browser only talks to port 5173.
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/recalls': 'http://127.0.0.1:8000',
      '/captures': 'http://127.0.0.1:8000',
    },
  },
})
