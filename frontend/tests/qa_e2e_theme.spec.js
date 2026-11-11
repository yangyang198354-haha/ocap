// PHASE_09 E2E（替代口径：jsdom 中挂载真实 App + 真实路由 + 真实页面 + 真实 api.js，HTTP 层用“带状态的假服务端”）
// 本机无浏览器，视觉/动效/计时项见 e2e_test_report 人工验证清单。
// 溯源：US-075/076/077/078/079/082/086 的用户旅程；AC-075-01、AC-076-01、AC-078-01/02/03、AC-079-02、AC-082-02、AC-086-01/02
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import App from '@/App.vue'
import router from '@/router'
import Login from '@/portal/Login.vue'
import { THEMES } from '@/theme/generated/registry'

const { http } = mocked
vi.setConfig({ testTimeout: 60000 })
const html = () => document.documentElement
const ME = (n) => ({
  profile: { id: n, nickname: `用户${n}`, phone: '138****0000' },
  identities: { is_guest: false, units: [{ id: 1 }], committee: null, labels: ['户主'] }
})

// 假服务端：账号表 {identifier: {token, theme}}；令牌 → 账号
let accounts
let puts
function installServer() {
  puts = []
  http.post.mockImplementation(async (url, body) => {
    if (url === '/auth/login/password') {
      const acc = accounts[body.identifier]
      if (!acc) throw { code: 'LOGIN_FAILED', message: '账号或密码错误' }
      return { token: acc.token, user: { id: acc.id }, is_new: false }
    }
    if (url === '/auth/logout') return {}
    throw new Error(`未预期 POST ${url}`)
  })
  const byToken = () => Object.values(accounts).find((a) => a.token === localStorage.getItem('ocap_token'))
  http.get.mockImplementation(async (url) => {
    if (url === '/me/theme') return { theme: byToken().theme }
    if (url === '/me') return ME(byToken().id)
    if (url === '/me/profile') return { nickname: `用户${byToken().id}` }
    if (url.startsWith('/resolutions') || url.startsWith('/approval') || url.startsWith('/polls')) return { results: [] }
    throw new Error('WECHAT_UNAVAILABLE')
  })
  http.put.mockImplementation(async (url, body) => {
    if (url !== '/me/theme') throw new Error(`未预期 PUT ${url}`)
    if (!THEMES.some((t) => t.key === body.theme)) throw { code: 'INVALID_VALUE' }
    puts.push(body.theme)
    byToken().theme = body.theme
    return { theme: body.theme }
  })
}

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const INLINE = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1]

// 模拟一次整页加载：先执行 index.html 的首屏内联脚本，再挂载应用
async function mountApp() {
  new Function(INLINE)()
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(App, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}
async function go(path) {
  await router.push(path)
  await flushPromises()
  await flushPromises()
}
async function loginAs(wrapper, identifier) {
  await go('/login')
  const login = wrapper.findComponent(Login)
  login.vm.form.identifier = identifier
  login.vm.form.password = 'Ocap2026pass'
  await login.vm.loginPassword()
  // 登录成功后的 router.replace 不被页面等待，且目标页组件为懒加载
  await vi.waitFor(() => expect(router.currentRoute.value.path).not.toBe('/login'), { timeout: 8000 })
  await flushPromises()
  await flushPromises()
}
async function logoutViaStore() {
  const { useAuthStore } = await import('@/stores/auth')
  await useAuthStore().logout()
  await go('/login')
}

beforeEach(async () => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  html().removeAttribute('data-theme')
  html().classList.remove('dark')
  accounts = {
    alice: { id: 1, token: 'TA', theme: null },
    bob: { id: 2, token: 'TB', theme: null },
    carol: { id: 3, token: 'TC', theme: 'terminal' }
  }
  installServer()
  await router.replace('/login').catch(() => {})
})

describe('TC-E2E-101 用户旅程：默认 B → 选 A → 全站沿用 → 退出后登录页沿用 → 重新登录 → 他人登录不串号 → 管理端独立偏好', () => {
  it('完整旅程', async () => {
    const wrapper = await mountApp()
    // 1 首次访问（无设备记忆）登录页为 B，且无风格入口（AC-079-01/03）
    await go('/login')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(wrapper.find('[role=radio]').exists()).toBe(false)
    // 2 alice 登录（账号从未选择）→ B（AC-075-01）
    await loginAs(wrapper, 'alice')
    expect(router.currentRoute.value.path).toBe('/')
    expect(html().getAttribute('data-theme')).toBe('bento')
    // 3 个人中心：B 处于选中，点击 A(neon) 即时生效并保存（AC-076-01）
    await go('/me')
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
    await wrapper.find('[data-theme-key=neon]').trigger('click')
    await flushPromises()
    expect(html().getAttribute('data-theme')).toBe('neon')
    expect(html().classList.contains('dark')).toBe(true)
    expect(puts).toEqual(['neon'])
    // 4 访问其它用户端页面，风格保持（AC-081 逻辑部分）
    for (const p of ['/resolutions', '/polls', '/claims', '/units', '/tasks', '/reports']) {
      await go(p)
      expect(html().getAttribute('data-theme'), p).toBe('neon')
    }
    // 5 退出登录 → 登录页仍是 neon（AC-079-02）
    await logoutViaStore()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(html().getAttribute('data-theme')).toBe('neon')
    // 6 alice 重新登录 → 账号值 neon（AC-078-01）
    await loginAs(wrapper, 'alice')
    expect(html().getAttribute('data-theme')).toBe('neon')
    // 7 同一浏览器 bob（从未选择）登录 → B，不受 alice 影响（AC-078-03）；alice 的账号值未变
    await logoutViaStore()
    await loginAs(wrapper, 'bob')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(accounts.alice.theme).toBe('neon')
    // 8 管理端使用独立偏好，用户端记忆不被改写（AC-143-01/02）
    await go('/me')
    http.put.mockResolvedValueOnce({ theme: 'terminal' })
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    localStorage.setItem('ocap_admin_token', 'adm')
    await go('/admin/registry')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    await go('/me')
    expect(html().getAttribute('data-theme')).toBe('terminal')
    wrapper.unmount()
  }, 60000)
})

describe('TC-E2E-102 用户旅程：换设备登录沿用账号风格；风格被下线后回退 B 并可重选', () => {
  it('另一设备（空设备记忆）登录 carol → terminal（AC-078-02）', async () => {
    const wrapper = await mountApp()
    await go('/login')
    expect(html().getAttribute('data-theme')).toBe('bento')
    await loginAs(wrapper, 'carol')
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    wrapper.unmount()
  })
  it('账号保存的风格已下线 → 登录后 B、功能可用；个人中心不含下线风格，可重选并立即生效（AC-086-01/02）', async () => {
    accounts.alice.theme = 'retired-d'
    const wrapper = await mountApp()
    await loginAs(wrapper, 'alice')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(router.currentRoute.value.path).toBe('/')
    await go('/me')
    const keys = wrapper.findAll('[role=radio]').map((o) => o.attributes('data-theme-key'))
    expect(keys).toEqual(['neon', 'bento', 'terminal'])
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(accounts.alice.theme).toBe('terminal')
    wrapper.unmount()
  })
  it('设备记忆的风格已下线（未登录）→ 登录页刷新后为 B（AC-079-04/086-03）', async () => {
    localStorage.setItem('ocap_theme', 'retired-d')
    const wrapper = await mountApp()
    await go('/register')
    await go('/login')
    expect(html().getAttribute('data-theme')).toBe('bento')
    wrapper.unmount()
  })
})
