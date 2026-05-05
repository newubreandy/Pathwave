import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// 환경별 백엔드 주소: VITE_API_BASE 환경변수 (개발 기본 http://localhost:8080)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE || 'http://localhost:8080'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5174,   // provider-web(5173) 과 분리
      proxy: {
        '/api': {
          target: apiBase,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
