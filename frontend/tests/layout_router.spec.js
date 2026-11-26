// ocap_brand_layout GROUP_D（MOD-131）：路由表守护（IFC-322，REQ-NFUNC-040 旧路径零回归）。
// 层级：integration（真实 router + 真实守卫 + 风格 store，仅 mock HTTP 层）。TC-INT-821 起。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import router from '@/router'

const { http, adminHttp } = mocked
const recordOf = (path) => {
  const r = router.resolve(path)
  return { r, last: r.matched[r.matched.length - 1] }
}
const sectionOf = (path) => {
  const { last } = recordOf(path)
  const props = last.props.default
  return typeof props === 'object' ? props.section : undefined
}

beforeEach(async () => {
  vi.clearAllMocks()
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  setActivePinia(createPinia())
  http.get.mockResolvedValue({ theme: null })
  adminHttp.get.mockResolvedValue({ theme: null })
  await router.push('/login')
  await flushPromises()
})
afterEach(() => { delete window.matchMedia })

describe('旧路径全部可解析（REQ-NFUNC-040、AC-210-03、AC-224-04）', () => {
  it('TC-INT-821 / AC-210-03：用户端 13 条既有路径均解析到布局路由的子路由，不落入兜底', () => {
    const paths = ['/', '/me', '/units', '/resolutions', '/resolutions/12', '/tasks', '/claims', '/income', '/polls', '/polls/3', '/reports', '/info', '/info/5']
    for (const p of paths) {
      const { r } = recordOf(p)
      expect(r.matched.length, p).toBe(2) // 布局路由 + 页面路由
      expect(r.matched[0].path, p).toBe('/')
      expect(r.matched[1].path, p).not.toContain('pathMatch')
      expect(r.fullPath, p).toBe(p)
    }
  })

  it('TC-INT-822 / AC-224-04：管理端 15 条既有路径一字不变地解析到 /admin 布局的子路由', () => {
    const paths = ['/admin/registry', '/admin/appeals', '/admin/memberships', '/admin/seats', '/admin/flows', '/admin/finance',
      '/admin/users', '/admin/audit', '/admin/content/posts', '/admin/content/posts/12', '/admin/content/styles',
      '/admin/content/media', '/admin/content/services', '/admin/content/platforms', '/admin/content/settings']
    expect(paths).toHaveLength(15)
    for (const p of paths) {
      const { r } = recordOf(p)
      expect(r.matched[0].path, p).toBe('/admin')
      expect(r.matched, p).toHaveLength(2)
      expect(r.matched[0].meta.admin, p).toBe(true)
    }
    expect(recordOf('/admin/login').last.meta).toMatchObject({ public: true, admin: true })
  })

  it('TC-INT-823 / AC-213-01、AC-214-02：新增子路径 /me/* 7 条与 /units/* 5 条全部可解析且地址互不相同', () => {
    const me = ['style', 'identity', 'profile', 'phone', 'password', 'email', 'cancel'].map((k) => `/me/${k}`)
    const units = ['review', 'pick', 'appeal', 'applications', 'appeals'].map((k) => `/units/${k}`)
    for (const p of [...me, ...units]) {
      const { r } = recordOf(p)
      expect(r.matched[0].path, p).toBe('/')
      expect(r.matched[1].path, p).toBe(p.slice(1) ? p : '/')
    }
    expect(new Set([...me, ...units]).size).toBe(12)
  })
})

describe('props.section（AC-214-02、AC-215-01、AC-225-02/03）', () => {
  it('TC-INT-824 / AC-233-03、AC-236-03（旧 AC-214-02）：/units 与 /me/identity 同传 section=identity（同页）；pick/appeal/applications 各自传入对应 section；appeals/review 为重定向', () => {
    // 改写：ocap_navigation_ia ADR-170——/units/appeals → /units/appeal?tab=mine，/units/review → /units?tab=review
    expect(sectionOf('/units')).toBe('identity')
    expect(sectionOf('/me/identity')).toBe('identity')
    expect(recordOf('/me/identity').last.components.default).toBe(recordOf('/units').last.components.default)
    for (const s of ['pick', 'appeal', 'applications']) expect(sectionOf(`/units/${s}`), s).toBe(s)
    expect(recordOf('/units/review').last.redirect).toBeTruthy()
    expect(recordOf('/units/appeals').last.redirect).toBeTruthy()
  })

  it('TC-INT-825 / AC-215-01、AC-215-02：决议 public/mine/todo 与报销 mine/todo', () => {
    expect([sectionOf('/resolutions'), sectionOf('/resolutions/mine'), sectionOf('/resolutions/todo')]).toEqual(['public', 'mine', 'todo'])
    expect([sectionOf('/claims'), sectionOf('/claims/todo')]).toEqual(['mine', 'todo'])
  })

  it('TC-INT-826 / AC-225-02、AC-225-03：管理端 4 页分区的 section', () => {
    expect([sectionOf('/admin/finance'), sectionOf('/admin/finance/limit')]).toEqual(['claims', 'limit'])
    expect([sectionOf('/admin/users'), sectionOf('/admin/users/registered')]).toEqual(['admins', 'registered'])
    expect([sectionOf('/admin/audit'), sectionOf('/admin/audit/logs')]).toEqual(['config', 'logs'])
    expect([sectionOf('/admin/content/services'), sectionOf('/admin/content/services/prompts')]).toEqual(['models', 'prompts'])
  })

  it('TC-INT-827 / AC-215-04：resolutions/mine、resolutions/todo 不被 :id(\\d+) 吞掉；数字 id 仍进详情路由；/resolutions/abc 不匹配详情', () => {
    expect(recordOf('/resolutions/mine').last.path).toBe('/resolutions/mine')
    expect(recordOf('/resolutions/todo').last.path).toBe('/resolutions/todo')
    expect(recordOf('/resolutions/12').last.path).toBe('/resolutions/:id(\\d+)')
    expect(recordOf('/resolutions/12').r.params.id).toBe('12')
    expect(recordOf('/resolutions/abc').last.path).not.toContain(':id')
  })
})

describe('导航守卫与重定向', () => {
  it('TC-INT-828 / AC-210-04：未知地址与 /resolutions/abc 回到 /（已登录），不报错', async () => {
    localStorage.setItem('ocap_token', 'tok')
    for (const p of ['/nope', '/a/b/c', '/resolutions/abc']) {
      await router.push(p)
      await flushPromises()
      expect(router.currentRoute.value.fullPath, p).toBe('/')
    }
  })

  it('TC-INT-829 / AC-221-03、AC-212-03：未登录访问 /me 与 /units 被重定向到 /login?redirect=…', async () => {
    await router.push('/me')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/me')
    await router.push('/units')
    await flushPromises()
    expect(router.currentRoute.value.query.redirect).toBe('/units')
  })

  it('TC-INT-830 / AC-306-02、AC-306-03（旧 AC-235-03、AC-233-03）：/units#review 留在 /units；/units/review 重定向到 /units?tab=review；#appeal → /units/appeal；/me/identity 不跳转；无 hash 留在 /units', async () => {
    // 改写：ocap_navigation_ia ADR-170——待审批改为页内 Tab，/units/review → /units?tab=review
    localStorage.setItem('ocap_token', 'tok')
    await router.push('/units#review')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units')
    expect(router.currentRoute.value.hash).toBe('#review')
    await router.push('/units/review')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units')
    expect(router.currentRoute.value.query.tab).toBe('review')
    expect(router.currentRoute.value.hash).toBe('')
    await router.push('/me/identity')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/me/identity')
    await router.push('/units#appeal')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units/appeal')
    await router.push('/units')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units')
    await router.push('/units#other')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units')
  })

  it('TC-INT-831 / AC-220-05、AC-221-01：/me 窄屏（jsdom 无 matchMedia）停在"我的"总览；宽屏（桩 min-width:768px 命中）进入 /me/profile', async () => {
    localStorage.setItem('ocap_token', 'tok')
    await router.push('/me')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/me')
    await router.push('/login')
    window.matchMedia = vi.fn((q) => ({ matches: q === '(min-width: 768px)', media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
    await router.push('/me')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/me/profile')
    expect(window.matchMedia).toHaveBeenCalledWith('(min-width: 768px)')
    await router.push('/login')
    window.matchMedia = vi.fn((q) => ({ matches: false, media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
    await router.push('/me')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/me') // 767px 一侧
  })

  it('TC-INT-832 / AC-224-04、AC-223-03：无管理端令牌访问 /admin/seats 跳 /admin/login；仅持用户端令牌同样被拒', async () => {
    await router.push('/admin/seats')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/login')
    localStorage.setItem('ocap_token', 'user-tok')
    await router.push('/admin/registry')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/login')
  })

  it('TC-INT-833 / AC-224-04：持管理端令牌时 /admin 重定向到 /admin/registry；/admin/login 为公开路由', async () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    await router.push('/admin')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/registry')
    await router.push('/admin/login')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/login')
  })

  it('TC-INT-834 / AC-207-03：路由切换不设置 document.title（静态标题由 index.html 提供）', async () => {
    localStorage.setItem('ocap_token', 'tok')
    document.title = '赛博@红枫岭'
    for (const p of ['/register', '/login', '/', '/units/review', '/me', '/admin/login']) {
      await router.push(p)
      await flushPromises()
      expect(document.title, p).toBe('赛博@红枫岭')
    }
  })
})
