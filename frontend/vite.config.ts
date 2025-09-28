import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // 모든 인터페이스에서 접근 가능
    port: 3000,
    strictPort: true, // 포트가 사용 중이면 실패
    // https: {
    //   key: '../ssl/key.pem',
    //   cert: '../ssl/cert.pem',
    // },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
    // 개발 서버 옵션
    hmr: {
      host: '127.0.0.1',
      port: 3001, // HMR용 별도 포트
    },
    // 추가 옵션
    open: false, // 자동 브라우저 열기 비활성화
    cors: true, // CORS 활성화
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
