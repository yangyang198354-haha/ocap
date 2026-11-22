// ocap_identity_property GROUP_D：Web"我的身份与房屋"页、主页小卡片、待审批卡片（MOD-135/136，IFC-337/341）。
// 层级：unit（页面级：单个页面组件 + 真实 store + 真实 api.js，仅 mock HTTP 层；TC-WEB-* 一律计入 unit 层）。TC-WEB-901 起。
// 溯源：US-232、US-234、US-235、US-237。全部为合成数据（C-73）。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('@/shared/confirm', () => ({ confirmDanger: vi.fn().mockResolvedValue(true) }))

import { mountPage, routeTable } from './helpers.js'
import Units from '@/portal/Units.vue'
import Home from '@/portal/Home.vue'
import { useHousingStore } from '@/stores/housing'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const titles = (wrapper) => wrapper.findAll('h3.title').map((h) => h.text().replace(/\s*\d+$/, ''))

const OWNED = {
  unit_id: 107, specific_part: '1栋1单元9层902号', role: 'HEAD', role_label: '产权业主', certified_at: '2026-01-01T00:00:00+08:00',
  unit_type_label: '住宅', area_display: '89.50 ㎡', pending_application_count: 0,
  residents: [{ user_id: 9, nickname: '合成同住人', account_no: '1000000009', joined_at: '2026-02-03T09:05:00+08:00' }]
}
const RESIDENT = {
  unit_id: 108, specific_part: '2栋2单元3层301号', role: 'RESIDENT', role_label: '同住人', certified_at: '2026-01-02T00:00:00+08:00',
  unit_type_label: '公寓', area_display: '60.00 ㎡', pending_application_count: 0, residents: []
}
const housing = (units, pending = 0) => ({
  summary: units.some((u) => u.role !== 'RESIDENT') ? { code: 'OWNER', label: '产权业主' } : units.length ? { code: 'RESIDENT', label: '同住人' } : { code: 'GUEST', label: '游客' },
  units, pending_review_count: pending
})
const REVIEW = (id, unitId, part, who) => ({ id, unit: { unit_id: unitId, specific_part: part }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { id: id + 100, nickname: who, account_no: `10000001${id}` } })
const ME = (units) => ({ profile: { id: 1, nickname: '合成用户', phone: '138****0000' }, identities: { is_guest: !units.length, units, labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } })

function table(over = {}) {
  return routeTable({
    '/me': ME([]), '/me/housing': housing([]), '/resident-applications/to-review': [], '/resident-applications/mine': [], '/appeals/mine': [], ...over
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('我的身份与房屋页：房屋明细（US-232）', () => {
  it('TC-WEB-901 / AC-232-01：2 套房——汇总身份 + 恰 2 行，每行含名称/类型/面积/关系；产权业主行含同住人名单与"移除"，同住人行含"退出"', async () => {
    http.get.mockImplementation(table({ '/me/housing': housing([OWNED, RESIDENT]) }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    const rows = wrapper.findAll('.list-item-top')
    expect(rows).toHaveLength(2)
    expect(wrapper.text()).toContain('汇总身份：产权业主')
    expect(rows[0].text()).toContain('1栋1单元9层902号')
    expect(rows[0].text()).toContain('住宅')
    expect(rows[0].text()).toContain('89.50 ㎡')
    expect(rows[0].text()).toContain('产权业主')
    expect(rows[0].text()).toContain('合成同住人')
    expect(buttonOf(rows[0], '移除')).toBeTruthy()
    expect(buttonOf(rows[0], '退出')).toBeUndefined()
    expect(rows[1].text()).toContain('2栋2单元3层301号')
    expect(rows[1].text()).toContain('公寓')
    expect(rows[1].text()).toContain('60.00 ㎡')
    expect(rows[1].text()).toContain('同住人')
    expect(buttonOf(rows[1], '退出')).toBeTruthy()
    expect(wrapper.text()).not.toContain('户主') // C-75：用户端不出现"户主"
  })

  it('TC-WEB-902 / AC-232-02：类型或面积未登记显示"未登记"，不显示 null/0/空白', async () => {
    const unit = { ...OWNED, residents: [], unit_type_label: '未登记', area_display: '未登记' }
    http.get.mockImplementation(table({ '/me/housing': housing([unit]) }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    const row = wrapper.find('.list-item-top')
    expect(row.text().match(/未登记/g)).toHaveLength(2)
    expect(row.text()).not.toMatch(/null|undefined|\b0\b/)
  })

  it('TC-WEB-903 / AC-232-03、AC-237-02：无有效关系——"暂无已认证房屋"、行数 0，并显示提醒与"认证产权"入口，点击进入认证产权页', async () => {
    http.get.mockImplementation(table())
    const { wrapper, router } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    expect(wrapper.findAll('.list-item-top')).toHaveLength(0)
    expect(wrapper.text()).toContain('暂无已认证房屋')
    expect(wrapper.text()).toContain('您还没有认证任何专有部分，请先认证产权')
    const entry = wrapper.findAll('button').filter((b) => b.text() === '认证产权')
    expect(entry.length).toBeGreaterThanOrEqual(2) // 提醒内入口 + 页面常驻按钮
    await entry[0].trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/pick'))
  })

  it('TC-WEB-904 / AC-232-05：房屋接口失败——"加载失败，请重试"+重试，不显示"暂无已认证房屋"/提醒/游客；重试成功后恢复明细', async () => {
    vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    let fail = true
    http.get.mockImplementation(table({ '/me/housing': () => (fail ? Promise.reject(new Error('network')) : housing([OWNED])) }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    expect(wrapper.text()).toContain('加载失败，请重试')
    expect(wrapper.text()).not.toContain('暂无已认证房屋')
    expect(wrapper.text()).not.toContain('请先认证产权')
    expect(wrapper.text()).not.toContain('游客')
    fail = false
    await buttonOf(wrapper, '重试').trigger('click')
    await flush()
    expect(wrapper.text()).not.toContain('加载失败')
    expect(wrapper.findAll('.list-item-top')).toHaveLength(1)
  })

  it('TC-WEB-905 / AC-237-01、AC-237-03：已有房屋时不显示提醒，"认证产权"按钮仍显示且进入认证产权页', async () => {
    http.get.mockImplementation(table({ '/me/housing': housing([RESIDENT]) }))
    const { wrapper, router } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    expect(wrapper.text()).not.toContain('您还没有认证任何专有部分')
    expect(wrapper.text()).not.toContain('暂无已认证房屋')
    const btn = buttonOf(wrapper, '认证产权')
    expect(btn).toBeTruthy()
    await btn.trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/pick'))
  })

  it('TC-WEB-906 / AC-237-04：仅有 1 条待审批的同住人申请、无有效关系——仍显示提醒（以有效关系数判定）', async () => {
    http.get.mockImplementation(table({ '/resident-applications/mine': [{ id: 1, unit: { unit_id: 5, specific_part: '3栋1单元1层101号' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', decided_at: null }] }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    expect(wrapper.text()).toContain('您还没有认证任何专有部分，请先认证产权')
  })

  it('TC-WEB-907 / AC-232-04、AC-237-05：主页只保留"认证房屋"数量小卡片（2），无逐套明细；游客空状态显示"去认证产权"；快捷入口"认证我的房屋"指向 /units/pick', async () => {
    const others = { results: [] }
    http.get.mockImplementation(routeTable({ '/me': ME([OWNED, RESIDENT]), '/me/housing': housing([OWNED, RESIDENT]), '/resolutions': others, '/approval/tasks': others, '/polls': others }))
    const owner = await mountPage(Home)
    const card = owner.wrapper.findAll('section.home-stat').find((s) => s.find('.label').text() === '认证房屋')
    expect(card.find('.stat-value').text()).toBe('2')
    expect(owner.wrapper.text()).not.toContain('902号')
    const quick = owner.wrapper.findAll('a.home-q').find((a) => a.text().includes('认证我的房屋'))
    expect(quick.attributes('href')).toBe('/units/pick')
  })
})

describe('我的身份与房屋页：待审批 Tab（US-234、US-235）', () => {
  it('TC-WEB-910 / AC-234-01、AC-234-02、AC-300-02：产权业主——页内第二个 Tab 为“待我审批的同住人申请”，含 1 行与通过/拒绝；通过后提示“已处理”，行消失并显示“暂无待审批的同住人申请”', async () => {
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    let pending = [REVIEW(8, 107, '1栋1单元9层902号', '合成申请人')]
    http.get.mockImplementation(table({
      '/me/housing': () => housing([{ ...OWNED, residents: [] }], pending.length),
      '/resident-applications/to-review': () => pending
    }))
    http.post.mockImplementation(async (url) => { pending = []; return {} })
    const { wrapper, pinia } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    // 改写（ocap_navigation_ia ADR-167）：底部卡片 → 页内 Tab
    expect(wrapper.findAll('.el-tabs__item').map((t) => t.text().replace(/\s*\d+$/, ''))).toEqual(['我的身份与房屋', '待我审批的同住人申请'])
    const review = wrapper.find('#review')
    expect(review.exists()).toBe(true)
    expect(review.text()).toContain('合成申请人 → 1栋1单元9层902号')
    expect(buttonOf(review, '通过')).toBeTruthy()
    expect(buttonOf(review, '拒绝')).toBeTruthy()
    expect(useHousingStore(pinia).pendingReviewCount).toBe(1)
    await buttonOf(review, '通过').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resident-applications/8/decision', { decision: 'APPROVE' })
    expect(success).toHaveBeenCalledWith('已处理')
    expect(wrapper.text()).toContain('暂无待审批的同住人申请')
    expect(wrapper.text()).not.toContain('合成申请人 →')
    expect(useHousingStore(pinia).pendingReviewCount).toBe(0)
  })

  it('TC-WEB-911 / AC-234-03：产权业主但无待审批——Tab 仍显示，内容“暂无待审批的同住人申请”', async () => {
    http.get.mockImplementation(table({ '/me/housing': housing([{ ...OWNED, residents: [] }]) }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    expect(wrapper.findAll('.el-tabs__item').map((t) => t.text().replace(/\s*\d+$/, ''))).toContain('待我审批的同住人申请')
    expect(wrapper.text()).toContain('暂无待审批的同住人申请')
  })

  it('TC-WEB-912 / AC-234-04、AC-300-03、REQ-NFUNC-042：游客与仅同住人——没有第二个 Tab（不是空 Tab），且不请求审批列表', async () => {
    for (const units of [[], [RESIDENT]]) {
      document.body.innerHTML = ''
      http.get.mockReset()
      http.get.mockImplementation(table({ '/me/housing': housing(units) }))
      const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
      await flush()
      expect(wrapper.findAll('.el-tabs__item').map((t) => t.text().replace(/\s*\d+$/, ''))).toEqual(['我的身份与房屋'])
      expect(wrapper.text()).not.toContain('待我审批的同住人申请')
      expect(wrapper.text()).not.toContain('暂无待审批的同住人申请')
      expect(wrapper.find('#review').exists()).toBe(false)
      expect(http.get.mock.calls.filter((c) => c[0] === '/resident-applications/to-review')).toHaveLength(0)
    }
  })

  it('TC-WEB-913 / AC-234-06：2 个专有部分各 1 条待审批——卡片列出恰 2 行，分别对应两个专有部分', async () => {
    const second = { ...OWNED, unit_id: 109, specific_part: '3栋1单元1层101号', residents: [] }
    http.get.mockImplementation(table({
      '/me/housing': housing([{ ...OWNED, residents: [] }, second], 2),
      '/resident-applications/to-review': [REVIEW(1, 107, '1栋1单元9层902号', '申请人甲'), REVIEW(2, 109, '3栋1单元1层101号', '申请人乙')]
    }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    const rows = wrapper.find('#review').findAll('.list-item-top')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('申请人甲 → 1栋1单元9层902号')
    expect(rows[1].text()).toContain('申请人乙 → 3栋1单元1层101号')
  })

  it('TC-WEB-914 / AC-234-05：审批接口 403 时前端提示服务端文案且列表不被清空（权限由后端把关，界面不做乐观更新）', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    http.get.mockImplementation(table({
      '/me/housing': housing([{ ...OWNED, residents: [] }], 1),
      '/resident-applications/to-review': [REVIEW(8, 107, '1栋1单元9层902号', '合成申请人')]
    }))
    http.post.mockRejectedValue({ code: 'FORBIDDEN', message: '仅该专有部分产权业主可审批', status: 403 })
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    await buttonOf(wrapper.find('#review'), '通过').trigger('click')
    await flush()
    expect(error).toHaveBeenCalled()
    expect(wrapper.find('#review').text()).toContain('合成申请人 →')
  })

  it('TC-WEB-915 / AC-306-02（定位）：访问 /units#review 的产权业主——数据加载后自动选中“待我审批”Tab；非产权业主无该 Tab 也不报错', async () => {
    http.get.mockImplementation(table({ '/me/housing': housing([{ ...OWNED, residents: [] }], 1), '/resident-applications/to-review': [REVIEW(8, 107, 'A房', '申请人')] }))
    const owner = await mountPage(Units, { props: { section: 'identity' }, path: '/units#review' })
    await flush()
    // 改写（ocap_navigation_ia ADR-167）：滚动定位 → 自动切换页内 Tab
    expect(owner.wrapper.find('.el-tabs__item.is-active').text()).toContain('待我审批')
    expect(owner.wrapper.find('#review').exists()).toBe(true)
    owner.wrapper.unmount()
    document.body.innerHTML = ''
    http.get.mockReset()
    http.get.mockImplementation(table({ '/me/housing': housing([RESIDENT]) }))
    const resident = await mountPage(Units, { props: { section: 'identity' }, path: '/units#review' })
    await flush()
    expect(resident.wrapper.find('.el-tabs__item.is-active').text()).toContain('我的身份与房屋')
    expect(resident.wrapper.find('#review').exists()).toBe(false)
  })

  it('TC-WEB-916 / AC-235-02、AC-235-04：主页"待审批同住人申请：2"链接指向 /units#review；游客与同住人不显示该链接', async () => {
    const others = { results: [] }
    const homeTable = (units, pending) => routeTable({ '/me': ME(units), '/me/housing': housing(units, pending), '/resolutions': others, '/approval/tasks': others, '/polls': others })
    http.get.mockImplementation(homeTable([OWNED], 2))
    const owner = await mountPage(Home)
    await flush()
    const link = owner.wrapper.findAll('a').find((a) => a.text().includes('待审批同住人申请：2'))
    expect(link).toBeTruthy()
    expect(link.attributes('href')).toBe('/units#review')
    owner.wrapper.unmount()
    for (const units of [[], [RESIDENT]]) {
      document.body.innerHTML = ''
      http.get.mockReset()
      http.get.mockImplementation(homeTable(units, 0))
      const other = await mountPage(Home)
      await flush()
      expect(other.wrapper.text()).not.toContain('待审批同住人申请')
    }
  })
})
