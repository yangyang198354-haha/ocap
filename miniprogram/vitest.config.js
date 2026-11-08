import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// 小程序的 vite.config.js 加载 @dcloudio/vite-plugin-uni，
// 该插件依赖 uni-app 运行时环境变量，在纯 CI 环境会启动失败，因此单独提供不加载 uni 插件的最小配置。
// 用例范围：utils/api.js、utils/http.js、store、页面脚本与模板（uni 全局对象与 @dcloudio/uni-app 生命周期钩子在 tests/ 下做最小桩）。
// uni 内置组件标签（view/text/picker 等）按自定义元素处理，仅用于在 jsdom 中挂载。
const UNI_TAGS = new Set([
  'view', 'text', 'picker', 'radio', 'radio-group', 'checkbox', 'checkbox-group',
  'scroll-view', 'image', 'swiper', 'swiper-item', 'navigator', 'switch', 'slider'
])

export default defineConfig({
  plugins: [
    vue({ template: { compilerOptions: { isCustomElement: (tag) => UNI_TAGS.has(tag) } } })
  ],
  resolve: {
    alias: {
      '@dcloudio/uni-app': fileURLToPath(new URL('./tests/stubs/uni-app.js', import.meta.url)),
      '@': fileURLToPath(new URL('./', import.meta.url))
    }
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    setupFiles: ['tests/setup.js']
  }
})
