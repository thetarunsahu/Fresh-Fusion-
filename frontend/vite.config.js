import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const frontendPort = Number(process.env.FRESHFUSION_FRONTEND_PORT || 5173);
const backendPort = Number(process.env.FRESHFUSION_BACKEND_PORT || 8000);
const backendHttp = `http://127.0.0.1:${backendPort}`;
const backendWs = `ws://127.0.0.1:${backendPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: frontendPort,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/api': { target: backendHttp, changeOrigin: true },
      '/uploads': { target: backendHttp, changeOrigin: true },
      '/ws': { target: backendWs, changeOrigin: true, ws: true },
    },
  },
});
