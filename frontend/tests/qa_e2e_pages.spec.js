// PHASE_09 E2E（替代口径）：逐页自动化走查——真实 App + 真实路由 + 全部页面组件，三套风格下 data-theme 正确、
// 业务内容（文本）与风格无关、无残留内联颜色；底部标签栏点击跳转；管理端 9 页固定 B。
// 视觉观感由人工清单覆盖（本机无浏览器）。溯源：AC-081-01/02/03（可自动化部分）、AC-082-01/03、AC-084-01、AC-074-01
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
import { useThemeStore } from '@/theme/store'

const { http, adminHttp } = mocked
const html = () => document.documentElement
vi.setConfig({ testTimeout: 120000 })

let accountTheme = null
const PORTAL = ['/login', '/register', '/login/wechat', '/', '/me', '/units', '/resolutions', '/resolutions/1', '/tasks', '/claims', '/income', '/polls', '/polls/1', '/reports']
const ADMIN = ['/admin/login', '/admin/registry', '/admin/appeals', '/admin/memberships', '/admin/seats', '/admin/flows', '/admin/finance', '/admin/users', '/admin/audit']

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  accountTheme = null
  html().removeAttribute('data-theme')
  const respond = async (url) => {
    if (url === '/me/theme') return { theme: accountTheme }
    if (url === '/me') return { profile: { id: 1, nickname: '张三', phone: '138****0000' }, identities: { is_guest: false, units: [{ id: 1 }], committee: { position: 'CHAIR' }, labels: ['户主', '主任'] } }
    if (url === '/me/profile') return { nickname: '张三' }
    if (/^\/(resolutions|polls)\/\d+$/.test(url)) return { id: 1, title: '示例', status: 'OPEN', questions: [], flows: [] }
    return { results: [], count: 0 }
  }
  http.get.mockImplementation(respond)
  adminHttp.get.mockImplementation(respond)
  http.put.mockImplementation(async (u, b) => ({ theme: b.theme }))
})

async function visit(wrapper, p) {
  await router.push(p)
  await flushPromises()
  await flushPromises()
  expect(router.currentRoute.value.path, `未能进入 ${p}`).toBe(p)
  // 风格选择器本身的“已选”标记随风格变化，属于预期差异，比较时剔除
  const clone = wrapper.element.cloneNode(true)
  clone.querySelectorAll('.theme-picker').forEach((n) => n.remove())
  return clone.textContent.replace(/\s+/g, ' ').trim()
}
function mountApp() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(App, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
}
// 内联样式里不得出现颜色字面量（风格选择器色块是数据驱动的，豁免）
function inlineColors() {
  return [...document.querySelectorAll('[style]')]
    .filter((el) => !el.closest('.theme-swatch'))
    .map((el) => el.getAttribute('style'))
    .filter((s) => /#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/.test(s))
}

describe('TC-E2E-104 用户端 14 页 × 三套风格逐页走查（AC-081-01/02/03 自动化部分）', () => {
  it('每页在 neon / bento / terminal 下 data-theme 正确、文本内容一致、无内联颜色', async () => {
    localStorage.setItem('ocap_token', 'tok')
    expect(PORTAL).toHaveLength(14)
    const wrapper = mountApp()
    const texts = {}
    const bad = []
    for (const key of ['neon', 'bento', 'terminal']) {
      accountTheme = key // 账号偏好与设备记忆一致（对账不改变风格）
      localStorage.setItem('ocap_theme', key)
      useThemeStore().resetSession()
      useThemeStore().initFromDevice()
      for (const p of PORTAL) {
        // 已登录访问 /login 等公开页同样可达
        texts[p] = texts[p] || {}
        texts[p][key] = await visit(wrapper, p)
        if (html().getAttribute('data-theme') !== key) bad.push(`${key} ${p}: data-theme=${html().getAttribute('data-theme')}`)
        const colors = inlineColors()
        if (colors.length) bad.push(`${key} ${p}: 内联颜色 ${colors.join('|')}`)
      }
    }
    expect(bad).toEqual([])
    const empty = PORTAL.filter((p) => !texts[p].bento)
    expect(empty, '页面渲染为空').toEqual([])
    const diff = PORTAL.filter((p) => new Set(Object.values(texts[p])).size !== 1)
    expect(diff, `风格间文本不一致的页面`).toEqual([])
    wrapper.unmount()
  })
})

describe('TC-E2E-105 管理端 9 页固定风格 B（AC-082-01/03）', () => {
  it('普通用户记忆 terminal 时，9 个管理端页面均为 bento，且无任何风格入口', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    localStorage.setItem('ocap_admin_token', 'adm')
    expect(ADMIN).toHaveLength(9)
    const wrapper = mountApp()
    const bad = []
    for (const p of ADMIN) {
      await visit(wrapper, p)
      if (html().getAttribute('data-theme') !== 'bento') bad.push(`${p}: ${html().getAttribute('data-theme')}`)
      if (document.querySelector('[role=radio], .theme-picker, .theme-option')) bad.push(`${p}: 出现风格入口`)
      const colors = inlineColors()
      if (colors.length) bad.push(`${p}: 内联颜色 ${colors.join('|')}`)
    }
    expect(bad).toEqual([])
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    wrapper.unmount()
  })
})

describe('TC-E2E-106 底部标签栏点击进入各页（AC-084-01）', () => {
  it('点击 首页/决议/投票/报销/我的 依次进入 /、/resolutions、/polls、/claims、/me，且当前项高亮唯一', async () => {
    localStorage.setItem('ocap_token', 'tok')
    const wrapper = mountApp()
    await visit(wrapper, '/units')
    const tabs = () => wrapper.findAll('.tabbar a')
    expect(tabs().map((a) => a.text())).toEqual(['首页', '决议', '投票', '报销', '我的'])
    const expected = ['/', '/resolutions', '/polls', '/claims', '/me']
    for (let i = 0; i < 5; i++) {
      await tabs()[i].trigger('click')
      await flushPromises()
      await flushPromises()
      expect(router.currentRoute.value.path).toBe(expected[i])
      expect(wrapper.findAll('.tabbar a.is-active').map((a) => a.text())).toEqual([tabs()[i].text()])
    }
    wrapper.unmount()
  })
})
