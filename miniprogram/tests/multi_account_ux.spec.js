// GROUP_D 小程序测试：报销/备用金账户选择
// 溯源：US-352、US-353；AC-423-01、AC-423-02、AC-424-01、AC-424-02
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, respondWith, requests } from './helpers.js'
import Claims from '../pages/claims/index.vue'

const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: false, units: [], labels: ['户主', '业委会委员'],
    committee: { position: 'MEMBER', term_end: '2027-01-01' },
    summary: { code: 'MEMBER', label: '委员' }
  }
}
const ACCOUNT_A = { id: 5, name: '基本账户', is_default: true, status: 'ENABLED', balance: '100.00' }
const ACCOUNT_B = { id: 6, name: '公共收益账户', is_default: false, status: 'ENABLED', balance: '50.00' }
const FLOW = { id: 7, name: '报销流程' }

const claimsList = (data) => ({ results: [] })

function routes(accounts) {
  return {
    'GET /me': ME,
    'GET /approval/flows': { results: [FLOW] },
    'GET /ledger/accounts/summary': { total_balance: '150.00', accounts },
    'GET /claims': claimsList,
    'GET /system/limits': { claim_amount_max: '5000.00' },
    'POST /claims/reimbursements': { id: 1 },
    'POST /claims/advances': { id: 2 }
  }
}

describe('小程序报销/备用金账户选择（US-352、US-353）', () => {
  it('TC-MP-2001 / AC-423-01、AC-424-01：仅请求启用账户并默认选中默认账户', async () => {
    respondWith(routes([ACCOUNT_A, ACCOUNT_B]))
    const { wrapper } = await mountPage(Claims)

    const summary = requests().find((r) => r.path === '/ledger/accounts/summary')
    expect(summary.data).toEqual({ status: 'ENABLED', recent: 0 })
    expect(wrapper.vm.accountIndex).toBe(0)
    expect(wrapper.vm.accountLabels).toEqual(['基本账户（默认）', '公共收益账户'])
    expect(wrapper.text()).toContain('入账账户：基本账户（默认）')

    wrapper.vm.pickType({ detail: { value: 1 } })
    expect(wrapper.vm.accountIndex).toBe(0)
  })

  it('TC-MP-2002 / AC-423-02、AC-424-02：切换账户后报销与备用金均提交所选 account_id', async () => {
    respondWith(routes([ACCOUNT_A, ACCOUNT_B]))
    const { wrapper } = await mountPage(Claims)

    wrapper.vm.pickAccount({ detail: { value: 1 } })
    wrapper.vm.pickFlow({ detail: { value: 0 } })
    wrapper.vm.amount = '300.50'
    wrapper.vm.reason = '打印费'
    wrapper.vm.occurredOn = '2025-06-02'
    await wrapper.vm.create()
    await flushPromises()
    expect(requests().find((r) => r.path === '/claims/reimbursements').data).toMatchObject({
      account_id: 6, amount: '300.50', approval_flow_id: 7
    })

    wrapper.vm.pickType({ detail: { value: 1 } })
    wrapper.vm.pickAccount({ detail: { value: 0 } })
    wrapper.vm.amount = '1000.00'
    wrapper.vm.reason = '活动'
    wrapper.vm.expectedUsage = '小区活动'
    wrapper.vm.expectedSettleOn = '2030-12-01'
    await wrapper.vm.create()
    await flushPromises()
    expect(requests().find((r) => r.path === '/claims/advances').data).toMatchObject({
      account_id: 5, amount: '1000.00', approval_flow_id: 7
    })
  })

  it('TC-MP-2002 / AC-423-02：无可用账户时提示且不发申请请求', async () => {
    respondWith(routes([]))
    const { wrapper } = await mountPage(Claims)
    expect(wrapper.vm.accountIndex).toBe(-1)

    wrapper.vm.pickFlow({ detail: { value: 0 } })
    wrapper.vm.amount = '10.00'
    wrapper.vm.reason = '测试'
    await wrapper.vm.create()

    expect(uni.showToast).toHaveBeenCalledWith({ title: '请选择入账账户', icon: 'none' })
    expect(requests().some((r) => r.method === 'POST' && r.path.startsWith('/claims'))).toBe(false)
  })
})
