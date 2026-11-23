// 财务报表 / 主页账户卡片 / 管理端账户管理界面测试（GROUP_D，PHASE_08/09 客户端侧）
// 溯源：US-322（AC-401-01/04/05）、US-323（AC-402-01/02）、US-329（AC-408-01）、US-330（AC-409-01/03）、US-325（AC-404-04）
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Reports from '@/portal/Reports.vue'
import Home from '@/portal/Home.vue'
import AdminAccounts from '@/admin/AdminAccounts.vue'

const { http, adminHttp } = mocked

const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: false, units: [], committee: { position: 'MEMBER', term_end: '2027-01-01' },
    labels: ['业委会委员'], summary: { code: 'COMMITTEE', label: '业委会委员' }
  }
}

const ACCOUNT = {
  id: 1, name: '第四届业主委员会基本账户', account_no: '', status: 'ENABLED', is_default: true,
  balance: '100.00',
  recent_entries: [{ id: 9, occurred_on: '2025-02-01', direction: 'INCOME', amount: '100.00', entry_type: 'INCOME' }]
}
const SUMMARY = { total_balance: '100.00', accounts: [ACCOUNT] }
const REPORTS = {
  count: 2,
  results: [
    { id: 1, period_type: 'QUARTER', year: 2025, quarter: 1, total_income: '100.00', total_expense: '0.00', balance: '100.00', legacy: false, stale: false },
    { id: 2, period_type: 'YEAR', year: 2025, quarter: null, total_income: '100.00', total_expense: '0.00', balance: '100.00', legacy: false, stale: false }
  ]
}
const DETAIL = {
  id: 1, period_type: 'QUARTER', year: 2025, quarter: 1, total_income: '100.00', total_expense: '0.00',
  balance: '100.00', opening_balance: '0.00', closing_balance: '100.00', legacy: false, stale: false,
  detail: [{ occurred_on: '2025-02-01', direction: 'INCOME', entry_type: '停车费', amount: '100.00' }]
}

const buttonByText = (root, text) => [...root.querySelectorAll('button')].find((b) => b.textContent.includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

function reportsRoutes(extra = {}) {
  return routeTable({
    '/me': ME,
    '/ledger/accounts/summary': SUMMARY,
    '/ledger/reports': REPORTS,
    '/ledger/reports/1': DETAIL,
    ...extra
  })
}

describe('财务报表页', () => {
  it('TC-WEB-1401 / AC-409-01、AC-409-03：展示账户余额合计、账户卡片与最近流水', async () => {
    http.get.mockImplementation(reportsRoutes())
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('财务报表')
    expect(text).toContain('第四届业主委员会基本账户')
    expect(text).toContain('¥100.00')
    expect(wrapper.text()).toContain('2025 年第 1 季度')
  })

  it('TC-WEB-1402 / AC-401-01、AC-401-04：切换“仅年报”后按 period_type 重新请求', async () => {
    http.get.mockImplementation(reportsRoutes())
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flushPromises()
    const yearBtn = wrapper.findAll('button').find((b) => b.text() === '仅年报')
    await yearBtn.trigger('click')
    await flushPromises()
    const calls = http.get.mock.calls.filter(([url]) => url === '/ledger/reports')
    expect(calls[calls.length - 1][1]).toEqual({ params: expect.objectContaining({ period_type: 'YEAR' }) })
  })

  it('TC-WEB-1403 / AC-402-01、AC-402-02：点击报表后浮层展示期初期末，关闭不离开列表', async () => {
    http.get.mockImplementation(reportsRoutes())
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flushPromises()
    const link = wrapper.findAll('button').find((b) => b.text().includes('2025 年第 1 季度'))
    await link.trigger('click')
    await flushPromises()
    expect(http.get).toHaveBeenCalledWith('/ledger/reports/1', { params: undefined })
    expect(document.body.textContent).toContain('期初结余')
    expect(document.body.textContent).toContain('期末结余')
    expect(document.body.textContent).toContain('2025 年第 1 季度报表')
    const closeBtn = buttonByText(document.body, '关闭')
    closeBtn.click()
    await flushPromises()
    expect(wrapper.text()).toContain('2025 年第 1 季度')
  })
})

describe('主页账户卡片', () => {
  it('TC-WEB-1404 / AC-408-01、AC-408-03：展示启用账户合计与各账户余额，点击进入财务报表', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions': { results: [] },
      '/approval/tasks': { count: 0, results: [] },
      '/polls': { results: [] },
      '/ledger/accounts/summary': SUMMARY
    }))
    const { wrapper, router } = await mountPage(Home, { path: '/' })
    await flushPromises()
    expect(wrapper.text()).toContain('账户余额')
    expect(wrapper.text()).toContain('¥100.00')
    expect(wrapper.text()).toContain('第四届业主委员会基本账户')
    const card = wrapper.find('.home-accounts')
    await card.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/reports')
  })
})

describe('管理端账户管理', () => {
  it('TC-WEB-1405 / AC-404-04：新建账户表单必填校验，不发起请求', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/ledger/accounts': {
        count: 1, page: 1, page_size: 20,
        results: [{ id: 1, name: '第四届业主委员会基本账户', account_no: '', status: 'ENABLED', is_default: true, balance: '0.00' }]
      }
    }))
    const { wrapper } = await mountPage(AdminAccounts, { path: '/admin/finance/accounts' })
    await flushPromises()
    expect(wrapper.text()).toContain('第四届业主委员会基本账户')
    await buttonByText(wrapper.element, '新建账户').click()
    await flushPromises()
    expect(document.body.textContent).toContain('账户名称')
    await buttonByText(document.body, '保存').click()
    await flushPromises()
    expect(document.body.textContent).toContain('请填写账户名称')
    expect(adminHttp.post).not.toHaveBeenCalled()
  })
})
