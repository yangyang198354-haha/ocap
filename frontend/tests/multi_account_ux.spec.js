// GROUP_D 前端测试：多账户落账表单与财务报表多账户 UI
// 溯源：US-339~US-351；AC-410-01~AC-422-02
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import AdminAccounts from '@/admin/AdminAccounts.vue'
import Income from '@/portal/Income.vue'
import Claims from '@/portal/Claims.vue'
import HistoricalExpenses from '@/portal/HistoricalExpenses.vue'
import Reports from '@/portal/Reports.vue'

const { http, adminHttp } = mocked

const flush = async () => {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
}

const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: false, units: [],
    committee: { position: 'MEMBER', term_end: '2027-01-01' },
    labels: ['业委会委员'], summary: { code: 'COMMITTEE', label: '业委会委员' }
  }
}

const ACCOUNT_A = { id: 1, name: '基本账户', account_no: '', status: 'ENABLED', is_default: true, balance: '100.00', recent_entries: [] }
const ACCOUNT_B = { id: 2, name: '公共收益账户', account_no: '', status: 'ENABLED', is_default: false, balance: '50.00', recent_entries: [] }
const ACCOUNT_C = { id: 3, name: '维修基金账户', account_no: '', status: 'ENABLED', is_default: false, balance: '20.00', recent_entries: [] }
const SUMMARY = { total_balance: '170.00', accounts: [ACCOUNT_A, ACCOUNT_B, ACCOUNT_C] }
const SUMMARY_EMPTY = { total_balance: '0.00', accounts: [] }

const REPORTS = {
  count: 2,
  results: [
    { id: 1, period_type: 'QUARTER', year: 2025, quarter: 1, total_income: '100.00', total_expense: '20.00', balance: '80.00', legacy: false, stale: false },
    { id: 2, period_type: 'YEAR', year: 2025, quarter: null, total_income: '100.00', total_expense: '20.00', balance: '80.00', legacy: false, stale: false }
  ]
}
const DETAIL = {
  id: 1, period_type: 'QUARTER', year: 2025, quarter: 1,
  total_income: '100.00', total_expense: '20.00', balance: '80.00',
  opening_balance: '0.00', closing_balance: '80.00', legacy: false, stale: false,
  detail: [
    { occurred_on: '2025-02-01', direction: 'INCOME', entry_type: '停车费', amount: '100.00' },
    { occurred_on: '2025-03-01', direction: 'EXPENSE', entry_type: '维修', amount: '20.00' }
  ]
}

const buttonByText = (root, text) => [...root.querySelectorAll('button')].find((b) => b.textContent.includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

describe('账户管理操作按钮（US-339）', () => {  it('TC-WEB-2001 / AC-410-01、AC-410-02：操作按钮使用高对比度 el-button，默认账户的“设为默认”禁用', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/ledger/accounts': {
        count: 2, page: 1, page_size: 20,
        results: [
          { id: 1, name: '基本账户', account_no: '', status: 'ENABLED', is_default: true, balance: '0.00' },
          { id: 2, name: '公共收益账户', account_no: '', status: 'ENABLED', is_default: false, balance: '0.00' }
        ]
      }
    }))
    const { wrapper } = await mountPage(AdminAccounts, { path: '/admin/finance/accounts' })
    await flush()

    const rows = wrapper.findAll('.el-table__row')
    expect(rows).toHaveLength(2)
    const defaultButtons = rows[0].findAll('button')
    expect(defaultButtons.some((b) => b.text() === '编辑')).toBe(true)
    for (const button of defaultButtons) {
      expect(button.classes()).toContain('el-button')
      expect(button.classes()).not.toContain('el-link')
    }
    const setDefault = defaultButtons.find((b) => b.text() === '设为默认')
    expect(setDefault).toBeTruthy()
    expect(setDefault.attributes('disabled')).toBeDefined()

    const otherDefault = rows[1].findAll('button').find((b) => b.text() === '设为默认')
    expect(otherDefault.attributes('disabled')).toBeUndefined()
  })
})

describe('收入逐条录入与批量导入（US-340、US-341）', () => {
  const routes = (summary) => routeTable({
    '/admin/income/sheets': { count: 0, results: [] },
    '/system/limits': {},
    '/approval/flows': { results: [{ id: 7, name: '收入审批', mode: 'DESIGNATED' }] },
    '/ledger/accounts/summary': summary
  })

  it('TC-WEB-2002 / AC-411-01、AC-411-02：逐条录入默认选中默认账户并提交 account_id', async () => {
    http.get.mockImplementation(routes(SUMMARY))
    const { wrapper } = await mountPage(Income, { path: '/income' })
    await flush()

    await buttonByText(wrapper.element, '逐条录入').click()
    await flush()

    expect(http.get).toHaveBeenCalledWith('/ledger/accounts/summary', {
      params: { status: 'ENABLED', recent: 0 }
    })
    expect(wrapper.vm.createAccountId).toBe(1)
    Object.assign(wrapper.vm.form.records[0], {
      occurred_on: '2025-06-01', amount: '88.00', category: '停车费', source_note: '临停'
    })
    await wrapper.vm.create()
    await flush()

    const post = http.post.mock.calls.find(([url]) => url === '/admin/income/sheets')
    expect(post[1]).toMatchObject({
      account_id: 1,
      records: [expect.objectContaining({ amount: '88.00', category: '停车费' })]
    })
  })

  it('TC-WEB-2003 / AC-411-03：无可用账户时提示并禁用保存', async () => {
    http.get.mockImplementation(routes(SUMMARY_EMPTY))
    const { wrapper } = await mountPage(Income, { path: '/income' })
    await flush()

    await buttonByText(wrapper.element, '逐条录入').click()
    await flush()

    expect(document.body.textContent).toContain('暂无可用账户')
    const save = buttonByText(document.body, '保存为草稿')
    expect(save.disabled).toBe(true)
    await wrapper.vm.create()
    expect(http.post.mock.calls.some(([url]) => url === '/admin/income/sheets')).toBe(false)
  })

  it('TC-WEB-2004 / AC-412-01、AC-412-02：未选账户不导入；已选账户随文件提交 account_id', async () => {
    http.get.mockImplementation(routes(SUMMARY_EMPTY))
    const { wrapper } = await mountPage(Income, { path: '/income' })
    await flush()
    await wrapper.vm.importFile({ file: new File(['a,b'], 'a.csv') })
    expect(document.body.textContent).toContain('请先选择入账账户')
    expect(http.post).not.toHaveBeenCalled()

    http.get.mockImplementation(routes(SUMMARY))
    const second = await mountPage(Income, { path: '/income' })
    await flush()
    expect(second.wrapper.vm.importAccountId).toBe(1)
    await second.wrapper.vm.importFile({ file: new File(['a,b'], 'a.csv') })
    await flush()
    const upload = http.post.mock.calls.find(([url]) => url === '/admin/income/sheets/import')
    expect(upload).toBeTruthy()
    expect(upload[1].get('account_id')).toBe('1')
    expect(upload[1].get('file')).toBeTruthy()
  })
})

describe('报销与备用金表单（US-342、US-343）', () => {
  const routes = (summary) => routeTable({
    '/me': ME,
    '/claims': { count: 0, results: [] },
    '/system/limits': {},
    '/approval/flows': { results: [{ id: 7, name: '报销审批', mode: 'DESIGNATED' }] },
    '/ledger/accounts/summary': summary
  })

  it('TC-WEB-2005 / AC-413-01、AC-413-02、AC-414-01：报销/备用金默认账户并提交 account_id', async () => {
    http.get.mockImplementation(routes(SUMMARY))
    const { wrapper } = await mountPage(Claims, { path: '/claims' })
    await flush()

    await buttonByText(wrapper.element, '新建申请').click()
    await flush()
    expect(wrapper.vm.form.account_id).toBe(1)

    Object.assign(wrapper.vm.form, {
      amount: '300.50', reason: '打印费', occurred_on: '2025-06-02', approval_flow_id: 7
    })
    await wrapper.vm.create()
    await flush()
    const reimbursement = http.post.mock.calls.find(([url]) => url === '/claims/reimbursements')
    expect(reimbursement[1]).toMatchObject({ account_id: 1, amount: '300.50' })

    await buttonByText(wrapper.element, '新建申请').click()
    await flush()
    wrapper.vm.form.type = 'ADVANCE'
    wrapper.vm.form.account_id = 2
    Object.assign(wrapper.vm.form, {
      amount: '1000.00', reason: '活动', expected_usage: '小区活动',
      expected_settle_on: '2030-12-01', approval_flow_id: 7
    })
    await wrapper.vm.create()
    await flush()
    const advance = http.post.mock.calls.find(([url]) => url === '/claims/advances')
    expect(advance[1]).toMatchObject({ account_id: 2, amount: '1000.00' })
  })

  it('TC-WEB-2006 / AC-414-02：未选账户不发请求并提示', async () => {
    http.get.mockImplementation(routes(SUMMARY_EMPTY))
    const { wrapper } = await mountPage(Claims, { path: '/claims' })
    await flush()
    await buttonByText(wrapper.element, '新建申请').click()
    await flush()
    expect(wrapper.vm.form.account_id).toBeNull()
    await wrapper.vm.create()
    expect(document.body.textContent).toContain('请选择入账账户')
    expect(http.post).not.toHaveBeenCalled()
  })
})

describe('历史支出导入（US-344、US-345）', () => {
  const BATCHES = {
    count: 3,
    results: [
      { id: 1, file_name: 'pending.csv', account_name: '基本账户', imported_by_label: '主任', total_rows: 1, imported_rows: 1, skipped_rows: 0, failed_rows: 0, total_amount: '10.00', status: 'PENDING', posted_rows: 0, created_at: '2025-06-01T10:00:00+08:00' },
      { id: 2, file_name: 'imported.csv', account_name: '公共收益账户', imported_by_label: '主任', total_rows: 1, imported_rows: 1, skipped_rows: 0, failed_rows: 0, total_amount: '20.00', status: 'IMPORTED', posted_rows: 1, created_at: '2025-06-02T10:00:00+08:00' },
      { id: 3, file_name: 'rejected.csv', account_name: '基本账户', imported_by_label: '主任', total_rows: 1, imported_rows: 1, skipped_rows: 0, failed_rows: 0, total_amount: '30.00', status: 'REJECTED', posted_rows: 0, created_at: '2025-06-03T10:00:00+08:00' }
    ]
  }
  const routes = (summary) => routeTable({
    '/me': ME,
    '/admin/ledger/historical-expenses/batches': BATCHES,
    '/approval/flows': { results: [{ id: 9, name: '历史支出审批', mode: 'DESIGNATED' }] },
    '/ledger/accounts/summary': summary
  })

  it('TC-WEB-2007 / AC-415-01、AC-415-03：默认账户、未选账户不导入、已选账户带 account_id 与流程', async () => {
    http.get.mockImplementation(routes(SUMMARY_EMPTY))
    const empty = await mountPage(HistoricalExpenses, { path: '/historical-expenses' })
    await flush()
    expect(empty.wrapper.vm.accountId).toBeNull()
    await empty.wrapper.vm.uploadFile({ file: new File(['x'], 'h.csv') })
    expect(document.body.textContent).toContain('请选择入账账户')
    expect(http.post).not.toHaveBeenCalled()

    http.get.mockImplementation(routes(SUMMARY))
    const { wrapper } = await mountPage(HistoricalExpenses, { path: '/historical-expenses' })
    await flush()
    expect(wrapper.vm.accountId).toBe(1)
    wrapper.vm.flowId = 9
    await wrapper.vm.uploadFile({ file: new File(['x'], 'h.csv') })
    await flush()
    const upload = http.post.mock.calls.find(([url]) => url === '/admin/ledger/historical-expenses/import')
    expect(upload).toBeTruthy()
    expect(upload[1].get('account_id')).toBe('1')
    expect(upload[1].get('approval_flow_id')).toBe('9')
  })

  it('TC-WEB-2008 / AC-416-04、AC-422-01：状态文案与按状态显示撤回/整批作废', async () => {
    http.get.mockImplementation(routes(SUMMARY))
    const { wrapper } = await mountPage(HistoricalExpenses, { path: '/historical-expenses' })
    await flush()

    const text = wrapper.text()
    expect(text).toContain('审批中')
    expect(text).toContain('已入账')
    expect(text).toContain('已驳回')
    expect(wrapper.findAll('button').filter((b) => b.text() === '撤回')).toHaveLength(1)
    expect(wrapper.findAll('button').filter((b) => b.text() === '整批作废')).toHaveLength(1)
  })
})

describe('财务报表多账户 UI（US-346~US-350）', () => {
  const reportsRoutes = (summary, detail = DETAIL) => routeTable({
    '/me': ME,
    '/ledger/accounts/summary': summary,
    '/ledger/reports': REPORTS,
    '/ledger/reports/1': detail
  })

  it('TC-WEB-2009 / AC-417-01、AC-417-03、AC-418-01、AC-418-02、AC-418-03、AC-419-02：卡片等宽排列、默认选中与切换账户取数', async () => {
    http.get.mockImplementation(reportsRoutes(SUMMARY))
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flush()

    const cards = wrapper.findAll('.account-card')
    expect(cards).toHaveLength(3)
    expect(cards[0].attributes('aria-pressed')).toBe('true')
    expect(cards[0].classes()).toContain('is-selected')
    expect(cards[1].attributes('aria-pressed')).toBe('false')

    const grid = wrapper.find('.reports-account-grid')
    expect(grid.exists()).toBe(true)
    expect(wrapper.find('.reports-accounts-head').element.closest('.reports-account-grid')).toBeNull()

    expect(http.get).toHaveBeenCalledWith('/ledger/accounts/summary', {
      params: { status: 'ENABLED', recent: 10 }
    })

    await cards[1].trigger('click')
    await flush()
    let calls = http.get.mock.calls.filter(([url]) => url === '/ledger/reports')
    expect(calls[calls.length - 1][1]).toEqual({ params: expect.objectContaining({ account_id: 2 }) })
    expect(wrapper.findAll('.account-card')[1].attributes('aria-pressed')).toBe('true')

    await buttonByText(wrapper.element, '仅季报').click()
    await flush()
    await wrapper.findAll('.account-card')[2].trigger('click')
    await flush()
    calls = http.get.mock.calls.filter(([url]) => url === '/ledger/reports')
    expect(calls[calls.length - 1][1]).toEqual({
      params: expect.objectContaining({ period_type: 'QUARTER', account_id: 3 })
    })
  })

  it('TC-WEB-2009 / AC-417-02：8 个账户全部渲染，停用账户不出现', async () => {
    const many = [...Array(8)].map((_, index) => ({
      id: index + 1, name: `账户${index + 1}`, account_no: '', status: 'ENABLED',
      is_default: index === 0, balance: '1.00', recent_entries: []
    }))
    http.get.mockImplementation(reportsRoutes({ total_balance: '8.00', accounts: many }))
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flush()

    expect(wrapper.findAll('.account-card')).toHaveLength(8)
    expect(wrapper.text()).not.toContain('停用账户')
    expect(http.get).toHaveBeenCalledWith('/ledger/accounts/summary', {
      params: { status: 'ENABLED', recent: 10 }
    })
  })

  it('TC-WEB-2010 / AC-420-01、AC-420-02、AC-421-01、AC-421-03：详情无账户下拉、按选中账户请求并区分收支颜色', async () => {
    http.get.mockImplementation(reportsRoutes(SUMMARY))
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flush()

    await wrapper.findAll('.account-card')[1].trigger('click')
    await flush()
    await wrapper.find('.reports-item-link').trigger('click')
    await flush()

    expect(http.get).toHaveBeenCalledWith('/ledger/reports/1', { params: { account_id: 2 } })
    const dialog = document.querySelector('.el-dialog')
    expect(dialog).toBeTruthy()
    expect(dialog.querySelectorAll('.el-select')).toHaveLength(0)
    expect(dialog.textContent).not.toContain('全部账户')
    expect(dialog.querySelector('.report-metric b.is-income')).toBeTruthy()
    expect(dialog.querySelector('.report-metric b.is-expense')).toBeTruthy()
    const scroll = dialog.querySelector('.report-detail-scroll')
    expect(scroll.querySelector('.is-income')).toBeTruthy()
    expect(scroll.querySelector('.is-expense')).toBeTruthy()
    expect(scroll.textContent).toContain('收入')
    expect(scroll.textContent).toContain('支出')
  })

  it('TC-WEB-2010 / AC-421-02：仅支出明细全部显示支出；空明细提示', async () => {
    const onlyExpense = { ...DETAIL, total_income: '0.00', detail: [DETAIL.detail[1]] }
    http.get.mockImplementation(reportsRoutes(SUMMARY, onlyExpense))
    const { wrapper } = await mountPage(Reports, { path: '/reports' })
    await flush()
    await wrapper.find('.reports-item-link').trigger('click')
    await flush()
    let dialog = document.querySelector('.el-dialog')
    let scroll = dialog.querySelector('.report-detail-scroll')
    expect(scroll.textContent).toContain('支出')
    expect(scroll.querySelector('.is-income')).toBeNull()

    wrapper.unmount()
    document.body.innerHTML = ''
    http.get.mockImplementation(reportsRoutes(SUMMARY, { ...DETAIL, detail: [] }))
    const second = await mountPage(Reports, { path: '/reports' })
    await flush()
    await second.wrapper.find('.reports-item-link').trigger('click')
    await flush()
    dialog = document.querySelector('.el-dialog')
    expect(dialog.textContent).toContain('本期暂无收支明细')
  })
})
