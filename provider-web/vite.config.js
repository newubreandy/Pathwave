import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// 환경별 백엔드 주소: VITE_API_BASE 환경변수 (개발 기본 http://localhost:8080)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE || 'http://localhost:8080'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',   // 같은 WiFi 모든 기기 접근 가능
      port: 5173,
      proxy: {
        // /api/* 요청을 백엔드로 프록시 → CORS 회피, 동일 도메인처럼 사용
        '/api': {
          target: apiBase,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
