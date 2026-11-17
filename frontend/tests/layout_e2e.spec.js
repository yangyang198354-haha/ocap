// ocap_brand_layout GROUP_D PHASE_09：端到端用户旅程（替代口径）。
// critical path 口径：替代——无浏览器 E2E 框架（画像 P4 无 Playwright），用 vitest + jsdom 挂载真实 App + 真实路由 + 真实页面 + 真实 api.js，
// HTTP 层用"带状态的假服务端"；多步旅程等价于最高层可执行的端到端用例。真实视口度量、字体渲染、WXSS 真机见 e2e_test_report 人工验证清单。
// 溯源：Must Have 故事 US-207~216、218~220、222~227、229~231 的跨页旅程。TC-E2E-801 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('@/shared/confirm', () => ({ confirmDanger: vi.fn().mockResolvedValue(true) }))

import App from '@/App.vue'
import router from '@/router'
import Login from '@/portal/Login.vue'
import AdminLogin from '@/admin/AdminLogin.vue'

const { http, adminHttp } = mocked
vi.setConfig({ testTimeout: 60000 })
const html = () => document.documentElement
const INLINE = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1]

// 视口桩：宽屏（≥768px）matchMedia 命中；窄屏不提供 matchMedia（jsdom 缺省，按窄屏）
function setViewport(wide) {
  if (wide) {
    window.matchMedia = vi.fn((q) => ({ matches: q === '(min-width: 768px)', media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
  } else {
    delete window.matchMedia
  }
}
async function mountApp() {
  new Function(INLINE)() // 与真实页面加载一致：先执行首屏风格脚本
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(App, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}
async function go(p) {
  await router.push(p)
  await vi.waitFor(async () => { await flushPromises(); expect(router.currentRoute.value.fullPath).toBe(router.currentRoute.value.fullPath) })
  await flushPromises()
  await flushPromises()
  await new Promise((r) => setTimeout(r, 0))
  await flushPromises()
}
const settle = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const side = (wrapper) => wrapper.find('aside.side')
const topLabels = (wrapper) => side(wrapper).findAll('.side-nav > .side-item .side-label').map((e) => e.text())
const toggle = (wrapper, label) => side(wrapper).findAll('button.side-group-toggle').find((b) => b.text().includes(label))
const sub = (wrapper, label) => side(wrapper).findAll('.side-sub-item').find((a) => a.text().includes(label))
const dropdownItem = (text) => [...document.body.querySelectorAll('.el-dropdown-menu__item')].find((e) => e.textContent.includes(text))

// ---------------------------------------------------------------- 假服务端
const HEAD_UNIT = { unit_id: 1, specific_part: '1栋1单元3层301号', role: 'HEAD', role_label: '户主', certified_at: '2026-01-01T00:00:00+08:00', residents: [], pending_application_count: 0 }
let S
const PENDING = () => [
  { id: 8, unit: { unit_id: 1, specific_part: '1栋1单元3层301号' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { id: 3, nickname: '小王', account_no: '1000000003' } },
  { id: 9, unit: { unit_id: 1, specific_part: '1栋1单元3层301号' }, status: 'PENDING', created_at: '2026-11-13T20:31:00+08:00', applicant: { id: 4, nickname: '小李', account_no: '1000000004' } }
]
function installPortalServer(accounts) {
  S = { pending: PENDING(), nickname: '小明', theme: null, resolutionScopes: [], logins: [], puts: [] }
  const who = () => Object.values(accounts).find((a) => a.token === localStorage.getItem('ocap_token'))
  const me = () => ({
    profile: { id: who().id, nickname: S.nickname, phone: '138****0000' },
    identities: {
      is_guest: false, units: [{ ...HEAD_UNIT }], labels: ['户主'], summary: { code: 'HEAD', label: '户主' },
      committee: who().committee ? { position: 'MEMBER', term_end: '2027-01-01' } : null
    }
  })
  http.post.mockImplementation(async (url, body) => {
    if (url === '/auth/login/password') {
      const acc = accounts[body.identifier]
      if (!acc) throw { code: 'LOGIN_FAILED', message: '账号或密码错误' }
      S.logins.push(body)
      return { token: acc.token, user: { id: acc.id }, is_new: false }
    }
    if (url === '/auth/logout') return {}
    const decision = url.match(/^\/resident-applications\/(\d+)\/decision$/)
    if (decision) { S.pending = S.pending.filter((r) => r.id !== Number(decision[1])); return {} }
    throw new Error(`未预期 POST ${url}`)
  })
  http.get.mockImplementation(async (url, arg) => {
    if (url === '/me') return me()
    if (url === '/me/theme') return { theme: S.theme }
    if (url === '/me/profile') return { account_no: '1000000001', nickname: S.nickname, gender: 0, birthday: null, phone: '138****0000', email: null, avatar_url: '' }
    if (url === '/me/housing') return { summary: { code: 'HEAD', label: '户主' }, units: [HEAD_UNIT], pending_review_count: S.pending.length }
    if (url === '/resident-applications/to-review') return S.pending
    if (url === '/resident-applications/mine' || url === '/appeals/mine') return []
    if (url === '/resolutions') { S.resolutionScopes.push(arg?.params?.scope); return { count: 1, results: [{ id: 12, title: '更换电梯', status: 'APPROVED' }] } }
    if (url === '/claims') return { count: 0, results: [] }
    if (url === '/info/posts') return { count: 0, results: [] }
    if (url.startsWith('/resolutions/')) return { id: 12, title: '更换电梯', content: 'x', status: 'APPROVED' }
    throw new Error('WECHAT_UNAVAILABLE')
  })
  http.put.mockImplementation(async (url, body) => {
    if (url === '/me/theme') { S.theme = body.theme; S.puts.push(body.theme); return { theme: body.theme } }
    throw new Error(`未预期 PUT ${url}`)
  })
  http.patch.mockImplementation(async (url, body) => {
    if (url === '/me/profile') { S.nickname = body.nickname; return { nickname: body.nickname } }
    throw new Error(`未预期 PATCH ${url}`)
  })
}
async function loginAs(wrapper, identifier) {
  await go('/login')
  const login = wrapper.findComponent(Login)
  login.vm.form.identifier = identifier
  login.vm.form.password = 'Ocap2026pass'
  await login.vm.loginPassword()
  await vi.waitFor(() => expect(router.currentRoute.value.path).not.toBe('/login'), { timeout: 8000 })
  await settle()
  await settle()
}

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(async () => {
  vi.clearAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  html().removeAttribute('data-theme')
  html().classList.remove('dark')
  setViewport(true)
  await router.replace('/login').catch(() => {})
})
afterEach(() => { delete window.matchMedia })

describe('TC-E2E-801 用户端宽屏旅程（业委会成员）', () => {
  it('登录页品牌 → 登录 → 左侧导航展开/高亮 → 二级分区 → 审批并更新角标 → 右上角菜单进入个人资料并改昵称 → 旧地址兼容 → 退出', async () => {
    const accounts = { alice: { id: 1, token: 'TA', committee: true } }
    installPortalServer(accounts)
    localStorage.setItem('ocap_theme', 'neon') // 设备记忆：霓虹玻璃（AC-209-01）
    const wrapper = await mountApp()

    // 1 登录页：品牌名 + neon 配图 + 无风格入口 + 静态标题（US-207、US-209、AC-207-01/03、AC-209-01/02）
    await go('/login')
    expect(html().getAttribute('data-theme')).toBe('neon')
    expect(wrapper.find('h1.auth-brand').text()).toBe('Cyber@红枫岭')
    expect(wrapper.find('.auth-art svg').classes()).toContain('neon-art')
    expect(wrapper.text()).not.toContain('业主委员会 · 登录')
    expect(wrapper.find('[role=radio]').exists()).toBe(false)
    expect(wrapper.findAll('.el-tabs__item').map((t) => t.text())).toEqual(['验证码', '密码', '邮箱'])

    // 2 登录 → 主页：9 个一级、全部二级收起、右上角昵称（US-210/211/212/216，AC-210-01、AC-216-01、AC-212-01）
    await loginAs(wrapper, 'alice')
    expect(router.currentRoute.value.path).toBe('/')
    expect(S.logins).toEqual([{ identifier: 'alice', password: 'Ocap2026pass', remember_me: false }])
    expect(side(wrapper).find('.side-brand').text()).toBe('Cyber@红枫岭')
    expect(topLabels(wrapper)).toEqual(['主页', '我的房屋', '决议', '投票/调查', '报销/备用金', '收入表', '财务报表', '待办', '信息公开'])
    expect(side(wrapper).findAll('ul.side-sub')).toHaveLength(0)
    expect(wrapper.find('header.topbar .user-menu-name').text()).toBe('小明')
    expect(wrapper.find('header.topbar .topnav').exists()).toBe(false)
    expect(document.title).not.toContain('业主委员会')

    // 3 决议：点击展开不导航 → 我发起的（scope=mine）→ 详情页仍高亮"决议"且二级无高亮（US-215、AC-216-02、AC-215-01/04）
    await toggle(wrapper, '决议').trigger('click')
    expect(router.currentRoute.value.path).toBe('/')
    expect(side(wrapper).findAll('.side-sub-item')).toHaveLength(3)
    await sub(wrapper, '我发起的').trigger('click')
    await settle()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/resolutions/mine'))
    await settle()
    expect(S.resolutionScopes.at(-1)).toBe('mine')
    expect(wrapper.find('.el-radio-group').exists()).toBe(false)
    expect(side(wrapper).find('.side-sub-item.is-active').text()).toContain('我发起的')
    await go('/resolutions/12')
    expect(side(wrapper).findAll('.side-item.is-active .side-label').map((e) => e.text())).toEqual(['决议'])
    expect(side(wrapper).findAll('.side-sub-item.is-active')).toHaveLength(0)

    // 4 我的房屋：同时只展开一个（AC-216-03）；二级项 5 个（AC-236-01）；"我的身份与房屋"项带角标 2，页面底部嵌入待审批卡片；通过一条后角标变 1
    // 改写：旧"点二级项'待我审批'进入 /units/review、其页只有一个标题块" → 新"点'我的身份与房屋'进入 /units，页面含身份卡 + 底部待审批卡"（ADR-133、AC-234-01、AC-235-01）
    await toggle(wrapper, '我的房屋').trigger('click')
    expect(toggle(wrapper, '决议').attributes('aria-expanded')).toBe('false')
    expect(side(wrapper).findAll('.side-sub-item')).toHaveLength(5)
    expect(sub(wrapper, '待我审批')).toBeUndefined()
    // 注：刚登录时侧栏角标数据尚未取到，进入任一 /units* 页前不显示——该缺陷见 TC-INT-914（DEF-002），此处按"进入后"断言
    await sub(wrapper, '我的身份与房屋').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units'))
    await settle()
    expect(wrapper.find('h3.title').text()).toContain('我的身份与房屋')
    expect(sub(wrapper, '我的身份与房屋').find('.side-badge').text()).toBe('2')
    expect(wrapper.find('main').text()).toContain('小王 → 1栋1单元3层301号')
    expect(wrapper.find('main').findAll('h3.title').map((h) => h.text().replace(/\s*\d+$/, ''))).toEqual(['我的身份与房屋', '待我审批的同住人申请']) // 待审批卡片在最底部（AC-234-01）
    const approve = wrapper.findAll('button').find((b) => b.text() === '通过')
    await approve.trigger('click')
    await settle()
    expect(http.post).toHaveBeenCalledWith('/resident-applications/8/decision', { decision: 'APPROVE' })
    expect(sub(wrapper, '我的身份与房屋').find('.side-badge').text()).toBe('1')

    // 5 信息公开：无二级项一次点击直达（US-229、AC-229-01、AC-217-01）
    await side(wrapper).findAll('a.side-item').find((a) => a.text().includes('信息公开')).trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/info'))
    await settle()
    expect(side(wrapper).findAll('.side-item.is-active .side-label').map((e) => e.text())).toEqual(['信息公开'])
    expect(side(wrapper).findAll('ul.side-sub')).toHaveLength(0)

    // 6 右上角菜单：8 项；进入个人资料独立页并改昵称，右上角即时更新（US-212/213、AC-212-02/05、AC-213-01）
    await wrapper.find('header.topbar button.user-menu-trigger').trigger('click')
    await settle()
    expect([...document.body.querySelectorAll('.el-dropdown-menu__item')].map((e) => e.textContent.trim())).toEqual(
      ['界面风格', '我的身份与房屋', '个人资料', '手机号', '设置密码', '邮箱验证', '账号注销', '退出登录'] // 改写：第 2 项改名（AC-233-01）
    )
    dropdownItem('个人资料').click()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/me/profile'))
    await settle()
    expect(wrapper.findAll('h3.title').map((h) => h.text())).toEqual(['个人资料'])
    expect(side(wrapper).findAll('.side-item.is-active')).toHaveLength(0) // 个人中心页不高亮任何一级
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    await wrapper.find('input[placeholder="昵称"]').setValue('小红')
    await wrapper.findAll('button').find((b) => b.text() === '保存').trigger('click')
    await settle()
    expect(http.patch).toHaveBeenCalledWith('/me/profile', { nickname: '小红', gender: 0, birthday: null })
    expect(wrapper.find('header.topbar .user-menu-name').text()).toBe('小红')

    // 7 界面风格页：选风格 C，立即生效并保存（AC-213-06、AC-222-02）
    dropdownItem('界面风格').click()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/me/style'))
    await settle()
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await settle()
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(S.puts).toEqual(['terminal'])

    // 8 旧地址兼容：/units#review 与 /units/review → /units（同页，AC-235-03）；/me/identity 同页不跳转（AC-233-03）；/me（宽屏）→ /me/profile；未知地址 → /（AC-221-01、AC-210-04）
    // 改写：旧 /units#review → /units/review（独立二级页）
    await go('/units#review')
    expect(router.currentRoute.value.path).toBe('/units')
    await go('/units/review')
    expect(router.currentRoute.value.path).toBe('/units')
    expect(router.currentRoute.value.hash).toBe('#review')
    await go('/me/identity')
    expect(router.currentRoute.value.path).toBe('/me/identity')
    expect(wrapper.find('main h3.title').text()).toContain('我的身份与房屋')
    await go('/me')
    expect(router.currentRoute.value.path).toBe('/me/profile')
    await go('/no/such/page')
    expect(router.currentRoute.value.path).toBe('/')

    // 9 退出登录：清登录态，回 /login，设备风格记忆保留，登录页用 terminal 版（AC-212-03、AC-209-01）
    await wrapper.find('header.topbar button.user-menu-trigger').trigger('click')
    await settle()
    dropdownItem('退出登录').click()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))
    await settle()
    expect(localStorage.getItem('ocap_token')).toBeNull()
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    expect(wrapper.find('.auth-art svg').classes()).toContain('terminal-art')
    await go('/units')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/units')
    wrapper.unmount()
  }, 60000)
})

describe('TC-E2E-802 用户端旅程：非业委会成员与窄屏', () => {
  it('非成员只见 6 项菜单且直达 /claims 不白屏；窄屏 /me 进"我的"总览，7 项入口 + 退出登录，一次点击进入个人资料页', async () => {
    const accounts = { bob: { id: 2, token: 'TB', committee: false } }
    installPortalServer(accounts)
    setViewport(false) // 窄屏（<768px）：jsdom 无 matchMedia，按窄屏
    const wrapper = await mountApp()
    await loginAs(wrapper, 'bob')
    // 1 非业委会成员（US-211、AC-211-01）
    expect(topLabels(wrapper)).toEqual(['主页', '我的房屋', '决议', '投票/调查', '财务报表', '信息公开'])
    expect(wrapper.find('nav.tabbar').exists()).toBe(true)
    expect(wrapper.findAll('nav.tabbar a').map((a) => a.text())).toEqual(['首页', '决议', '投票', '我的']) // 非成员无"报销"（AC-220-01）
    // 2 直达 /claims 行为与改动前一致：页面能渲染，不出现新增按钮（AC-211-03）
    await go('/claims')
    expect(router.currentRoute.value.path).toBe('/claims')
    expect(wrapper.find('h3.title').text()).toBe('报销 / 备用金')
    expect(wrapper.findAll('button').find((b) => b.text().includes('新建申请'))).toBeUndefined()
    // 3 窄屏二级切换条：我的房屋 5 项（改写：旧 6 项，AC-236-04），点"我的申诉"只显示该项（US-230、AC-230-01）
    await go('/units')
    expect(wrapper.findAll('nav.sub-nav-bar .sub-nav-item')).toHaveLength(5)
    expect(wrapper.find('nav.sub-nav-bar').text()).not.toContain('选择房屋')
    await wrapper.findAll('nav.sub-nav-bar a').find((a) => a.text() === '我的申诉').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/appeals'))
    await settle()
    expect(wrapper.find('main').findAll('h3.title').map((h) => h.text())).toEqual(['我的申诉'])
    expect(wrapper.find('nav.sub-nav-bar .sub-nav-item.is-active').text()).toBe('我的申诉')
    // 4 底部"我的" → /me 总览（窄屏不重定向）：7 项 + 退出登录（US-220、AC-220-02/05）
    await wrapper.findAll('nav.tabbar a').find((a) => a.text() === '我的').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/me'))
    await settle()
    expect(wrapper.findAll('nav.me-overview > *')).toHaveLength(8)
    // 5 进入个人资料独立页，再点底部"我的"回到总览（AC-220-03）
    await wrapper.findAll('nav.me-overview a').find((a) => a.text().includes('个人资料')).trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/me/profile'))
    await wrapper.findAll('nav.tabbar a').find((a) => a.text() === '我的').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/me'))
    await settle()
    // 6 退出登录（总览页按钮）
    await wrapper.find('nav.me-overview button.me-logout').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))
    expect(localStorage.getItem('ocap_token')).toBeNull()
    wrapper.unmount()
  }, 60000)
})

// ---------------------------------------------------------------- 管理端
let A
function installAdminServer() {
  A = { theme: 'terminal', puts: [], loggedIn: false } // 账号偏好 terminal：登录对账后与设备记忆一致（账号偏好优先）
  adminHttp.post.mockImplementation(async (url, body) => {
    if (url === '/admin/auth/login') {
      if (body.password !== 'Ocap2026pass') throw { code: 'LOGIN_FAILED', message: '账号或密码错误' }
      A.loggedIn = true
      return { token: 'ATOK', admin: { id: 1, username: body.username } }
    }
    throw new Error(`未预期 admin POST ${url}`)
  })
  adminHttp.get.mockImplementation(async (url) => {
    if (url === '/admin/me/theme') return { theme: A.theme }
    if (url === '/admin/users') return { count: 1, results: [{ id: 1, account_no: '1', phone: null, nickname: '甲', status: 'ACTIVE', identity_label: '游客', certified_units: 0, real_names: [], last_login_at: null }] }
    if (url === '/admin/admins') return [{ id: 1, username: 'admin01', is_active: true }]
    if (url === '/admin/system-config') return { 'claim.amount_max': '1000000.00' }
    return { count: 0, results: [] }
  })
  adminHttp.put.mockImplementation(async (url, body) => {
    if (url === '/admin/me/theme') { A.theme = body.theme; A.puts.push(body.theme); return { theme: body.theme } }
    throw new Error(`未预期 admin PUT ${url}`)
  })
}

describe('TC-E2E-803 管理端旅程', () => {
  it('管理端登录页（独立风格记忆）→ 登录 → 左侧导航 9 项/二级展开/高亮 → 右上角菜单切换风格与账号名 → 窄屏抽屉 → 退出', async () => {
    installAdminServer()
    localStorage.setItem('ocap_theme', 'bento') // 用户端设备记忆不得影响管理端（AC-227-02）
    localStorage.setItem('ocap_admin_theme', 'terminal')
    const wrapper = await mountApp()

    // 1 未登录访问 /admin/seats → /admin/login；登录页品牌 + terminal 版 + 无风格入口（US-227、AC-224-04、AC-227-01/02）
    await go('/admin/seats')
    expect(router.currentRoute.value.path).toBe('/admin/login')
    expect(html().getAttribute('data-theme')).toBe('terminal')
    expect(html().getAttribute('data-surface')).toBe('admin')
    expect(wrapper.find('h1.auth-brand').text()).toBe('Cyber@红枫岭')
    expect(wrapper.find('.auth-sub').text()).toBe('管理后台登录')
    expect(wrapper.find('.auth-art svg').classes()).toContain('terminal-art')
    expect(wrapper.find('[role=radio]').exists()).toBe(false)

    // 2 错误密码：服务端文案、不保存令牌（AC-227-03）
    vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const login = wrapper.findComponent(AdminLogin)
    login.vm.username = 'admin01'
    login.vm.password = 'bad'
    await login.vm.login()
    await settle()
    expect(ElMessage.error).toHaveBeenCalledWith('账号或密码错误')
    expect(localStorage.getItem('ocap_admin_token')).toBeNull()
    // 3 正确登录 → /admin/registry（AC-224-01 入口，重定向不变）
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    login.vm.password = 'Ocap2026pass'
    await login.vm.login()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/registry'))
    await settle()
    await settle()
    expect(localStorage.getItem('ocap_admin_name')).toBe('admin01')

    // 4 管理端布局：品牌位、9 个一级、顶栏无横排导航与退出（US-223/224，AC-223-01、AC-224-01）
    expect(wrapper.find('aside.admin-side .side-brand').text()).toBe('Cyber@红枫岭 · 管理后台')
    expect(wrapper.findAll('aside.admin-side .side-nav > .side-item .side-label').map((e) => e.text())).toEqual(
      ['业主清册', '申诉', '房屋关系', '业委会席位', '审批流程', '财务', '账号', '内容管理', '审计/配置']
    )
    expect(wrapper.find('header.admin-bar .topnav').exists()).toBe(false)
    expect(wrapper.find('aside.admin-side').findAll('ul.side-sub')).toHaveLength(0) // AC-225-01 默认收起
    expect(wrapper.find('header.admin-bar .user-menu-name').text()).toBe('admin01')

    // 5 账号 › 注册用户（US-225，AC-225-01/04）
    const adminSide = () => wrapper.find('aside.admin-side')
    await adminSide().findAll('button.side-group-toggle').find((b) => b.text().includes('账号')).trigger('click')
    expect(adminSide().findAll('.side-sub-item').map((a) => a.text())).toEqual(['管理员账号', '注册用户'])
    await adminSide().findAll('.side-sub-item').find((a) => a.text() === '注册用户').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/users/registered'))
    await settle()
    expect(wrapper.findAll('h3').map((h) => h.text())).toContain('注册用户')
    expect(wrapper.text()).not.toContain('新建管理员')
    expect(adminSide().find('.side-sub-item.is-active').text()).toBe('注册用户')

    // 6 内容管理 7 项；编辑页高亮"信息公开"（AC-225-02、AC-224-02）
    await go('/admin/content/posts/12')
    expect(adminSide().findAll('.side-sub-item')).toHaveLength(7)
    expect(adminSide().find('.side-sub-item.is-active').text()).toBe('信息公开')

    // 7 右上角菜单：3 风格 + 退出登录，当前项"已选"；切换风格保存并立即生效，用户端设备键不变（US-226，AC-226-02/03、AC-222-03）
    await wrapper.find('header.admin-bar button.user-menu-trigger').trigger('click')
    await settle()
    const items = () => [...document.body.querySelectorAll('.el-dropdown-menu__item')].map((e) => e.textContent.replace(/\s+/g, ''))
    expect(items()).toEqual(['霓虹玻璃', '极光Bento', '赛博终端已选', '退出登录'])
    dropdownItem('霓虹玻璃').click()
    await settle()
    expect(A.puts).toEqual(['neon'])
    expect(html().getAttribute('data-theme')).toBe('neon')
    expect(localStorage.getItem('ocap_admin_theme')).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('bento')
    expect(items()).toContain('霓虹玻璃已选')

    // 8 窄屏：菜单键唤出抽屉，点二级项后关闭（US-231，AC-231-03）
    setViewport(false)
    await wrapper.find('header.admin-bar .admin-menu-btn').trigger('click')
    await settle()
    const drawer = wrapper.findComponent({ name: 'ElDrawer' })
    expect(drawer.props('modelValue')).toBe(true)
    const drawerNav = document.body.querySelector('.admin-drawer .side-nav')
    expect(drawerNav.querySelectorAll(':scope > .side-item')).toHaveLength(9)
    ;[...drawerNav.querySelectorAll('button.side-group-toggle')].find((b) => b.textContent.includes('审计')).click()
    await settle()
    ;[...document.body.querySelectorAll('.admin-drawer .side-sub-item')].find((a) => a.textContent.includes('审计日志')).click()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/audit/logs'))
    await settle()
    expect(drawer.props('modelValue')).toBe(false)

    // 9 退出：令牌与账号名清除，回 /admin/login；再访问 /admin/registry 被拦（AC-226-04）
    await wrapper.find('header.admin-bar button.user-menu-trigger').trigger('click')
    await settle()
    dropdownItem('退出登录').click()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/login'))
    await settle()
    expect(localStorage.getItem('ocap_admin_token')).toBeNull()
    expect(localStorage.getItem('ocap_admin_name')).toBeNull()
    await go('/admin/registry')
    expect(router.currentRoute.value.path).toBe('/admin/login')
    wrapper.unmount()
  }, 60000)
})
