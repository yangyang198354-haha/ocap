import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { runLifecycle } from './stubs/uni-app.js'

/** 按 "METHOD path" 返回预置响应的 uni.request 实现；未登记的请求以 404 失败，避免静默吞掉路径错误。 */
export function respondWith(table) {
  uni.request.mockImplementation(({ url, method, data, success }) => {
    const path = url.replace(/^\/api\/v1/, '')
    const key = `${method} ${path}`
    const hit = table[key]
    if (hit === undefined) {
      success({ statusCode: 404, data: { code: 'NOT_FOUND', message: `未预期的请求 ${key}` } })
      return
    }
    const body = typeof hit === 'function' ? hit(data) : hit
    success({ statusCode: 200, data: body })
  })
}

export function requests() {
  return uni.request.mock.calls.map(([opt]) => ({
    method: opt.method, path: opt.url.replace(/^\/api\/v1/, ''), data: opt.data, header: opt.header
  }))
}

export async function mountPage(component, { query = {}, token = 'tok' } = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  if (token) uni.setStorageSync('ocap_token', token)
  const wrapper = mount(component, { global: { plugins: [pinia] }, attachTo: document.body })
  await runLifecycle(query)
  await flushPromises()
  return { wrapper, pinia }
}

export const byText = (wrapper, selector, text) =>
  wrapper.findAll(selector).find((el) => el.text().includes(text))
