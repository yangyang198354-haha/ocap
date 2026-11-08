import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    setupFiles: ['tests/setup.js']
  }
})
