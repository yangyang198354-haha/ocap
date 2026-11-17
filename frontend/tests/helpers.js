// 测试辅助：Element Plus + Pinia + 内存路由挂载页面（不 mock 被测页面与 api.js，只 mock HTTP 层）
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus from 'element-plus'

// props：布局拆分后的分区页（section）等需要向被测组件传 props（向后兼容，缺省不传）
export async function mountPage(component, { path = '/', props = {}, pinia: sharedPinia = null } = {}) {
  // pinia：跨页面保持同一仓库（如认证页转申诉页的预填姓名）
  const pinia = sharedPinia || createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/polls/:id', component: { template: '<div />' } },
      { path: '/:pathMatch(.*)*', component: { template: '<div />' } }
    ]
  })
  router.push(path)
  await router.isReady()
  const wrapper = mount(component, {
    props,
    global: { plugins: [pinia, router, ElementPlus] },
    attachTo: document.body
  })
  await flushPromises()
  return { wrapper, router, pinia }
}

/** 按 `METHOD path` 返回预置响应；未登记的请求直接抛错，避免静默吞掉路径错误。 */
export function routeTable(table) {
  return async (url, arg) => {
    const hit = table[url]
    if (hit === undefined) throw new Error(`未预期的请求 ${url} ${JSON.stringify(arg)}`)
    return typeof hit === 'function' ? hit(arg) : hit
  }
}
