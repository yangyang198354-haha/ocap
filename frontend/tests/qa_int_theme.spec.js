// PHASE_08 集成测试（ocap_ui_theme / Web）：路由 + 风格 store + 真实 api.js + 真实页面（仅 mock HTTP 层）
// 溯源：AC-075-01、AC-076-01/03/04、AC-077-03、AC-078-01、AC-079-02/03、AC-082-01/02/04、AC-084-01、AC-085-01/02、AC-086-01/02、AC-090-03
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { ElMessage } from 'element-plus'
import { mountPage, routeTable } from './helpers.js'
import router from '@/router'
import Login from '@/portal/Login.vue'
import Me from '@/portal/Me.vue'
import PortalLayout from '@/portal/PortalLayout.vue'
import { useThemeStore } from '@/theme/store'
import { useAuthStore } from '@/stores/auth'

const { http } = mocked
const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src')
const html = () => document.documentElement
const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: false, units: [{ id: 1 }], committee: null, labels: ['户主'] }
}

beforeEach(async () => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  html().removeAttribute('data-theme')
  html().classList.remove('dark')
  setActivePinia(createPinia())
  http.get.mockReset()
  http.put.mockReset()
  http.post.mockReset()
})

describe('TC-INT-101 路由 ↔ 风格 store：管理端固定 bento（AC-082-01/02/04）', () => {
  it('普通用户记忆 terminal 时进入管理端登录页仍为 bento，且设备记忆不被改写、不请求 /me/theme', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    await router.push('/admin/login')
    await flushPromises()
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(html().classList.contains('dark')).toBe(false)
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    expect(http.get).not.toHaveBeenCalledWith('/me/theme', expect.anything())
  })
  it('管理端登录态：进入后台页 bento；离开后台回到用户端按设备记忆 terminal', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    localStorage.setItem('ocap_admin_token', 'adm')
    await router.push('/admin/registry')
    await flushPromises()
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(router.currentRoute.value.path).toBe('/admin/registry')
    await router.push('/login')
    await flushPromises()
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(html().classList.contains('dark')).toBe(true)
  })
  it('管理端令牌缺失仍跳 /admin/login，行为与改动前一致（AC-082-04）', async () => {
    await router.push('/admin/audit')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/login')
  })
  it('未登录访问 /me 跳登录并带 redirect，不显示风格区块（AC-076-04）', async () => {
    await router.push('/me')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/me')
    expect(document.body.innerHTML).not.toContain('界面风格')
  })
  it('已登录进入用户端页面：触发一次与账号偏好对账（GET /me/theme），账号值覆盖设备记忆（AC-077-03/078-01）', async () => {
    localStorage.setItem('ocap_token', 'tok')
    localStorage.setItem('ocap_theme', 'terminal')
    http.get.mockImplementation(routeTable({ '/me/theme': { theme: 'neon' }, '/me': ME }))
    await router.push('/login')
    await flushPromises()
    await router.push('/units')
    await flushPromises()
    expect(http.get).toHaveBeenCalledWith('/me/theme', { params: undefined })
    expect(html().getAttribute('data-theme')).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('neon')
  })
})

describe('TC-INT-102 登录后对账（AC-075-01、AC-077-02、AC-086-01、AC-090-03）', () => {
  async function loginWith(account, device) {
    if (device) localStorage.setItem('ocap_theme', device)
    http.post.mockResolvedValue({ token: 'T', user: { id: 1 }, is_new: false })
    http.get.mockImplementation(async (url) => {
      if (url === '/me/theme') {
        if (account instanceof Error) throw account
        return { theme: account }
      }
      throw new Error('WECHAT_UNAVAILABLE')
    })
    const { wrapper, router: r } = await mountPage(Login, { path: '/login' })
    useThemeStore().initFromDevice()
    const replace = vi.spyOn(r, 'replace')
    wrapper.vm.form.identifier = '13800000001'
    wrapper.vm.form.password = 'Ocap2026pass'
    await wrapper.vm.loginPassword()
    await flushPromises()
    return { replace, r }
  }
  it('账号值优先：设备记忆 terminal、账号 neon → 登录后 neon，跳转发生在对账之后', async () => {
    const order = []
    http.get.mockImplementation(async (url) => {
      if (url !== '/me/theme') throw new Error('WECHAT_UNAVAILABLE')
      order.push('GET theme')
      return { theme: 'neon' }
    })
    http.post.mockResolvedValue({ token: 'T', user: { id: 1 }, is_new: false })
    localStorage.setItem('ocap_theme', 'terminal')
    const { wrapper, router: r } = await mountPage(Login, { path: '/login' })
    useThemeStore().initFromDevice()
    vi.spyOn(r, 'replace').mockImplementation(async () => { order.push('replace') })
    wrapper.vm.form.identifier = '13800000001'
    wrapper.vm.form.password = 'Ocap2026pass'
    await wrapper.vm.loginPassword()
    await flushPromises()
    expect(order).toEqual(['GET theme', 'replace'])
    expect(html().getAttribute('data-theme')).toBe('neon')
  })
  it('账号值为 null（从未选择 / 老账号）→ bento，并覆盖他人遗留的设备记忆（AC-078-03）', async () => {
    await loginWith(null, 'terminal')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(localStorage.getItem('ocap_theme')).toBe('bento')
  })
  it('账号值是已下线的 key → bento，业务页可继续跳转，无报错', async () => {
    const { replace } = await loginWith('retired-d', 'neon')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(replace).toHaveBeenCalledWith('/')
  })
  it('偏好读取失败（超时）→ 保持设备记忆风格，仍跳转，不出现空白（AC-090-03）', async () => {
    const { replace } = await loginWith(new Error('timeout'), 'terminal')
    expect(useThemeStore().current).toBe('terminal')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    expect(replace).toHaveBeenCalled()
  })
  it('Register / WechatCallback 同样在跳转前对账（源码顺序）', () => {
    for (const f of ['Register.vue', 'WechatCallback.vue']) {
      const text = fs.readFileSync(path.join(SRC, 'portal', f), 'utf8')
      const a = text.indexOf('reconcileAfterLogin')
      const b = text.indexOf('router.replace', a)
      expect(a, f).toBeGreaterThan(-1)
      expect(b, f).toBeGreaterThan(a)
    }
  })
})

describe('TC-INT-103 个人中心风格区块（AC-074-01、AC-076-01/02/03、AC-086-02）', () => {
  const routes = routeTable({ '/me': ME, '/me/profile': { nickname: '张三' } })
  beforeEach(() => {
    http.get.mockImplementation(async (u, a) => (u === '/me/theme' ? { theme: null } : routes(u, a)))
  })
  it('风格区块是独立区块，列出 3 项，默认“极光 Bento”选中；来回切换不限次数', async () => {
    const { wrapper } = await mountPage(Me, { path: '/me' }).catch(() => ({}))
    expect(wrapper).toBeTruthy()
    const titles = wrapper.findAll('h3.title').map((h) => h.text())
    expect(titles[0]).toBe('界面风格')
    expect(titles.length).toBeGreaterThan(1)
    const opts = wrapper.findAll('[role=radio]')
    expect(opts.map((o) => o.find('.theme-name').text())).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端'])
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
    for (const key of ['terminal', 'neon', 'terminal', 'bento']) {
      http.put.mockResolvedValueOnce({ theme: key })
      await wrapper.find(`[data-theme-key=${key}]`).trigger('click')
      await flushPromises()
      expect(html().getAttribute('data-theme')).toBe(key)
      expect(wrapper.findAll('[role=radio][aria-checked=true]')).toHaveLength(1)
    }
    expect(http.put).toHaveBeenCalledTimes(4)
    expect(http.put).toHaveBeenLastCalledWith('/me/theme', { theme: 'bento' })
  })
  it('保存失败：弹出含“保存失败”的提示，选中回到保存前；个人资料区块仍在', async () => {
    const spy = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountPage(Me, { path: '/me' })
    http.put.mockRejectedValueOnce(new Error('offline'))
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(spy.mock.calls[0][0]).toContain('保存失败')
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(wrapper.findAll('h3.title').length).toBeGreaterThan(1)
    spy.mockRestore()
  })
})

describe('TC-INT-104 退出登录保留设备记忆（AC-079-02/03）', () => {
  it('logout 后设备记忆仍在；登录页应用该风格且没有风格入口', async () => {
    localStorage.setItem('ocap_token', 'tok')
    localStorage.setItem('ocap_theme', 'terminal')
    http.post.mockResolvedValue({})
    const { wrapper } = await mountPage(Login, { path: '/login' }) // 未登录页
    setActivePinia(createPinia())
    await useAuthStore().logout()
    expect(localStorage.getItem('ocap_token')).toBeNull()
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    const store = useThemeStore()
    store.initFromDevice()
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(wrapper.find('[role=radio]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('界面风格')
  })
})

describe('TC-INT-105 布局：导航高亮与底部 5 标签（AC-084-01、AC-085-01/02）', () => {
  async function layoutAt(p) {
    localStorage.setItem('ocap_token', 'tok')
    http.get.mockImplementation(async () => ME)
    const { createMemoryHistory, createRouter } = await import('vue-router')
    const r = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }]
    })
    r.push(p)
    await r.isReady()
    const { mount } = await import('@vue/test-utils')
    const ElementPlus = (await import('element-plus')).default
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(PortalLayout, { global: { plugins: [pinia, r, ElementPlus] } })
    await flushPromises()
    return { wrapper, r }
  }
  it('决议列表与详情页：顶部导航仅“决议”高亮；切到投票后高亮项变为“投票”，任一时刻数量 = 1', async () => {
    const { wrapper, r } = await layoutAt('/resolutions')
    const active = () => wrapper.findAll('.topnav a.is-active').map((a) => a.text())
    expect(active()).toEqual(['决议'])
    await r.push('/resolutions/7')
    await flushPromises()
    expect(active()).toEqual(['决议'])
    await r.push('/polls')
    await flushPromises()
    expect(active()).toEqual(['投票/调查'])
    expect(wrapper.findAll('.tabbar a.is-active')).toHaveLength(1)
  })
  it('布局始终渲染底部标签栏 5 项（宽屏由 CSS 隐藏），顶部导航保留', async () => {
    const { wrapper } = await layoutAt('/')
    expect(wrapper.findAll('.tabbar a').map((a) => a.text())).toEqual(['首页', '决议', '投票', '报销', '我的'])
    expect(wrapper.find('.topnav').exists()).toBe(true)
  })
})
