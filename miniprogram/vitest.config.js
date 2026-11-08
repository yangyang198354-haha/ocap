import { defineConfig } from 'vitest/config'

// 小程序的 vite.config.js 加载 @dcloudio/vite-plugin-uni，
// 该插件依赖 uni-app 运行时环境变量，在纯 CI 环境会启动失败。
// 小程序当前无任何 *.spec.js 用例，vitest 仅作为占位，
// 因此单独提供一个不加载 uni 插件的最小配置。
export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    setupFiles: ['tests/setup.js']
  }
})
