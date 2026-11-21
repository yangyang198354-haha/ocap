import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    // 路由用例首次导航需冷启动动态 import 登录页；并行 worker 下在 Windows 上可能超时，串行执行更稳定
    fileParallelism: false,
    hookTimeout: 30000,
    testTimeout: 20000
  }
})
