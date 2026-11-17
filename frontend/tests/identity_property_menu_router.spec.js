// ocap_identity_property GROUP_D：导航、菜单与路由守护（MOD-135 / IFC-339、IFC-340）。
// 层级：unit（菜单纯函数/常量）与 integration（真实 router + 守卫，仅 mock HTTP 层）。TC-UNIT-930 起、TC-INT-970 起。
// 溯源：US-233（AC-233-01~05）、US-235（AC-235-03）、US-236（AC-236-01~04）、REQ-NFUNC-045。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import router from '@/router'
import { PORTAL_MENU, PORTAL_USER_MENU, nextOpenKey, resolveActive, visibleMenu } from '@/layout/menus'

const { http, adminHttp } = mocked
const UNITS = PORTAL_MENU.find((n) => n.key === 'units')
const recordOf = (path) => {
  const r = router.resolve(path)
  return { r, last: r.matched[r.matched.length - 1] }
}

describe('菜单配置与高亮（unit）', () => {
  it('TC-UNIT-930 / AC-233-05：/me/identity 与 /units 都使"我的房屋"展开、仅二级项"我的身份与房屋"高亮（Q-IP-16=A）', () => {
    for (const p of ['/units', '/me/identity']) {
      const active = resolveActive(visibleMenu(PORTAL_MENU, { isCommittee: true }), p)
      expect(active.leaf.label, p).toBe('我的身份与房屋')
      expect(active.node.key, p).toBe('units')
      expect(nextOpenKey(PORTAL_MENU, p), p).toBe('units')
    }
    // 其他二级路径不会误高亮"我的身份与房屋"
    for (const p of ['/units/pick', '/units/appeal', '/units/applications', '/units/appeals']) {
      expect(resolveActive(PORTAL_MENU, p).leaf.label, p).not.toBe('我的身份与房屋')
    }
  })

  it('TC-UNIT-931 / AC-236-01、AC-233-01、REQ-NFUNC-045：菜单文案残留数为 0——无"选择房屋""待我审批的同住人申请"二级项，无恰为"我的身份"的项', () => {
    const labels = [...PORTAL_MENU.flatMap((n) => [n.label, ...(n.children || []).map((c) => c.label)]), ...PORTAL_USER_MENU.map((i) => i.label)]
    expect(labels.filter((l) => l === '选择房屋')).toEqual([])
    expect(labels.filter((l) => l === '我的身份')).toEqual([])
    expect(labels.filter((l) => l === '待我审批的同住人申请')).toEqual([])
    expect(labels.filter((l) => l === '我的身份与房屋')).toHaveLength(2) // 右上角 + 左侧二级项，同名
    expect(UNITS.children.map((c) => c.to)).toEqual(['/units', '/units/pick', '/units/appeal', '/units/applications', '/units/appeals'])
  })

  it('TC-UNIT-932 / AC-233-02：右上角项与左侧二级项同名，两个入口地址不同（/me/identity、/units）、均保留', () => {
    const userItem = PORTAL_USER_MENU.find((i) => i.key === 'me.identity')
    const sideItem = UNITS.children.find((c) => c.key === 'units.identity')
    expect(userItem.label).toBe(sideItem.label)
    expect([userItem.to, sideItem.to]).toEqual(['/me/identity', '/units'])
    expect(sideItem.activeOn).toEqual(['/me/identity'])
  })

  it('TC-UNIT-933 / AC-235-01、AC-234-04：仅"我的身份与房屋"二级项带 pendingReview 角标；对所有受众可见（游客与非产权业主也看得到菜单，卡片由页面控制）', () => {
    const guestMenu = visibleMenu(PORTAL_MENU, { isCommittee: false })
    const children = guestMenu.find((n) => n.key === 'units').children
    expect(children).toHaveLength(5)
    expect(children.filter((c) => c.badge).map((c) => c.label)).toEqual(['我的身份与房屋'])
  })
})

describe('路由（integration）', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    http.get.mockResolvedValue({ theme: null })
    adminHttp.get.mockResolvedValue({ theme: null })
    await router.push('/login')
    await flushPromises()
  })
  afterEach(() => { delete window.matchMedia })

  it('TC-INT-970 / AC-233-02、AC-233-03：/me/identity 与 /units 解析为同一页面组件、同一 section，且直接显示不跳转（地址栏保持所访问的地址）', async () => {
    localStorage.setItem('ocap_token', 'tok')
    const a = recordOf('/me/identity').last
    const b = recordOf('/units').last
    expect(a.components.default).toBe(b.components.default)
    expect(a.props.default.section).toBe('identity')
    expect(b.props.default.section).toBe('identity')
    for (const p of ['/me/identity', '/units']) {
      await router.push(p)
      await flushPromises()
      expect(router.currentRoute.value.fullPath).toBe(p)
      expect(router.currentRoute.value.matched.length).toBeGreaterThan(0)
      expect(router.currentRoute.value.matched.at(-1).path).not.toContain('pathMatch') // 非 404 兜底
    }
  })

  it('TC-INT-971 / AC-233-02：从 / 点进 /me/identity 后后退一次回到 /（无中间跳转历史）', async () => {
    localStorage.setItem('ocap_token', 'tok')
    await router.push('/')
    await flushPromises()
    await router.push('/me/identity')
    await flushPromises()
    router.back()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/'))
  })

  it('TC-INT-972 / AC-235-03：/units/review 与 /units#review 都到达"我的身份与房屋"页并带 #review 定位；不出现 404', async () => {
    localStorage.setItem('ocap_token', 'tok')
    for (const p of ['/units/review', '/units#review']) {
      await router.push(p)
      await flushPromises()
      expect(router.currentRoute.value.path, p).toBe('/units')
      expect(router.currentRoute.value.hash, p).toBe('#review')
    }
  })

  it('TC-INT-973 / AC-236-03：旧书签 /units/pick 仍到达"认证产权"分区；其余 /units/* 兼容路径可解析', () => {
    expect(recordOf('/units/pick').last.props.default.section).toBe('pick')
    for (const s of ['appeal', 'applications', 'appeals']) expect(recordOf(`/units/${s}`).last.props.default.section).toBe(s)
  })

  it('TC-INT-974 / AC-233-03：未登录访问 /me/identity 与 /units 被带去登录页并保留 redirect（守卫仍生效）', async () => {
    for (const p of ['/me/identity', '/units']) {
      await router.push(p)
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/login')
      expect(router.currentRoute.value.query.redirect).toBe(p)
      await router.push('/login')
    }
  })
})
