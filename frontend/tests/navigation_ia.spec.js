// ocap_navigation_ia GROUP_D（MOD-174/175/176/177）：Web 下拉菜单动效参数、菜单常量、身份页 Tab 深链白名单。
// 层级：unit（纯常量与样式） + integration（真实 el-dropdown / 页面 + 真实 store，仅 mock HTTP 层）。
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus, { ElDropdown } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import PortalUserMenu from '@/portal/PortalUserMenu.vue'
import Units from '@/portal/Units.vue'
import MeProfile from '@/portal/me/MeProfile.vue'
import MeStyle from '@/portal/me/MeStyle.vue'
import {
  PORTAL_MENU,
  PORTAL_USER_MENU,
  USER_MENU_TIMING
} from '@/layout/menus'
import { useAuthStore } from '@/stores/auth'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const CSS = readFileSync(path.join(ROOT, 'frontend/src/shared/style.css'), 'utf8')

const OWNED = {
  unit_id: 7, specific_part: 'A房', role: 'HEAD', role_label: '产权业主',
  unit_type_label: '住宅', area_display: '89.50 ㎡', pending_application_count: 0, residents: []
}
const HOUSING = (units, pending = 0) => ({
  summary: units.length ? { code: 'OWNER', label: '产权业主' } : { code: 'GUEST', label: '游客' },
  units, pending_review_count: pending
})
const ME = { profile: { id: 1, nickname: '合成用户' }, identities: { is_guest: true, units: [], labels: [], committee: null } }
const table = (over = {}) => routeTable({
  '/me': ME, '/me/housing': HOUSING([]), '/resident-applications/to-review': [],
  '/resident-applications/mine': [], '/appeals/mine': [], ...over
})

beforeEach(() => {
  vi.clearAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  document.body.innerHTML = ''
})

describe('菜单常量与动效参数（US-302/308/309）', () => {
  it('TC-UNIT-1101 / AC-309-01、AC-302-01、AC-302-02、AC-303-01：右上角仅“个人资料/系统设置”两项，业务项下沉为页内 Tab，无“手机号/认证申诉”', () => {
    expect(PORTAL_USER_MENU.map((i) => i.label)).toEqual(['个人资料', '系统设置'])
    expect(PORTAL_USER_MENU.map((i) => i.to)).toEqual(['/me/profile', '/me/settings'])
    const allLabels = [
      ...PORTAL_MENU.flatMap((n) => [n.label, ...(n.children || []).map((c) => c.label)]),
      ...PORTAL_USER_MENU.map((i) => i.label)
    ]
    expect(allLabels).not.toContain('手机号')
    expect(allLabels).not.toContain('认证申诉')
    // 改写（MOD-178）：这四项不再直接出现在下拉菜单
    for (const label of ['绑定手机', '设置密码', '邮箱验证', '账号注销', '界面风格']) {
      expect(PORTAL_USER_MENU.map((i) => i.label)).not.toContain(label)
    }
  })

  it('TC-INT-1106 / AC-302-01：绑定手机/设置密码/邮箱验证/账号注销是个人资料页内 Tab；界面风格是系统设置页内 Tab', async () => {
    http.get.mockImplementation(table({
      '/me/profile': { id: 1, nickname: '合成用户', phone: '', email: '' }, '/me/theme': { theme: null }
    }))
    const profile = await mountPage(MeProfile, { path: '/me/profile' })
    await flush()
    expect(profile.wrapper.findAll('.el-tabs__item').map((t) => t.text()))
      .toEqual(['个人资料', '绑定手机', '设置密码', '邮箱验证', '账号注销'])
    const settings = await mountPage(MeStyle, { path: '/me/settings' })
    await flush()
    expect(settings.wrapper.findAll('.el-tabs__item').map((t) => t.text())).toEqual(['界面风格'])
  })

  it('TC-UNIT-1102 / AC-308-01、AC-308-02：USER_MENU_TIMING 为 400ms 过渡 + 180ms 悬停意图', () => {
    expect(USER_MENU_TIMING).toEqual({ transitionMs: 400, hoverIntentMs: 180 })
  })

  it('TC-INT-1101 / AC-308-02：el-dropdown 传播 show/hide-timeout=180、trigger 含 hover/click、popper-class=user-menu-popper', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<i />' } }] })
    router.push('/')
    await router.isReady()
    useAuthStore(pinia).me = ME
    const wrapper = (await import('@vue/test-utils')).mount(PortalUserMenu, {
      global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body
    })
    await flush()
    const dd = wrapper.findComponent(ElDropdown)
    expect(dd.props('showTimeout')).toBe(180)
    expect(dd.props('hideTimeout')).toBe(180)
    expect(dd.props('trigger')).toEqual(['hover', 'click'])
    expect(dd.props('popperClass') ?? dd.attributes('popper-class')).toBe('user-menu-popper')
    wrapper.unmount()
  })

  it('TC-INT-1102 / AC-308-01、AC-308-03：全局样式含 400ms 过渡与 prefers-reduced-motion 降级到 0s', () => {
    expect(CSS).toMatch(/\.user-menu-popper\.el-zoom-in-top-enter-active[\s\S]*?transition-duration:\s*400ms/)
    expect(CSS).toMatch(/\.user-menu-popper\.el-zoom-in-top-leave-active/)
    expect(CSS).toMatch(/@media \(prefers-reduced-motion: reduce\)[\s\S]*?transition-duration:\s*0s/)
  })
})

describe('身份页 Tab 深链白名单（US-300/306）', () => {
  const activeTab = (wrapper) => wrapper.find('.el-tabs__item.is-active').text().replace(/\s*\d+$/, '')

  it('TC-INT-1103 / AC-306-02、AC-300-01、AC-300-02：/units?tab=review 的产权业主落到待我审批 Tab', async () => {
    http.get.mockImplementation(table({
      '/me/housing': HOUSING([OWNED], 1),
      '/resident-applications/to-review': [{ id: 8, unit: { unit_id: 7, specific_part: 'A房' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { nickname: '王五', account_no: '1000000005' } }]
    }))
    const { wrapper } = await mountPage(Units, { path: '/units?tab=review', props: { section: 'identity' } })
    await flush()
    expect(activeTab(wrapper)).toBe('待我审批的同住人申请')
    expect(wrapper.find('#review').text()).toContain('王五')
  })

  it('TC-INT-1104 / AC-306-02、AC-300-03：无产权业主请求 review 回落身份 Tab，且无审批 Tab', async () => {
    http.get.mockImplementation(table({ '/me/housing': HOUSING([]) }))
    const { wrapper } = await mountPage(Units, { path: '/units?tab=review', props: { section: 'identity' } })
    await flush()
    expect(activeTab(wrapper)).toBe('我的身份与房屋')
    expect(wrapper.findAll('.el-tabs__item')).toHaveLength(1)
  })

  it('TC-INT-1105 / AC-306-02：非法 tab 值忽略并回落默认身份 Tab', async () => {
    http.get.mockImplementation(table({ '/me/housing': HOUSING([OWNED], 0) }))
    const { wrapper } = await mountPage(Units, { path: '/units?tab=bogus', props: { section: 'identity' } })
    await flush()
    expect(activeTab(wrapper)).toBe('我的身份与房屋')
  })
})
