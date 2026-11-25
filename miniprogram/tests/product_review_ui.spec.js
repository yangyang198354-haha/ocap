// ocap_product_review GROUP_D：小程序页面行为（AC-150-04、151-05、152-04、153-05、156-05、157、161-03、166、168-03）。
// 页面脚本与模板经 @vue/test-utils 编译挂载；uni 为桩（setup.js），不代表微信真机行为。TC-UNIT-551 起。
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { byText, mountPage, requests, respondWith } from './helpers.js'
import Units from '../pages/units/index.vue'
import Index from '../pages/index/index.vue'
import Me from '../pages/me/index.vue'
import Resolutions from '../pages/resolutions/index.vue'
import UnitPicker from '../components/UnitPicker.vue'

const UNIT = { unit_id: 1, specific_part: '1栋1单元3层301号', role: 'HEAD', role_label: '户主' }
const ME = (position = null, units = [UNIT], summary = { code: 'HEAD', label: '户主' }) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: !units.length, units, labels: [], summary, committee: position ? { position, term_end: '2027-01-01' } : null }
})
const housing = (over = {}) => ({
  summary: { code: 'HEAD', label: '户主' }, pending_review_count: 0,
  units: [{ ...UNIT, residents: [], pending_application_count: 0 }], ...over
})
const toasts = () => uni.showToast.mock.calls.map((c) => c[0].title)

describe('小程序 我的房屋（同住人链路）', () => {
  const base = (over = {}) => ({
    'GET /me': ME(), 'GET /me/housing': housing(), 'GET /resident-applications/to-review': [],
    'GET /resident-applications/mine': [], 'GET /appeals/mine': [], 'GET /units/options': { options: [] }, ...over
  })

  it('TC-UNIT-551 / AC-243-01、AC-242-06（旧 AC-150-04）：逐级选房，"我的同住人申请"发起区没有文本输入框；选定后申请只提交 {unit_id} 并提示"申请已提交，等待产权业主审批"', async () => {
    respondWith({ ...base(), 'POST /resident-applications': { id: 9, status: 'PENDING' } })
    const { wrapper } = await mountPage(Units)
    // ocap_owner_auth_v2：认证须输入姓名、申诉须输入产权人名字，仅此两个文本框；仍无专有部分编号输入
    // 改写：旧占位 ['请输入姓名','产权人名字'] → 新 ['请输入您本人的姓名（…）','产权人名字']（AC-238-01）；
    // 页面现有 2 个 UnitPicker：第 1 个属"认证产权"，第 2 个属"我的同住人申请"发起区，申请用第 2 个
    expect(wrapper.findAll('input, textarea').map((el) => el.attributes('placeholder')))
      .toEqual(['请输入您本人的姓名（须与业主清册登记的姓名一致）', '产权人名字'])
    expect(wrapper.text()).not.toMatch(/专有部分 ?ID|内部编号/)
    expect(wrapper.findAllComponents(UnitPicker)).toHaveLength(3)
    wrapper.findAllComponents(UnitPicker)[2].vm.$emit('update:modelValue', 42)
    await flushPromises()
    await byText(wrapper, 'button', '申请成为同住人').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.method === 'POST' && r.path === '/resident-applications')
    expect(post.data).toEqual({ unit_id: 42 })
    expect(toasts()).toContain('申请已提交，等待产权业主审批')
  })

  it('TC-UNIT-552 / AC-151-05、AC-152-04：产权业主在小程序看到待审批并通过；我的申请显示状态与"年-月-日 时:分"', async () => {
    respondWith(base({
      'GET /resident-applications/to-review': [{ id: 4, applicant: { nickname: '小王', phone: '139****0001' }, unit: { specific_part: 'A房' }, created_at: '2026-11-13T20:30:00+08:00' }],
      'GET /resident-applications/mine': [{ id: 1, unit: { specific_part: 'B房' }, status: 'REJECTED', created_at: '2026-11-12T10:00:00+08:00', decided_at: '2026-11-12T11:15:00+08:00' }],
      'POST /resident-applications/4/decision': {}
    }))
    const { wrapper } = await mountPage(Units)
    const text = wrapper.text()
    expect(text).toContain('小王 → A房')
    expect(text).toContain('2026-11-13 20:30')
    expect(text).toContain('已拒绝')
    expect(text).toContain('处理 2026-11-12 11:15')
    expect(text).not.toMatch(/REJECTED|1\d{10}/)
    await byText(wrapper, 'button', '通过').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.path === '/resident-applications/4/decision')
    expect(post.data).toEqual({ decision: 'APPROVE' })
  })

  it('TC-UNIT-553 / AC-153-05：同住人退出——取消不发请求；确认后 POST /units/{id}/leave', async () => {
    const resident = { ...UNIT, role: 'RESIDENT', role_label: '同住人', residents: [], pending_application_count: 0 }
    respondWith(base({
      'GET /me/housing': housing({ summary: { code: 'RESIDENT', label: '同住人' }, units: [resident] }),
      'POST /units/1/leave': {}
    }))
    const { wrapper } = await mountPage(Units)
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: false }))
    await byText(wrapper, 'button', '退出').trigger('click')
    await flushPromises()
    expect(requests().some((r) => r.path === '/units/1/leave')).toBe(false)
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: true }))
    await byText(wrapper, 'button', '退出').trigger('click')
    await flushPromises()
    expect(requests().some((r) => r.method === 'POST' && r.path === '/units/1/leave')).toBe(true)
    expect(uni.showModal.mock.calls[1][0].content).toContain('对象：1栋1单元3层301号')
  })

  it('TC-UNIT-554 / AC-156-05：我的申诉显示状态、处理时间与驳回原因；空态"暂无申诉"', async () => {
    respondWith(base({
      'GET /appeals/mine': [{ id: 3, unit: { specific_part: 'B房' }, status: 'REJECTED', submitted_at: '2026-11-10T08:00:00+08:00', decided_at: '2026-11-11T09:05:00+08:00', reject_reason: '材料不清，请重传' }]
    }))
    let { wrapper } = await mountPage(Units)
    expect(wrapper.text()).toContain('已驳回')
    expect(wrapper.text()).toContain('驳回原因：材料不清，请重传')
    expect(wrapper.text()).toContain('提交 2026-11-10 08:00')
    document.body.innerHTML = ''
    respondWith(base())
    ;({ wrapper } = await mountPage(Units))
    expect(wrapper.text()).toContain('暂无申诉')
    expect(wrapper.text()).toContain('暂无同住人申请')
  })
})

describe('小程序 首页 / 我的 / 决议', () => {
  const indexTable = (me, over = {}) => ({
    'GET /me': me, 'GET /me/housing': housing({ pending_review_count: 2 }), 'GET /approval/tasks': { count: 0, results: [] },
    'GET /resolutions': { count: 0, results: [] }, 'GET /polls': { count: 0, results: [] }, ...over
  })

  it('TC-UNIT-555 / AC-151-05、AC-151-04、AC-368：产权业主首页显示“待我处理 · 2”并进入我的房屋待审批区；无待审时不显示', async () => {
    respondWith(indexTable(ME()))
    let { wrapper } = await mountPage(Index)
    const card = wrapper.findAll('.card').find((c) => c.text().includes('待我处理 · 2'))
    expect(card).toBeTruthy()
    await card.trigger('click')
    expect(uni.navigateTo.mock.calls.at(-1)[0].url).toBe('/pages/units/index?review=1')
    document.body.innerHTML = ''
    respondWith(indexTable(ME(), { 'GET /me/housing': housing({ pending_review_count: 0 }) }))
    ;({ wrapper } = await mountPage(Index))
    expect(wrapper.text()).not.toContain('待我处理')
  })

  it('TC-UNIT-556 / AC-166-01、AC-154-04、AC-166-03：非成员首页不请求待办、无待办卡与快捷宫格，但仍见“待我处理”；委员不请求待办时也不渲染 0 条卡', async () => {
    respondWith(indexTable(ME()))
    let { wrapper } = await mountPage(Index)
    expect(requests().some((r) => r.path === '/approval/tasks')).toBe(false)
    expect(wrapper.find('.home-todo').exists()).toBe(false)
    expect(wrapper.findAll('.home-q-label')).toHaveLength(0)
    expect(wrapper.text()).toContain('待我处理 · 2')
    document.body.innerHTML = ''
    respondWith(indexTable(ME('MEMBER')))
    ;({ wrapper } = await mountPage(Index))
    expect(wrapper.find('.home-todo').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('暂无审批待办')
    expect(wrapper.text()).toContain('管理快捷')
    expect(wrapper.text()).toContain('报销 / 备用金')
    expect(requests().some((r) => r.path === '/approval/tasks')).toBe(true)
  })

  it('TC-UNIT-557 / AC-157-01、AC-168-03：我的页列出每套房屋与身份（中文）；无已生成报表时显示"暂无已生成报表"', async () => {
    respondWith({
      'GET /me': ME(), 'GET /me/housing': housing({ units: [
        { ...UNIT, residents: [], pending_application_count: 0 },
        { unit_id: 2, specific_part: 'B房', role: 'RESIDENT', role_label: '同住人', residents: [], pending_application_count: 0 }] }),
      'GET /ledger/reports': { count: 0, results: [] }
    })
    const { wrapper } = await mountPage(Me)
    const text = wrapper.text()
    expect(text).toContain('1栋1单元3层301号（户主）')
    expect(text).toContain('B房（同住人）')
    expect(text).toContain('暂无已生成报表')
    expect(text).not.toMatch(/HEAD|RESIDENT/)
  })

  it('TC-UNIT-558 / AC-161-03：决议列表点"加载更多"追加下一批（请求 page=2），到底后显示"没有更多了，共 N 条"', async () => {
    const page = (n) => Array.from({ length: n === 1 ? 20 : 5 }, (_, i) => ({ id: n * 100 + i, title: `决议${n}-${i}`, status: 'APPROVED', approval_mode: 'DESIGNATED' }))
    respondWith({
      'GET /me': ME(),
      'GET /resolutions': (data) => ({ count: 25, results: page(data?.page || 1) })
    })
    const { wrapper } = await mountPage(Resolutions)
    expect(wrapper.findAll('.res-card')).toHaveLength(20)
    expect(byText(wrapper, 'button', '加载更多')).toBeTruthy()
    await byText(wrapper, 'button', '加载更多').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.res-card')).toHaveLength(25)
    expect(wrapper.text()).toContain('没有更多了，共 25 条')
    expect(byText(wrapper, 'button', '加载更多')).toBeUndefined()
    const calls = requests().filter((r) => r.path === '/resolutions')
    expect(calls.map((c) => c.data.page)).toEqual([1, 2])
    expect(new Set(wrapper.findAll('.res-title').map((e) => e.text())).size).toBe(25)
  })

  it('TC-UNIT-559 / AC-161-03（边界）：总数不超过 20 时无"加载更多"，直接显示"没有更多了，共 N 条"', async () => {
    respondWith({ 'GET /me': ME(), 'GET /resolutions': { count: 3, results: [1, 2, 3].map((i) => ({ id: i, title: `决议${i}`, status: 'APPROVED' })) } })
    const { wrapper } = await mountPage(Resolutions)
    expect(byText(wrapper, 'button', '加载更多')).toBeUndefined()
    expect(wrapper.text()).toContain('没有更多了，共 3 条')
  })
})
