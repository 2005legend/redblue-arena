import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The React shell talks to `python -m arena.cli serve` on 8765. `/ws` streams the match,
// `/api` holds the read-only SOC endpoints, and `/target` is the live victim view that the
// Arena page embeds so the demo shows the real storefront under attack.
const proxy = {
  '/ws': {
    target: 'ws://127.0.0.1:8765',
    ws: true,
  },
  '/api': {
    target: 'http://127.0.0.1:8765',
    changeOrigin: true,
  },
  '/target': {
    target: 'http://127.0.0.1:8765',
    changeOrigin: true,
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy },
  preview: { port: 4173, proxy }
})
