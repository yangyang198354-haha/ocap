// ocap_identity_property GROUP_D PHASE_09：Web 端到端用户旅程（替代口径）。
// critical path 口径：替代——无浏览器 E2E 框架（画像 P4 无 Playwright），用 vitest + jsdom 挂载真实 App + 真实路由 + 真实页面 + 真实 api.js，
// HTTP 层用"带状态的假服务端"（接口形状与后端 IFC-332~337 一致，由后端契约/集成用例另行核对）。真实浏览器渲染、真机见 e2e_test_report 人工验证清单。
// 溯源：US-232~243 的跨页旅程。TC-E2E-910 起。合成数据（C-73）。
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
import Register from '@/portal/Register.vue'

const { http, adminHttp } = mocked
vi.setConfig({ testTimeout: 60000 })
const settle = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

function setWide() {
  window.matchMedia = vi.fn((q) => ({ matches: q === '(min-width: 768px)', media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
}
async function mountApp() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(App, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
  await settle()
  return wrapper
}
async function go(p) {
  await router.push(p)
  await settle()
  await settle()
}
const side = (wrapper) => wrapper.find('aside.side')
const subLabels = (wrapper) => side(wrapper).findAll('.side-sub-item').map((a) => a.text().replace(/\d+$/, '').trim())
const toggle = (wrapper, label) => side(wrapper).findAll('button.side-group-toggle').find((b) => b.text().includes(label))
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const mainTitles = (wrapper) => wrapper.find('main').findAll('h1, h2.title').map((h) => h.text().replace(/\s*\d+$/, ''))
const tabLabels = (wrapper) => wrapper.find('main').findAll('.el-tabs__item').map((t) => t.text().replace(/\s*\d+$/, ''))

// ---------------------------------------------------------------- 带状态的假服务端
const POOL = (n) => Array.from({ length: n }, (_, i) => ({ unit_id: 2000 + i, specific_part: `车库B-${i + 1}`, unit_type_label: '车位', area_display: `${10 + i}.00 ㎡` }))
let S
function install({ matches = [], owned = [], residentOf = [], pendingReviews = [], prompt = 'PENDING' } = {}) {
  S = { matches, owned: [...owned], residentOf: [...residentOf], pending: [...pendingReviews], prompt, confirms: [], dismissed: 0, applications: [], applyBodies: [] }
  const isPending = () => S.prompt === 'PENDING' && S.matches.some((m) => !S.owned.some((o) => o.unit_id === m.unit_id))
  const units = () => [...S.owned.map((u) => ({ ...u, role: 'HEAD', role_label: '产权业主', residents: [], pending_application_count: 0 })),
    ...S.residentOf.map((u) => ({ ...u, role: 'RESIDENT', role_label: '同住人', residents: [], pending_application_count: 0 }))]
  const summary = () => (S.owned.length ? { code: 'OWNER', label: '产权业主' } : S.residentOf.length ? { code: 'RESIDENT', label: '同住人' } : { code: 'GUEST', label: '游客' })
  const me = () => ({ profile: { id: 7, nickname: '合成用户', phone: '139****0001' }, identities: { is_guest: !units().length, units: units().map(({ residents, ...u }) => u), labels: [summary().label], summary: summary(), committee: null } })
  http.post.mockImplementation(async (url, body) => {
    if (url === '/auth/register') return { token: 'TOK', user: { id: 7 }, is_new: true, auto_bound: [], registry_match: { pending: S.matches.length > 0, count: S.matches.length } }
    if (url === '/auth/login/password') return { token: 'TOK', user: { id: 7 }, is_new: false }
    if (url === '/auth/logout') return {}
    if (url === '/me/registry-matches/confirm') {
      if (!isPending()) throw { code: 'MATCH_NOT_PENDING', message: '当前没有待确认的清册匹配', status: 409 }
      S.confirms.push(body)
      const chosen = S.matches.filter((m) => body.unit_ids.includes(m.unit_id))
      S.owned.push(...chosen)
      S.prompt = 'DONE'
      return { succeeded: chosen.length, failed: 0, results: chosen.map((c) => ({ unit_id: c.unit_id, specific_part: c.specific_part, ok: true, role: 'HEAD', code: null })) }
    }
    if (url === '/me/registry-matches/dismiss') { S.dismissed += 1; if (S.prompt === 'PENDING') S.prompt = 'DISMISSED'; return null }
    if (url === '/resident-applications') {
      S.applyBodies.push(body)
      const row = { id: 50 + S.applications.length, unit: { unit_id: body.unit_id, specific_part: '2栋2单元3层301号' }, status: 'PENDING', created_at: '2026-11-17T10:00:00+08:00', decided_at: null }
      S.applications.push(row)
      return row
    }
    const decision = url.match(/^\/resident-applications\/(\d+)\/decision$/)
    if (decision) { S.pending = S.pending.filter((r) => r.id !== Number(decision[1])); return {} }
    throw new Error(`未预期 POST ${url}`)
  })
  http.get.mockImplementation(async (url) => {
    if (url === '/me') return me()
    if (url === '/me/theme') return { theme: null }
    if (url === '/me/registry-matches') {
      const open = isPending() ? S.matches.filter((m) => !S.owned.some((o) => o.unit_id === m.unit_id)) : []
      return { pending: open.length > 0, total: open.length, units: open.map(({ unit_id, specific_part, unit_type_label }) => ({ unit_id, specific_part, unit_type_label })) }
    }
    if (url === '/me/housing') return { summary: summary(), units: units(), pending_review_count: S.owned.length ? S.pending.length : 0 }
    // 返回副本：共享同一数组引用会让 Pinia 因引用未变而不触发更新（夹具问题，非产品缺陷）
    if (url === '/resident-applications/to-review') return [...S.pending]
    if (url === '/resident-applications/mine') return [...S.applications]
    if (url === '/appeals/mine') return []
    if (url === '/units/options') return { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] }
    if (url === '/resolutions' || url === '/approval/tasks' || url === '/polls') return { count: 0, results: [] }
    throw new Error(`未预期 GET ${url}`)
  })
}
const REVIEW = [{ id: 8, unit: { unit_id: 2000, specific_part: '车库B-1' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { id: 3, nickname: '申请人甲', account_no: '1000000003' } }]

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(async () => {
  vi.clearAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  setWide()
  await router.replace('/login').catch(() => {})
})
afterEach(() => { delete window.matchMedia })

describe('TC-E2E-910 手机号注册 → 引导 → 确认 → 我的身份与房屋', () => {
  it('注册（匹配 12 套）→ 自动进入认证产权页并显示引导 → 展开更多、取消 2 套 → 确认 10 套 → 两个地址显示同一页（10 行含类型与面积）→ 引导消失、无"自动认证"提示', async () => {
    const pool = POOL(12)
    install({ matches: pool })
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const wrapper = await mountApp()
    await go('/register')
    const reg = wrapper.findComponent(Register)
    reg.vm.form.phone = '13900000001'
    reg.vm.form.code = '123456'
    await reg.vm.submit()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/pick'))
    await settle()
    expect(success).toHaveBeenCalledWith('注册成功')
    expect(success.mock.calls.flat().join('|')).not.toContain('自动认证')
    // 引导页：认证产权、折叠 10 + 展开更多 + 已选 12
    expect(mainTitles(wrapper)).toEqual(['认证产权', '发现您名下的专有部分'])
    expect(wrapper.find('main').text()).toContain('展开更多（还有 2 套）')
    expect(wrapper.find('main').text()).toContain('已选 12 套')
    expect(S.owned).toHaveLength(0) // 未确认前无任何绑定
    await buttonOf(wrapper, '展开更多').trigger('click')
    await settle()
    const boxes = wrapper.findAll('.registry-match input[type=checkbox]')
    expect(boxes).toHaveLength(12)
    await boxes[10].setValue(false)
    await boxes[11].setValue(false)
    await settle()
    expect(wrapper.find('main').text()).toContain('已选 10 套')
    await buttonOf(wrapper, '是，确认认证').trigger('click')
    await settle()
    expect(S.confirms).toEqual([{ unit_ids: pool.slice(0, 10).map((u) => u.unit_id) }])
    expect(wrapper.find('.registry-match').exists()).toBe(false)
    // 左侧二级菜单 3 项（ocap_navigation_ia ADR-166），且无"选择房屋"/"认证产权"（当前在 /units/pick，"我的房屋"已自动展开）
    if (toggle(wrapper, '我的房屋').attributes('aria-expanded') !== 'true') await toggle(wrapper, '我的房屋').trigger('click')
    expect(subLabels(wrapper)).toEqual(['我的身份与房屋', '我的认证与申诉', '我的同住人申请'])
    // 两个地址同页：10 行，含类型与面积，产权业主页内有“待我审批”Tab
    for (const p of ['/me/identity', '/units']) {
      await go(p)
      expect(router.currentRoute.value.path).toBe(p)
      expect(tabLabels(wrapper)).toEqual(['我的身份与房屋', '待我审批的同住人申请'])
      const rows = wrapper.find('main').findAll('.housing-property')
      expect(rows, p).toHaveLength(10)
      expect(rows[0].text()).toContain('车库B-1')
      expect(rows[0].text()).toContain('车位')
      expect(rows[0].text()).toContain('10.00 ㎡')
      expect(wrapper.find('main').text()).not.toContain('您还没有认证任何专有部分')
      expect(side(wrapper).findAll('.side-sub-item.is-active')).toHaveLength(1)
      expect(side(wrapper).find('.side-sub-item.is-active').text()).toContain('我的身份与房屋')
    }
    wrapper.unmount()
  })
})

describe('TC-E2E-911 选择"不是"后不再强制弹出，仍可手动认证入口', () => {
  it('注册 → 引导 → "不是"→ 无绑定、我的身份与房屋页显示提醒 → 再次进入认证产权页不再出现引导 → 主页空状态"去认证产权"', async () => {
    install({ matches: POOL(1) })
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const wrapper = await mountApp()
    await go('/register')
    const reg = wrapper.findComponent(Register)
    reg.vm.form.phone = '13900000001'
    reg.vm.form.code = '123456'
    await reg.vm.submit()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/pick'))
    await settle()
    expect(wrapper.find('main').text()).toContain('我们发现您的手机号登记在 车库B-1（车位）名下，您是该专有部分的业主吗？')
    await buttonOf(wrapper, '不是').trigger('click')
    await settle()
    expect(S.dismissed).toBe(1)
    expect(S.owned).toHaveLength(0)
    expect(wrapper.find('.registry-match').exists()).toBe(false)
    await go('/units')
    expect(wrapper.find('main').text()).toContain('您还没有认证任何专有部分，请先认证产权')
    expect(wrapper.find('main').findAll('.housing-property')).toHaveLength(0)
    expect(mainTitles(wrapper)).toEqual(['我的身份与房屋', '暂无已认证房屋'])
    expect(tabLabels(wrapper)).toEqual(['我的身份与房屋']) // 无待审批 Tab
    await go('/units/pick') // 再次进入不再弹出
    expect(wrapper.find('.registry-match').exists()).toBe(false)
    expect(mainTitles(wrapper)).toEqual(['认证产权'])
    await go('/')
    const homeLink = wrapper.findAll('main a').find((a) => a.text() === '去认证')
    expect(homeLink.attributes('href')).toBe('/units/pick')
    wrapper.unmount()
  })
})

describe('TC-E2E-912 游客：提醒、认证产权入口与同住人申请迁移', () => {
  it('游客在身份页点提醒内"认证产权"→ 认证产权页无同住人按钮 → 经提示链接进入我的同住人申请页 → 选房申请（无姓名）→ 列表出现待审批', async () => {
    install()
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    localStorage.setItem('ocap_token', 'TOK')
    const wrapper = await mountApp()
    await go('/me/identity')
    expect(wrapper.find('main').text()).toContain('您还没有认证任何专有部分，请先认证产权')
    await wrapper.find('main').findAll('button').find((b) => b.text() === '认证产权').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/pick'))
    await settle()
    expect(mainTitles(wrapper)).toEqual(['认证产权'])
    expect(wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').exists()).toBe(true) // AC-238-01
    expect(wrapper.text()).toContain('您本人的姓名')
    expect(buttonOf(wrapper, '申请成为同住人')).toBeUndefined()
    await wrapper.find('main').findAll('a').find((a) => a.text().includes('我的同住人申请')).trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/applications'))
    await settle()
    expect(mainTitles(wrapper)).toEqual(['我的同住人申请'])
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 42)
    await settle()
    await wrapper.find('input[placeholder="本人实名"]').setValue('申请人')
    await buttonOf(wrapper, '申请成为同住人').trigger('click')
    await settle()
    expect(S.applyBodies).toEqual([{ unit_id: 42, applicant_name: '申请人' }])
    expect(wrapper.find('main').text()).toContain('2栋2单元3层301号')
    expect(wrapper.find('main').text()).toContain('待审批')
    wrapper.unmount()
  })
})

describe('TC-E2E-913 待审批：产权业主在身份页底部处理，同住人看不到', () => {
  it('产权业主：菜单"我的身份与房屋"角标 1、主页链接到 /units#review、旧地址 /units/review 到达同页；审批后角标消失。同住人：无卡片、无角标、旧地址到达同页无卡片', async () => {
    install({ owned: [POOL(1)[0]], pendingReviews: REVIEW })
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    localStorage.setItem('ocap_token', 'TOK')
    const wrapper = await mountApp()
    await go('/')
    const link = wrapper.find('main').findAll('a').find((a) => a.text().includes('去处理'))
    expect(link.attributes('href')).toBe('/units')
    await toggle(wrapper, '我的房屋').trigger('click')
    expect(side(wrapper).find('.side-sub-item .side-badge').text()).toBe('1')
    expect(side(wrapper).find('.side-sub-item .side-badge').element.closest('a').textContent).toContain('我的身份与房屋')
    await go('/units/review')
    expect(router.currentRoute.value.path).toBe('/units')
    expect(router.currentRoute.value.query.tab).toBe('review')
    expect(tabLabels(wrapper)).toEqual(['我的身份与房屋', '待我审批的同住人申请'])
    expect(wrapper.find('#review').exists()).toBe(true)
    await buttonOf(wrapper.find('#review'), '通过').trigger('click')
    await settle()
    expect(http.post).toHaveBeenCalledWith('/resident-applications/8/decision', { decision: 'APPROVE' })
    expect(wrapper.find('#review').text()).toContain('暂无待审批的同住人申请')
    expect(side(wrapper).find('.side-sub-item .side-badge').exists()).toBe(false)
    wrapper.unmount()
    document.body.innerHTML = ''

    install({ residentOf: [{ ...POOL(1)[0], unit_id: 3000 }], pendingReviews: REVIEW })
    const resident = await mountApp()
    await go('/units/review')
    expect(router.currentRoute.value.path).toBe('/units')
    expect(tabLabels(resident)).toEqual(['我的身份与房屋'])
    expect(resident.find('#review').exists()).toBe(false)
    await go('/')
    expect(resident.find('main').text()).not.toContain('待我处理')
    expect(toggle(resident, '我的房屋')).toBeTruthy()
    await toggle(resident, '我的房屋').trigger('click')
    expect(side(resident).findAll('.side-badge')).toHaveLength(0)
    resident.unmount()
  })
})
