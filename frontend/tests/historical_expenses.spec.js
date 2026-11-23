// PHASE_07 单元测试（Web 历史支出导入页）：AC-333-01、AC-335-01/02、AC-336-01、AC-338-02。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import HistoricalExpenses from '@/portal/HistoricalExpenses.vue'

const flush = async () => {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
}

const me = (position) => ({ identities: { committee: { position } } })
const BATCH = {
  id: 1, file_name: '2022-2026历史支出.xlsx', imported_by: 1, imported_by_label: '主任',
  status: 'IMPORTED', total_rows: 3, imported_rows: 2, skipped_rows: 1, failed_rows: 0,
  total_amount: '600.00', created_at: '2026-11-23T10:00:00+08:00', voided_at: null, void_reason: ''
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
  URL.createObjectURL = vi.fn(() => 'blob:mock')
  URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

describe('历史支出导入页', () => {
  it('AC-338-02 非业委会成员：显示无权限提示且不请求批次接口', async () => {
    mocked.http.get.mockImplementation(routeTable({ '/me': me('') }))
    await mountPage(HistoricalExpenses)
    await flush()
    expect(document.body.textContent).toContain('仅主任、副主任或委员可使用历史支出导入')
    const paths = mocked.http.get.mock.calls.map((call) => call[0])
    expect(paths).not.toContain('/admin/ledger/historical-expenses/batches')
  })

  it('AC-335-01 委员：加载批次列表并显示行数与金额合计', async () => {
    mocked.http.get.mockImplementation(routeTable({
      '/me': me('MEMBER'),
      '/admin/ledger/historical-expenses/batches': { count: 1, results: [BATCH] }
    }))
    await mountPage(HistoricalExpenses)
    await flush()
    expect(mocked.http.get).toHaveBeenCalledWith('/admin/ledger/historical-expenses/batches',
      { params: { page: 1, page_size: expect.any(Number) } })
    const text = document.body.textContent
    expect(text).toContain('2022-2026历史支出.xlsx')
    expect(text).toContain('600.00')
    expect(text).toContain('已导入')
  })

  it('AC-333-01 下载模板：请求 xlsx 并触发本地保存', async () => {
    mocked.http.get.mockImplementation(routeTable({
      '/me': me('CHAIR'),
      '/admin/ledger/historical-expenses/batches': { count: 0, results: [] },
      '/admin/ledger/historical-expenses/template': new Blob(['x'], { type: 'application/octet-stream' })
    }))
    const { wrapper } = await mountPage(HistoricalExpenses)
    await flush()
    const button = wrapper.findAll('button').find((b) => b.text().includes('下载 xlsx 模板'))
    await button.trigger('click')
    await flush()
    expect(mocked.http.get).toHaveBeenCalledWith('/admin/ledger/historical-expenses/template',
      { params: { file_type: 'xlsx' }, responseType: 'blob' })
    expect(URL.createObjectURL).toHaveBeenCalled()
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled()
  })

  it('AC-335-02 明细：点击“明细”读取批次逐行结果并展示错误原因', async () => {
    mocked.http.get.mockImplementation(routeTable({
      '/me': me('MEMBER'),
      '/admin/ledger/historical-expenses/batches': { count: 1, results: [BATCH] },
      '/admin/ledger/historical-expenses/batches/1': {
        ...BATCH,
        rows: [
          { line_no: 2, occurred_on: '2022-07-01', amount: '100.00', category: '维修', purpose: '更换钢丝绳', remark: '', status: 'IMPORTED', error_message: '' },
          { line_no: 3, occurred_on: '2022-07-01', amount: '100.00', category: '维修', purpose: '更换钢丝绳', remark: '', status: 'DUPLICATE', error_message: '与已有历史支出或文件内其他行重复' }
        ]
      }
    }))
    const { wrapper } = await mountPage(HistoricalExpenses)
    await flush()
    const detailButton = wrapper.findAll('button').find((b) => b.text() === '明细')
    await detailButton.trigger('click')
    await flush()
    expect(mocked.http.get).toHaveBeenCalledWith('/admin/ledger/historical-expenses/batches/1')
    const text = document.body.textContent
    expect(text).toContain('更换钢丝绳')
    expect(text).toContain('与已有历史支出或文件内其他行重复')
  })

  it('AC-336-01 整批作废：填写原因后调用作废接口并刷新列表', async () => {
    mocked.http.get.mockImplementation(routeTable({
      '/me': me('MEMBER'),
      '/admin/ledger/historical-expenses/batches': { count: 1, results: [BATCH] }
    }))
    mocked.http.post.mockResolvedValue({ ...BATCH, status: 'VOIDED', void_reason: '科目有误' })
    const { wrapper } = await mountPage(HistoricalExpenses)
    await flush()
    const voidButton = wrapper.findAll('button').find((b) => b.text() === '整批作废')
    await voidButton.trigger('click')
    await flush()

    const textarea = document.querySelector('.el-dialog textarea')
    expect(textarea).toBeTruthy()
    textarea.value = '科目有误'
    textarea.dispatchEvent(new Event('input'))
    await flush()
    const confirm = [...document.querySelectorAll('.el-dialog button')].find((b) => b.textContent.includes('确认作废'))
    confirm.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flush()
    expect(mocked.http.post).toHaveBeenCalledWith('/admin/ledger/historical-expenses/batches/1/void',
      { reason: '科目有误' })
    const batchCalls = mocked.http.get.mock.calls.filter((c) => c[0] === '/admin/ledger/historical-expenses/batches')
    expect(batchCalls.length).toBeGreaterThanOrEqual(2)
  })
})
