// ocap_product_review MOD-085 自验证：新增 api 路径/方法、加载更多、确认取消不发请求、同住人链路、报表明细、入口可见性
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, respondWith, requests, byText } from './helpers.js'
import { api } from '../utils/api.js'
import { confirmDanger } from '../utils/confirm.js'
import { usePaging } from '../utils/paging.js'
import { statusLabel } from '../utils/labels.js'
import Units from '../pages/units/index.vue'
import ReportDetail from '../pages/reports/detail.vue'
import Me from '../pages/me/index.vue'
import Claims from '../pages/claims/index.vue'

const ME = (position = null) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: false, units: [{ unit_id: 1, specific_part: 'A', role: 'OWNER' }], labels: ['产权业主'],
    summary: { code: 'OWNER', label: '产权业主' }, committee: position ? { position, term_end: '2027-01-01' } : null
  }
})

describe('新增 API 函数（IFC-283）', () => {
  it('TC-UNIT-568 / AC-178-02、AC-150-04、AC-153-05、AC-168-01：路径、方法、请求体', async () => {
    respondWith({
      'GET /me/housing': {}, 'GET /system/limits': {}, 'GET /appeals/mine': [], 'POST /resident-applications': {},
      'GET /resident-applications/mine': [], 'GET /resident-applications/to-review': [],
      'POST /resident-applications/4/decision': {}, 'DELETE /units/2/residents/9': {}, 'POST /units/2/leave': {},
      'GET /ledger/reports/5': {}, 'GET /ledger/reports': {}
    })
    await api.housing()
    await api.limits()
    await api.myAppeals()
    await api.createResidentApplication({ unit_id: 3 })
    await api.decideResidentApplication(4, 'APPROVE')
    await api.removeResident(2, 9)
    await api.leaveUnit(2)
    await api.report(5)
    await api.reports({ page: 2, page_size: 20 })
    const calls = requests().map((r) => `${r.method} ${r.path}`)
    expect(calls).toEqual([
      'GET /me/housing', 'GET /system/limits', 'GET /appeals/mine', 'POST /resident-applications',
      'POST /resident-applications/4/decision', 'DELETE /units/2/residents/9', 'POST /units/2/leave',
      'GET /ledger/reports/5', 'GET /ledger/reports'
    ])
    expect(requests()[3].data).toEqual({ unit_id: 3 })
    expect(requests()[4].data).toEqual({ decision: 'APPROVE' })
    expect(requests()[8].data).toEqual({ page: 2, page_size: 20 })
  })
})

describe('utils', () => {
  it('TC-UNIT-569 / AC-167-01：statusLabel 中文映射', () => {
    expect(statusLabel('application', 'CLOSED')).toBe('已关闭（申请人已注销）')
    expect(statusLabel('appeal', 'APPROVED')).toBe('已通过')
  })

  it('TC-UNIT-570 / AC-153-05：confirmDanger：确认 true、取消 false', async () => {
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: true }))
    expect(await confirmDanger('leaveUnit', { name: 'A' })).toBe(true)
    expect(uni.showModal.mock.calls[0][0].content).toContain('对象：A')
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: false, cancel: true }))
    expect(await confirmDanger('removeResident')).toBe(false)
  })

  it('TC-UNIT-571 / AC-161-03：usePaging：加载更多追加不重复，到底后 hasMore 为 false', async () => {
    const pages = { 1: { count: 3, results: [{ id: 1 }, { id: 2 }] }, 2: { count: 3, results: [{ id: 3 }] } }
    const paging = usePaging({ fetch: async ({ page }) => pages[page], pageSize: 2 })
    await paging.reset()
    expect(paging.hasMore.value).toBe(true)
    await paging.loadMore()
    expect(paging.items.value.map((x) => x.id)).toEqual([1, 2, 3])
    expect(paging.hasMore.value).toBe(false)
    expect(paging.total.value).toBe(3)
  })
})

describe('页面', () => {
  it('TC-UNIT-572 / AC-153-05、AC-156-05、AC-157-01：我的房屋：汇总身份、同住人名单；取消移除不发请求；确认后 DELETE', async () => {
    respondWith({
      'GET /me': ME(),
      'GET /me/housing': {
        summary: { code: 'OWNER', label: '产权业主' }, pending_review_count: 1,
        units: [{ unit_id: 1, specific_part: '1栋1单元301', role: 'OWNER', role_label: '产权业主', residents: [
          { user_id: 9, nickname: '李四', account_no: 'A0009', joined_at: '2026-11-01T00:00:00+08:00' }], pending_application_count: 1 }]
      },
      'GET /resident-applications/to-review': { results: [{ id: 4, applicant: { nickname: '王五' }, unit: { specific_part: '1栋1单元301' }, created_at: '2026-11-13T10:00:00+08:00' }] },
      'GET /resident-applications/mine': [],
      'GET /appeals/mine': [{ id: 1, unit: { specific_part: 'B' }, status: 'REJECTED', submitted_at: '2026-11-01T10:00:00+08:00', decided_at: '2026-11-02T10:00:00+08:00', reject_reason: '证明不清晰' }],
      'GET /units/options': { options: [] },
      'DELETE /units/1/residents/9': {}
    })
    const { wrapper } = await mountPage(Units)
    const text = wrapper.text()
    expect(text).toContain('汇总身份：产权业主')
    expect(text).toContain('李四')
    expect(text).toContain('王五')
    expect(text).toContain('暂无同住人申请')
    expect(text).toContain('驳回原因：证明不清晰')
    expect(text).toContain('已驳回')
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: false }))
    await byText(wrapper, 'button', '移除').trigger('click')
    await flushPromises()
    expect(requests().some((r) => r.method === 'DELETE')).toBe(false)
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: true }))
    await byText(wrapper, 'button', '移除').trigger('click')
    await flushPromises()
    expect(requests().some((r) => r.method === 'DELETE' && r.path === '/units/1/residents/9')).toBe(true)
  })

  it('TC-UNIT-573 / AC-150-04：我的房屋：未选房屋申请同住人给出提示且不发请求', async () => {
    respondWith({
      'GET /me': ME(), 'GET /me/housing': { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 },
      'GET /resident-applications/to-review': [], 'GET /resident-applications/mine': [], 'GET /appeals/mine': [],
      'GET /units/options': { options: [] }
    })
    const { wrapper } = await mountPage(Units)
    expect(wrapper.text()).toContain('暂无已认证房屋')
    await byText(wrapper, 'button', '申请成为同住人').trigger('click')
    expect(requests().some((r) => r.path === '/resident-applications' && r.method === 'POST')).toBe(false)
  })

  it('TC-UNIT-574 / AC-168-01：报表明细：合计与明细行，显示收入来源与支出事由', async () => {
    respondWith({
      'GET /ledger/reports/5': {
        id: 5, period_type: 'QUARTER', year: 2026, quarter: 3, total_income: '100.00', total_expense: '30.00', balance: '70.00',
        detail: [{ direction: 'EXPENSE', occurred_on: '2026-08-01', entry_type: 'REIMBURSEMENT', amount: '30.00', summary: '电梯维修' },
          { direction: 'INCOME', occurred_on: '2026-08-02', entry_type: '停车费', amount: '100.00', summary: '小区公共收益' }]
      }
    })
    const { wrapper } = await mountPage(ReportDetail, { query: { id: '5' } })
    expect(wrapper.text()).toContain('2026 年第 3 季度')
    expect(wrapper.text()).toContain('收入合计：¥100.00')
    expect(wrapper.text()).toContain('报销')
    expect(wrapper.text()).toContain('¥30.00')
    expect(wrapper.text()).toContain('电梯维修')
    expect(wrapper.text()).toContain('小区公共收益')
  })

  it('TC-UNIT-575 / AC-154-04、AC-168-01：我的：报表可点击进入明细；非成员无“报销 / 备用金”按钮；成员有', async () => {
    const routes = {
      'GET /me/housing': { units: [] },
      'GET /ledger/reports': { count: 1, results: [{ id: 5, period_type: 'YEAR', year: 2026, total_income: '1.00', total_expense: '0.00' }] }
    }
    respondWith({ ...routes, 'GET /me': ME() })
    let { wrapper } = await mountPage(Me)
    expect(byText(wrapper, 'button', '报销 / 备用金')).toBeUndefined()
    await byText(wrapper, '.list-item', '2026 年度').trigger('click')
    expect(uni.navigateTo.mock.calls[0][0].url).toBe('/pages/reports/detail?id=5')
    document.body.innerHTML = ''
    respondWith({ ...routes, 'GET /me': ME('CHAIR') })
    ;({ wrapper } = await mountPage(Me))
    expect(byText(wrapper, 'button', '报销 / 备用金')).toBeTruthy()
  })

  it('TC-UNIT-576 / AC-154-01、AC-154-04：报销页：非成员显示“需要业委会成员身份”且无新建表单', async () => {
    respondWith({
      'GET /me': ME(), 'GET /claims': { count: 0, results: [] }, 'GET /approval/flows': { results: [] },
      'GET /system/limits': { claim_amount_max: '1000000.00' }
    })
    const { wrapper } = await mountPage(Claims)
    expect(wrapper.text()).toContain('需要业委会成员身份')
    expect(wrapper.text()).not.toContain('新建申请')
  })
})
