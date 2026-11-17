// ocap_brand_layout GROUP_D（MOD-131）：布局与分区页面行为（MOD-121~126）。
// 层级：integration（真实页面 + 真实 router/pinia/api.js，仅 mock HTTP 层；跨组件：布局 ↔ 菜单 ↔ 仓库 ↔ 页面）。TC-INT-881 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus, { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('@/shared/confirm', () => ({ confirmDanger: vi.fn().mockResolvedValue(true) }))

import { mountPage } from './helpers.js'
import PortalLayout from '@/portal/PortalLayout.vue'
import AdminLayout from '@/admin/AdminLayout.vue'
import Units from '@/portal/Units.vue'
import Resolutions from '@/portal/Resolutions.vue'
import Claims from '@/portal/Claims.vue'
import Me from '@/portal/Me.vue'
import MeStyle from '@/portal/me/MeStyle.vue'
import UnitsIdentity from '@/portal/units/UnitsIdentity.vue' // 改写：MeIdentity.vue 已删除（ADR-132），/me/identity 与 /units 同页显示 UnitsIdentity
import MeProfile from '@/portal/me/MeProfile.vue'
import MePhone from '@/portal/me/MePhone.vue'
import MePassword from '@/portal/me/MePassword.vue'
import MeEmail from '@/portal/me/MeEmail.vue'
import MeCancel from '@/portal/me/MeCancel.vue'
import UnitsReview from '@/portal/units/UnitsReview.vue'
import AdminFinance from '@/admin/AdminFinance.vue'
import AdminUsers from '@/admin/AdminUsers.vue'
import AdminAudit from '@/admin/AdminAudit.vue'
import AdminAiServices from '@/admin/AdminAiServices.vue'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'

const { http, adminHttp } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const ME = (position = null, units = [], nickname = '张三') => ({
  profile: { id: 1, nickname, phone: '138****0000' },
  identities: { is_guest: !units.length, units, labels: [], summary: { code: units.length ? 'HEAD' : 'GUEST', label: units.length ? '户主' : '游客' }, committee: position ? { position, term_end: '2027-01-01' } : null }
})
const HEAD_UNIT = { unit_id: 1, specific_part: '1栋1单元3层301号', role: 'HEAD', role_label: '户主', certified_at: '2026-01-01T00:00:00+08:00' }
const getsOf = (client, url) => client.get.mock.calls.filter((c) => c[0] === url)

// 缺省返回空列表，具体用例用 table 覆盖；需要精确断言请求时读 mock.calls
function fakeGet(table = {}) {
  return async (url) => {
    if (url in table) return typeof table[url] === 'function' ? table[url]() : table[url]
    return { count: 0, results: [] }
  }
}

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})
afterEach(() => { delete window.matchMedia; document.body.innerHTML = '' })

// ------------------------------------------------------------------ 用户端布局（MOD-121）
describe('PortalLayout 组合（US-210/211/212/214/220/230）', () => {
  async function mountLayout(path, { me = ME('MEMBER', [HEAD_UNIT]), meDelay = null, housing = { summary: { code: 'HEAD', label: '户主' }, units: [], pending_review_count: 2 } } = {}) {
    http.get.mockImplementation(fakeGet({
      '/me': async () => { if (meDelay) await meDelay; return me },
      '/me/housing': housing
    }))
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }] })
    router.push(path)
    await router.isReady()
    const wrapper = mount(PortalLayout, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    return { wrapper, router, pinia }
  }

  it('TC-INT-881 / AC-210-01、AC-212-01：业委会成员——左侧品牌位"Cyber@红枫岭"链到 /，9 个一级项；顶栏没有横排导航与"退出"按钮，只有右上角用户菜单', async () => {
    const { wrapper } = await mountLayout('/')
    await flush()
    expect(wrapper.find('aside.side .side-brand').text()).toBe('Cyber@红枫岭')
    expect(wrapper.find('aside.side .side-brand').attributes('href')).toBe('/')
    expect(wrapper.findAll('aside.side .side-nav .side-item .side-label').map((e) => e.text())).toEqual(
      ['主页', '我的房屋', '决议', '投票/调查', '报销/备用金', '收入表', '财务报表', '待办', '信息公开']
    )
    expect(wrapper.find('header.topbar nav').exists()).toBe(false)
    expect(wrapper.find('.topnav').exists()).toBe(false)
    expect(wrapper.find('header.topbar').text()).not.toContain('退出')
    expect(wrapper.find('header.topbar .topbar-user button.user-menu-trigger').text()).toBe('张三')
    wrapper.unmount()
  })

  it('TC-INT-882 / AC-211-01：产权业主（非业委会成员）——一级菜单恰 6 项，窄屏底栏 4 项（无"报销"）', async () => {
    const { wrapper } = await mountLayout('/', { me: ME(null, [HEAD_UNIT]) })
    await flush()
    expect(wrapper.findAll('aside.side .side-nav .side-item .side-label').map((e) => e.text())).toEqual(
      ['主页', '我的房屋', '决议', '投票/调查', '财务报表', '信息公开']
    )
    expect(wrapper.findAll('nav.tabbar a').map((a) => a.text())).toEqual(['首页', '决议', '投票', '我的'])
    wrapper.unmount()
  })

  it('TC-INT-883 / AC-211-04：/me 尚未返回时先显示全员 6 项，不闪现业委会专属项；返回后补充为 9 项', async () => {
    let release
    const gate = new Promise((r) => { release = r })
    const { wrapper } = await mountLayout('/', { meDelay: gate })
    await flushPromises()
    expect(wrapper.findAll('aside.side .side-nav .side-item')).toHaveLength(6)
    for (const t of ['报销/备用金', '收入表', '待办']) expect(wrapper.find('aside.side').text()).not.toContain(t)
    release()
    await flush()
    expect(wrapper.findAll('aside.side .side-nav .side-item')).toHaveLength(9)
    wrapper.unmount()
  })

  it('TC-INT-884 / AC-211-04：/me 请求失败时保持全员 6 项，页面不白屏', async () => {
    http.get.mockImplementation(async (url) => { if (url === '/me') throw new Error('offline'); return { count: 0, results: [] } })
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }] })
    router.push('/')
    await router.isReady()
    const wrapper = mount(PortalLayout, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    await flush()
    expect(wrapper.findAll('aside.side .side-nav .side-item')).toHaveLength(6)
    expect(wrapper.find('header.topbar .user-menu-name').text()).toBe('业主')
    wrapper.unmount()
  })

  it('TC-INT-885 / AC-235-01（旧 AC-214-03、AC-230-04）：产权业主有 2 条待审批——/units 下侧栏"我的身份与房屋"显示角标 2，窄屏切换条同项同值；首页链接 /units#review 的角标数据来自同一仓库', async () => {
    // 改写：角标由已取消的"待我审批的同住人申请"项移到"我的身份与房屋"项
    const { wrapper, pinia } = await mountLayout('/units', { me: ME('MEMBER', [HEAD_UNIT]) })
    await flush()
    expect(useHousingStore(pinia).pendingReviewCount).toBe(2)
    const sideBadge = wrapper.find('aside.side .side-sub-item .side-badge')
    expect(sideBadge.text()).toBe('2')
    expect(wrapper.find('aside.side .side-sub-item .side-badge').element.closest('a').textContent).toContain('我的身份与房屋')
    expect(wrapper.find('aside.side').text()).not.toContain('待我审批的同住人申请')
    expect(wrapper.find('nav.sub-nav-bar .side-badge').text()).toBe('2')
    wrapper.unmount()
  })

  // DEF-002：登录后 auth.me 先是登录响应里的 user 简要对象（无 identities，backend user_brief），PortalLayout.onMounted 因 me 非空不再 fetchMe，
  // 首页随后自己 fetchMe 补全身份，但侧栏角标只在挂载时和进入 /units* 路由时刷新——此时身份尚无房屋，角标被置 0；
  // 用户展开"我的房屋"看到的二级菜单没有角标，直到进入任一 /units* 页。AC-214-03 要求"存在待审批时查看二级菜单显示角标"。
  it('TC-INT-914 / AC-235-01（旧 AC-214-03）：刚登录（auth.me 为登录响应的简要对象）→ 首页补全身份后展开"我的房屋"，"我的身份与房屋"应显示角标 2（无需先进入 /units*）', async () => {
    http.get.mockImplementation(fakeGet({
      '/me': ME('MEMBER', [HEAD_UNIT]),
      '/me/housing': { summary: { code: 'HEAD', label: '户主' }, units: [], pending_review_count: 2 }
    }))
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore(pinia).setAuth('tok', { id: 1, account_no: '1000000001', nickname: '张三', avatar_url: '', status: 'ACTIVE' }) // 登录后的状态
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }] })
    router.push('/')
    await router.isReady()
    const wrapper = mount(PortalLayout, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    await flush()
    await useAuthStore(pinia).fetchMe() // 首页 onMounted 的 auth.fetchMe()
    await flush()
    await wrapper.findAll('button.side-group-toggle').find((b) => b.text().includes('我的房屋')).trigger('click')
    await flush()
    const badge = wrapper.find('aside.side .side-sub-item .side-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('2')
    expect(badge.element.closest('a').textContent).toContain('我的身份与房屋')
    wrapper.unmount()
  })

  it('TC-INT-886 / AC-214-03：游客无待审批——角标不显示且不请求 /me/housing（静默策略，不弹错误）', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountLayout('/units', { me: ME(null, []) })
    await flush()
    expect(wrapper.findAll('.side-badge')).toHaveLength(0)
    expect(getsOf(http, '/me/housing')).toHaveLength(0)
    expect(error).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('TC-INT-887 / AC-214-03：待审批数为 0 不显示角标；/me/housing 失败时静默置 0，不弹错误', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const zero = await mountLayout('/units', { housing: { summary: { code: 'HEAD', label: '户主' }, units: [], pending_review_count: 0 } })
    await flush()
    expect(zero.wrapper.findAll('.side-badge')).toHaveLength(0)
    zero.wrapper.unmount()
    document.body.innerHTML = ''
    http.get.mockImplementation(async (url) => { if (url === '/me') return ME('MEMBER', [HEAD_UNIT]); if (url === '/me/housing') throw new Error('500'); return {} })
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }] })
    router.push('/units')
    await router.isReady()
    const wrapper = mount(PortalLayout, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    await flush()
    expect(useHousingStore(pinia).pendingReviewCount).toBe(0)
    expect(wrapper.findAll('.side-badge')).toHaveLength(0)
    expect(error).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('TC-INT-888 / AC-220-01、AC-230-01、AC-230-02：窄屏结构——布局始终渲染底栏 5 项（成员）、品牌文字 .brand、二级切换条（我的房屋 5 项（旧 6 项，AC-236-04）、决议 3 项、报销 2 项、其他一级无切换条）；显隐由 CSS 控制', async () => {
    const barItems = async (p) => {
      const { wrapper, router } = await mountLayout(p)
      await flush()
      const items = wrapper.findAll('nav.sub-nav-bar a').map((a) => a.find('span').text())
      const out = { items, tabs: wrapper.findAll('nav.tabbar a').map((a) => a.text()), brand: wrapper.find('header.topbar a.brand').text() }
      wrapper.unmount()
      document.body.innerHTML = ''
      void router
      return out
    }
    const units = await barItems('/units/appeals')
    expect(units.items).toEqual(['我的身份与房屋', '认证产权', '认证申诉', '我的同住人申请', '我的申诉'])
    expect(units.tabs).toEqual(['首页', '决议', '投票', '报销', '我的'])
    expect(units.brand).toBe('Cyber@红枫岭')
    expect((await barItems('/resolutions/todo')).items).toEqual(['公开决议', '我发起的', '待我表决'])
    expect((await barItems('/claims')).items).toEqual(['我提交的', '待我审批'])
    for (const p of ['/', '/polls', '/reports', '/info', '/tasks', '/income']) expect((await barItems(p)).items, p).toEqual([])
  }, 30000) // 同一用例内挂载布局 9 次，全量并发运行时需放宽默认 5s

  it('TC-INT-889 / AC-229-03、AC-235-02：首页快捷入口"信息公开"仍指向 /info（改版不使其失效）；待审批链接改指向 /units#review（旧：/units/review）', async () => {
    const home = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/portal/Home.vue'), 'utf8')
    expect(home).toMatch(/label:\s*'信息公开',\s*to:\s*'\/info'/)
    expect(home).toContain('<router-link to="/units#review" class="link">')
    expect(home).not.toContain('to="/units/review"')
    expect(home).toMatch(/label:\s*'认证我的房屋',\s*to:\s*'\/units\/pick'/) // AC-237-05：快捷入口指向"认证产权"页
  })
})

// ------------------------------------------------------------------ 我的房屋分区（MOD-123）
describe('我的房屋分区宿主 Units.vue（US-214）', () => {
  const TITLES = {
    identity: '我的身份与房屋', pick: '认证产权', appeal: '认证申诉', applications: '我的同住人申请', appeals: '我的申诉'
  } // 改写：旧 6 个分区（含 review 与"选择房屋"）→ 新 5 个分区（IFC-340、AC-236-02）

  it('TC-INT-890 / AC-214-02、AC-234-04：5 个分区各只显示自己的卡片，其余不在页面上（游客的身份页无"待我审批"卡片）；缺省与未知分区（含已取消的 review）回退"我的身份与房屋"', async () => {
    http.get.mockImplementation(fakeGet({ '/me/housing': { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 }, '/units/options': { level: 'building', options: [] } }))
    for (const [section, title] of Object.entries(TITLES)) {
      document.body.innerHTML = ''
      const { wrapper } = await mountPage(Units, { props: { section } })
      await flush()
      const shown = wrapper.findAll('h3.title').map((h) => h.text().replace(/\s*\d+$/, ''))
      expect(shown, section).toEqual([title])
      wrapper.unmount()
    }
    document.body.innerHTML = ''
    const def = await mountPage(Units)
    await flush()
    expect(def.wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['我的身份与房屋'])
    const bad = await mountPage(Units, { props: { section: 'nope' } })
    await flush()
    expect(bad.wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['我的身份与房屋'])
    document.body.innerHTML = ''
    const gone = await mountPage(Units, { props: { section: 'review' } }) // 旧分区 review 已取消
    await flush()
    expect(gone.wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['我的身份与房屋'])
  })

  it('TC-INT-891 / AC-214-02：同一实例在兄弟路由间切换分区（props 变化）——内容随之切换并重新挂载', async () => {
    http.get.mockImplementation(fakeGet({ '/me/housing': { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 } }))
    const { wrapper } = await mountPage(Units, { props: { section: 'applications' } })
    await flush()
    expect(wrapper.find('h3.title').text()).toBe('我的同住人申请')
    await wrapper.setProps({ section: 'appeals' })
    await flush()
    expect(wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['我的申诉'])
    await wrapper.setProps({ section: 'appeal' })
    await flush()
    expect(wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['认证申诉'])
  })

  it('TC-INT-892 / AC-214-03：审批同住人申请成功后刷新仓库，侧栏角标数据随之变化（2 → 1）', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const reviews = [{ id: 8, unit: { unit_id: 1, specific_part: 'A房' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { nickname: '小王' } },
      { id: 9, unit: { unit_id: 1, specific_part: 'A房' }, status: 'PENDING', created_at: '2026-11-13T20:31:00+08:00', applicant: { nickname: '小李' } }]
    let pending = [...reviews]
    http.get.mockImplementation(fakeGet({
      '/resident-applications/to-review': () => pending,
      '/me/housing': () => ({ summary: { code: 'HEAD', label: '户主' }, units: [], pending_review_count: pending.length })
    }))
    http.post.mockImplementation(async (url) => { pending = pending.filter((r) => `/resident-applications/${r.id}/decision` !== url); return {} })
    const { wrapper, pinia } = await mountPage(UnitsReview)
    await flush()
    expect(useHousingStore(pinia).pendingReviewCount).toBe(2)
    expect(wrapper.find('h3.title .el-badge').text()).toBe('2')
    await buttonOf(wrapper, '通过').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resident-applications/8/decision', { decision: 'APPROVE' })
    expect(useHousingStore(pinia).pendingReviewCount).toBe(1)
    expect(wrapper.text()).not.toContain('小王')
    expect(wrapper.text()).toContain('小李')
  })
})

// ------------------------------------------------------------------ 决议与报销分区（MOD-124）
describe('决议、报销二级分区（US-215）', () => {
  it('TC-INT-893 / AC-215-01：决议页按 section 请求 scope（public/mine/todo），页面没有 el-radio-group 切换条；分区标题随之变化', async () => {
    http.get.mockImplementation(fakeGet({ '/me': ME() }))
    for (const [section, title] of [['public', '公开决议'], ['mine', '我发起的'], ['todo', '待我表决']]) {
      document.body.innerHTML = ''
      http.get.mockClear()
      const { wrapper } = await mountPage(Resolutions, { props: { section } })
      await flush()
      expect(getsOf(http, '/resolutions')[0][1].params.scope, section).toBe(section)
      expect(wrapper.find('.el-radio-group').exists()).toBe(false)
      expect(wrapper.find('.section-title').text()).toBe(title)
      wrapper.unmount()
    }
  })

  it('TC-INT-894 / AC-215-01：同一实例切换分区（props 变化）——重新请求新 scope 的列表；缺省与非法分区取 public', async () => {
    http.get.mockImplementation(fakeGet({ '/me': ME() }))
    const { wrapper } = await mountPage(Resolutions, { props: { section: 'public' } })
    await flush()
    http.get.mockClear()
    await wrapper.setProps({ section: 'mine' })
    await flush()
    const calls = getsOf(http, '/resolutions')
    expect(calls.length).toBeGreaterThanOrEqual(1)
    expect(calls.at(-1)[1].params.scope).toBe('mine')
    http.get.mockClear()
    await wrapper.setProps({ section: 'bogus' })
    await flush()
    expect(getsOf(http, '/resolutions').at(-1)[1].params.scope).toBe('public')
  })

  it('TC-INT-895 / AC-215-03、AC-215-02：仅主任/副主任看到"发起决议"；委员与非成员不显示', async () => {
    const seen = {}
    for (const position of ['CHAIR', 'VICE_CHAIR', 'MEMBER', null]) {
      document.body.innerHTML = ''
      http.get.mockImplementation(fakeGet({ '/me': ME(position) }))
      const { wrapper } = await mountPage(Resolutions)
      await flush()
      seen[position] = Boolean(buttonOf(wrapper, '发起决议'))
      wrapper.unmount()
    }
    expect(seen).toEqual({ CHAIR: true, VICE_CHAIR: true, MEMBER: false, null: false })
  })

  it('TC-INT-896 / AC-215-02、AC-211-03：报销页按 section 请求 scope（mine/todo）、无 radio 切换条；业委会成员保留"新建申请""备用金核销"；非成员直接访问不白屏且不显示这两个按钮', async () => {
    http.get.mockImplementation(fakeGet({ '/me': ME('MEMBER') }))
    for (const [section, scope, title] of [['mine', 'mine', '我提交的'], ['todo', 'todo', '待我审批']]) {
      document.body.innerHTML = ''
      http.get.mockClear()
      const { wrapper } = await mountPage(Claims, { props: { section } })
      await flush()
      expect(getsOf(http, '/claims')[0][1].params.scope).toBe(scope)
      expect(wrapper.find('.el-radio-group').exists()).toBe(false)
      expect(wrapper.find('.section-title').text()).toBe(title)
      expect(Boolean(buttonOf(wrapper, '新建申请')), section).toBe(true)
      expect(Boolean(buttonOf(wrapper, '备用金核销')), section).toBe(true)
      wrapper.unmount()
    }
    document.body.innerHTML = ''
    http.get.mockImplementation(fakeGet({ '/me': ME(null) }))
    const guest = await mountPage(Claims, { props: { section: 'mine' } })
    await flush()
    expect(guest.wrapper.find('h3.title').text()).toBe('报销 / 备用金')
    expect(buttonOf(guest.wrapper, '新建申请')).toBeUndefined()
    expect(buttonOf(guest.wrapper, '备用金核销')).toBeUndefined()
  })

  it('TC-INT-897 / AC-215-02：待审批分区不显示"撤回"按钮，我提交的分区对审批中的申请显示"撤回"', async () => {
    const rows = { count: 1, results: [{ id: 5, type: 'REIMBURSEMENT', amount: '10.00', reason: '打印', status: 'PENDING' }] }
    http.get.mockImplementation(fakeGet({ '/me': ME('MEMBER'), '/claims': rows }))
    const mine = await mountPage(Claims, { props: { section: 'mine' } })
    await flush()
    expect(buttonOf(mine.wrapper, '撤回')).toBeTruthy()
    mine.wrapper.unmount()
    document.body.innerHTML = ''
    const todo = await mountPage(Claims, { props: { section: 'todo' } })
    await flush()
    expect(buttonOf(todo.wrapper, '撤回')).toBeUndefined()
  })
})

// ------------------------------------------------------------------ 个人中心拆分（MOD-122）
describe('个人中心各页（US-212/213/220）', () => {
  const profile = { account_no: '1000000001', phone: '138****0000', nickname: '张三', gender: 0, birthday: null, email: 'a@b.cn', avatar_url: '' }
  const base = () => fakeGet({
    '/me': ME(null, [HEAD_UNIT]), '/me/profile': profile, '/me/theme': { theme: null },
    // 真实 /me/housing 的每套均含 residents（IFC-337）；/me/identity 现挂 UnitsIdentity，需要完整夹具
    '/me/housing': { summary: { code: 'HEAD', label: '户主' }, units: [{ ...HEAD_UNIT, residents: [], pending_application_count: 0, unit_type_label: '住宅', area_display: '89.50 ㎡' }], pending_review_count: 0 }
  })

  it('TC-INT-898 / AC-213-01、AC-233-02：7 个个人中心入口对应的页各只含自己的功能块（标题互不相同；旧第 2 页 MeIdentity 已删除，/me/identity 改为我的身份与房屋页，产权业主另含底部待审批卡片），"设置密码"页不含个人资料表单', async () => {
    http.get.mockImplementation(base())
    // 改写：旧第 2 页 [MeIdentity, '身份'] → [UnitsIdentity, '我的身份与房屋']（产权业主页面底部多一张"待我审批的同住人申请"卡片，AC-234-01）
    const pages = [[MeStyle, '界面风格'], [UnitsIdentity, '我的身份与房屋'], [MeProfile, '个人资料'], [MePhone, '更换手机号'], [MePassword, '设置密码'], [MeEmail, '邮箱验证'], [MeCancel, '账号注销']]
    const seen = []
    for (const [comp, title] of pages) {
      document.body.innerHTML = ''
      const { wrapper } = await mountPage(comp)
      await flush()
      const expected = comp === UnitsIdentity ? [title, '待我审批的同住人申请'] : [title]
      expect(wrapper.findAll('h3.title').map((h) => h.text().replace(/\s*\d+$/, '')), title).toEqual(expected)
      seen.push(wrapper.find('h3.title').text())
      wrapper.unmount()
    }
    expect(new Set(seen).size).toBe(7)
    expect(seen).not.toContain('身份')
    document.body.innerHTML = ''
    const pwd = await mountPage(MePassword)
    expect(pwd.wrapper.find('input[placeholder="昵称"]').exists()).toBe(false)
    expect(pwd.wrapper.text()).not.toContain('个人资料')
  })

  it('TC-INT-899 / AC-213-03：已绑定手机号显示"更换手机号"（原号+新号两个验证码），未绑定显示"绑定手机号"，二者互斥', async () => {
    http.get.mockImplementation(fakeGet({ '/me/profile': { ...profile, phone: '138****0000' }, '/me': ME() }))
    const bound = await mountPage(MePhone)
    await flush()
    expect(bound.wrapper.findAll('h3').map((h) => h.text())).toEqual(['更换手机号'])
    expect(bound.wrapper.find('input[placeholder="原号验证码"]').exists()).toBe(true)
    expect(bound.wrapper.find('input[placeholder="新号验证码"]').exists()).toBe(true)
    bound.wrapper.unmount()
    document.body.innerHTML = ''
    http.get.mockImplementation(fakeGet({ '/me/profile': { ...profile, phone: null }, '/me': ME() }))
    const unbound = await mountPage(MePhone)
    await flush()
    expect(unbound.wrapper.findAll('h3').map((h) => h.text())).toEqual(['绑定手机号'])
    expect(unbound.wrapper.find('input[placeholder="原号验证码"]').exists()).toBe(false)
  })

  it('TC-INT-900 / AC-212-05：个人资料页保存成功后刷新 auth.me——昵称在不重新登录的情况下更新（"小明"→"小红"）；保存请求体字段不变', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    let nickname = '小明'
    http.get.mockImplementation(fakeGet({ '/me': () => ME(null, [], nickname), '/me/profile': () => ({ ...profile, nickname }) }))
    http.patch.mockImplementation(async (url, body) => { nickname = body.nickname; return { ...profile, nickname } })
    const { wrapper, pinia } = await mountPage(MeProfile)
    await useAuthStore(pinia).fetchMe()
    await flush()
    expect(useAuthStore(pinia).me.profile.nickname).toBe('小明')
    await wrapper.find('input[placeholder="昵称"]').setValue('小红')
    await buttonOf(wrapper, '保存').trigger('click')
    await flush()
    expect(http.patch).toHaveBeenCalledWith('/me/profile', { nickname: '小红', gender: 0, birthday: null })
    expect(useAuthStore(pinia).me.profile.nickname).toBe('小红')
  })

  it('TC-INT-901 / AC-213-02：昵称保存成功提示"已保存"；3MB png 头像被拒绝提示"头像不能超过 2 MB"且不发上传请求', async () => {
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    http.get.mockImplementation(base())
    http.patch.mockResolvedValue({ ...profile, nickname: '新' })
    const { wrapper } = await mountPage(MeProfile)
    await flush()
    await buttonOf(wrapper, '保存').trigger('click')
    await flush()
    expect(success).toHaveBeenCalledWith('已保存')
    const before = wrapper.findComponent({ name: 'ElUpload' }).props('beforeUpload')
    expect(before({ name: 'a.png', type: 'image/png', size: 3 * 1024 * 1024 })).toBe(false)
    expect(error).toHaveBeenCalledWith('头像不能超过 2 MB')
    expect(http.post.mock.calls.filter((c) => c[0] === '/attachments')).toHaveLength(0)
  })

  it('TC-INT-902 / AC-213-04：设置密码——服务端拒绝不合规密码时原样显示服务端文案，密码输入不被当作成功清空', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    http.get.mockImplementation(base())
    http.put.mockRejectedValue({ code: 'WEAK_PASSWORD', message: '密码须为 8~64 位且包含字母和数字' })
    const { wrapper } = await mountPage(MePassword)
    Object.assign(wrapper.vm.pwd, { current: '', password: 'abc', confirm: 'abc' })
    await wrapper.vm.savePassword()
    await flush()
    expect(http.put).toHaveBeenCalledWith('/me/password', { password: 'abc', password_confirm: 'abc' })
    expect(error).toHaveBeenCalledWith('密码须为 8~64 位且包含字母和数字')
    expect(success).not.toHaveBeenCalled()
    expect(wrapper.vm.pwd.password).toBe('abc')
  })

  it('TC-INT-903 / AC-213-06、AC-222-02：界面风格页点击风格 C 立即生效（PUT /me/theme），页面无保存按钮', async () => {
    http.get.mockImplementation(base())
    http.put.mockResolvedValue({ theme: 'terminal' })
    const { wrapper } = await mountPage(MeStyle)
    await flush()
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flush()
    expect(http.put).toHaveBeenCalledWith('/me/theme', { theme: 'terminal' })
    expect(document.documentElement.getAttribute('data-theme')).toBe('terminal')
    expect(buttonOf(wrapper, '保存')).toBeUndefined()
  })

  it('TC-INT-904 / AC-220-02、AC-220-03：窄屏"我的"总览页——7 项个人中心入口 + "退出登录"共 8 个条目，地址指向 /me/*；退出登录清除登录态并回 /login', async () => {
    http.get.mockImplementation(base())
    http.post.mockResolvedValue({})
    const { wrapper, router } = await mountPage(Me)
    await flush()
    const links = wrapper.findAll('nav.me-overview a')
    expect(links.map((a) => a.find('span').text())).toEqual(['界面风格', '我的身份与房屋', '个人资料', '手机号', '设置密码', '邮箱验证', '账号注销'])
    expect(links.map((a) => a.attributes('href'))).toEqual(['/me/style', '/me/identity', '/me/profile', '/me/phone', '/me/password', '/me/email', '/me/cancel'])
    expect(wrapper.findAll('nav.me-overview > *')).toHaveLength(8)
    expect(wrapper.find('nav.me-overview button.me-logout').text()).toBe('退出登录')
    await wrapper.find('nav.me-overview button.me-logout').trigger('click')
    await flush()
    expect(localStorage.getItem('ocap_token')).toBeNull()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('TC-INT-905 / AC-220-04、AC-220-05：总览页挂载后窗口由窄变宽（matchMedia change）——replace 到 /me/profile；保持窄屏不跳转', async () => {
    http.get.mockImplementation(base())
    let handler = null
    window.matchMedia = vi.fn(() => ({ matches: false, addEventListener: (_e, fn) => { handler = fn }, removeEventListener: vi.fn() }))
    const { wrapper, router } = await mountPage(Me, { path: '/me' })
    await flush()
    expect(router.currentRoute.value.path).toBe('/me')
    expect(handler).toBeTypeOf('function')
    handler({ matches: false })
    await flush()
    expect(router.currentRoute.value.path).toBe('/me')
    handler({ matches: true })
    await flush()
    expect(router.currentRoute.value.path).toBe('/me/profile')
    wrapper.unmount()
  })
})

// ------------------------------------------------------------------ 管理端（MOD-125/126）
describe('管理端 4 页分区（US-225）', () => {
  it('TC-INT-906 / AC-225-03、AC-225-05：财务——claims 分区只含记录表且只请求 /admin/claims；limit 分区只含金额上限卡且只请求 /admin/system-config；切换分区只触发新分区的请求', async () => {
    adminHttp.get.mockImplementation(async (url) => (url === '/admin/system-config' ? { 'claim.amount_max': '1000000.00' } : { count: 0, results: [] }))
    const { wrapper } = await mountPage(AdminFinance, { props: { section: 'claims' } })
    await flush()
    expect(wrapper.find('table').exists() || wrapper.find('.el-table').exists()).toBe(true)
    expect(wrapper.find('.amount-limit-card').exists()).toBe(false)
    expect(getsOf(adminHttp, '/admin/claims').length).toBeGreaterThan(0)
    expect(getsOf(adminHttp, '/admin/system-config')).toHaveLength(0)
    adminHttp.get.mockClear()
    await wrapper.setProps({ section: 'limit' })
    await flush()
    expect(wrapper.find('.amount-limit-card').exists()).toBe(true)
    expect(wrapper.find('.el-table').exists()).toBe(false)
    expect(getsOf(adminHttp, '/admin/system-config').length).toBeGreaterThan(0)
    expect(getsOf(adminHttp, '/admin/claims')).toHaveLength(0)
  })

  it('TC-INT-907 / AC-225-01：账号——admins 分区只请求 /admin/admins 且显示"管理员账号"；registered 分区只请求 /admin/users 且显示"注册用户"；不同时出现', async () => {
    adminHttp.get.mockImplementation(async (url) => (url === '/admin/admins' ? [{ id: 1, username: 'root', is_active: true }] : { count: 0, results: [] }))
    const { wrapper } = await mountPage(AdminUsers, { props: { section: 'admins' } })
    await flush()
    expect(wrapper.findAll('h3').map((h) => h.text())).toEqual(['管理员账号'])
    expect(getsOf(adminHttp, '/admin/users')).toHaveLength(0)
    adminHttp.get.mockClear()
    await wrapper.setProps({ section: 'registered' })
    await flush()
    expect(wrapper.findAll('h3').map((h) => h.text())).toEqual(['注册用户'])
    expect(getsOf(adminHttp, '/admin/users').length).toBeGreaterThan(0)
    expect(getsOf(adminHttp, '/admin/admins')).toHaveLength(0)
  })

  it('TC-INT-908 / AC-225-03：审计/配置——config 分区显示系统配置并读 /admin/system-config/audit.retention_months；logs 分区显示审计日志并读 /admin/audit-logs', async () => {
    adminHttp.get.mockImplementation(async (url) => (url.startsWith('/admin/system-config/') ? { value: 24 } : { count: 0, results: [] }))
    const { wrapper } = await mountPage(AdminAudit, { props: { section: 'config' } })
    await flush()
    expect(getsOf(adminHttp, '/admin/system-config/audit.retention_months')).toHaveLength(1)
    expect(getsOf(adminHttp, '/admin/audit-logs')).toHaveLength(0)
    expect(wrapper.find('.el-table').exists()).toBe(false)
    adminHttp.get.mockClear()
    await wrapper.setProps({ section: 'logs' })
    await flush()
    expect(getsOf(adminHttp, '/admin/audit-logs').length).toBeGreaterThan(0)
    expect(wrapper.find('.el-table').exists()).toBe(true)
  })

  it('TC-INT-909 / AC-225-02：AI 服务——页面不再有 el-tabs；models 分区只请求 /admin/content/services，prompts 分区只请求 /admin/content/prompt-templates 且显示提示词表格', async () => {
    adminHttp.get.mockImplementation(async (url) => (url === '/admin/content/services' ? [] : []))
    const { wrapper } = await mountPage(AdminAiServices, { props: { section: 'models' } })
    await flush()
    expect(wrapper.find('.el-tabs').exists()).toBe(false)
    expect(getsOf(adminHttp, '/admin/content/services')).toHaveLength(1)
    expect(getsOf(adminHttp, '/admin/content/prompt-templates')).toHaveLength(0)
    expect(wrapper.find('h2').text()).toContain('模型与生成服务')
    adminHttp.get.mockClear()
    await wrapper.setProps({ section: 'prompts' })
    await flush()
    expect(wrapper.find('.el-tabs').exists()).toBe(false)
    expect(wrapper.find('.el-table').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('提示词模板')
    expect(getsOf(adminHttp, '/admin/content/prompt-templates')).toHaveLength(1)
    expect(getsOf(adminHttp, '/admin/content/services')).toHaveLength(0)
  })
})

describe('AdminLayout（US-224、231）', () => {
  async function mountAdminLayout(path = '/admin/registry') {
    const pinia = createPinia()
    setActivePinia(pinia)
    adminHttp.get.mockResolvedValue({ theme: null })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }] })
    router.push(path)
    await router.isReady()
    const wrapper = mount(AdminLayout, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    await flush()
    return { wrapper, router, pinia }
  }

  it('TC-INT-910 / AC-224-01、AC-223-01：左侧 9 个一级项；品牌位"Cyber@红枫岭 · 管理后台"链到 /admin；顶栏无横排导航与"退出"按钮；右上角菜单键仅供窄屏（按钮存在，显隐靠 CSS）', async () => {
    const { wrapper } = await mountAdminLayout()
    expect(wrapper.find('aside.admin-side .side-brand').text()).toBe('Cyber@红枫岭 · 管理后台')
    expect(wrapper.find('aside.admin-side .side-brand').attributes('href')).toBe('/admin')
    expect(wrapper.findAll('aside.admin-side .side-nav > .side-item .side-label').map((e) => e.text())).toEqual(
      ['业主清册', '申诉', '房屋关系', '业委会席位', '审批流程', '财务', '账号', '内容管理', '审计/配置']
    )
    expect(wrapper.find('header.admin-bar nav').exists()).toBe(false)
    expect(wrapper.find('header.admin-bar').text()).not.toContain('退出')
    expect(wrapper.find('header.admin-bar .admin-menu-btn').attributes('aria-label')).toBe('打开导航')
    wrapper.unmount()
  })

  it('TC-INT-911 / AC-231-03：窄屏点菜单键唤出抽屉，抽屉内含全部一级菜单；点击二级项（路由变化）后抽屉自动关闭', async () => {
    const { wrapper, router } = await mountAdminLayout()
    const drawer = () => wrapper.findComponent({ name: 'ElDrawer' })
    expect(drawer().props('modelValue')).toBe(false)
    await wrapper.find('.admin-menu-btn').trigger('click')
    await flush()
    expect(drawer().props('modelValue')).toBe(true)
    const nav = document.body.querySelector('.admin-drawer .side-nav')
    expect(nav).toBeTruthy()
    expect(nav.querySelectorAll(':scope > .side-item')).toHaveLength(9)
    ;[...nav.querySelectorAll('button.side-group-toggle')].find((b) => b.textContent.includes('账号')).click()
    await flush()
    const sub = [...document.body.querySelectorAll('.admin-drawer .side-sub-item')].find((a) => a.textContent.includes('注册用户'))
    expect(sub).toBeTruthy()
    sub.click()
    await flush()
    expect(router.currentRoute.value.path).toBe('/admin/users/registered')
    expect(drawer().props('modelValue')).toBe(false)
    wrapper.unmount()
  })

  it('TC-INT-912 / AC-231-04：抽屉打开时窗口变宽（matchMedia change 到 ≥768px）——抽屉关闭，页面内容不丢失（路由保持）', async () => {
    let handler = null
    window.matchMedia = vi.fn(() => ({ matches: false, addEventListener: (_e, fn) => { handler = fn }, removeEventListener: vi.fn() }))
    const { wrapper, router } = await mountAdminLayout('/admin/seats')
    await wrapper.find('.admin-menu-btn').trigger('click')
    await flush()
    const drawer = wrapper.findComponent({ name: 'ElDrawer' })
    expect(drawer.props('modelValue')).toBe(true)
    handler({ matches: true })
    await flush()
    expect(drawer.props('modelValue')).toBe(false)
    expect(router.currentRoute.value.path).toBe('/admin/seats')
    wrapper.unmount()
  })

  it('TC-INT-913 / AC-222-03、AC-224-02：管理端风格与用户端风格互不影响——管理端设备键 ocap_admin_theme 决定管理端；编辑页路径高亮"内容管理"并展开', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    const { wrapper } = await mountAdminLayout('/admin/content/posts/12')
    expect(wrapper.find('aside.admin-side .side-item.is-active .side-label').text()).toBe('内容管理')
    expect(wrapper.find('aside.admin-side .side-sub-item.is-active').text()).toContain('信息公开')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    wrapper.unmount()
  })
})
