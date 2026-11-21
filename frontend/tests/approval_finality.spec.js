// 审批失败终局与重新发起留痕（REQ-FUNC-269~275）：失败单不再提供原单重提，改为新建并展示双向关联
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('@/shared/confirm', () => ({ confirmDanger: vi.fn().mockResolvedValue(true) }))
vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useRoute: () => ({ params: { id: globalThis.__routeId || '1' }, query: globalThis.__query || {} })
  }
})

import { mountPage, routeTable } from './helpers.js'
import ResolutionDetail from '@/portal/ResolutionDetail.vue'
import Resolutions from '@/portal/Resolutions.vue'
import Income from '@/portal/Income.vue'
import Claims from '@/portal/Claims.vue'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const ME = {
  profile: { id: 1, nickname: '张三' },
  identities: { is_guest: false, units: [], labels: ['业委会委员'], committee: { position: 'MEMBER' },
    summary: { code: 'MEMBER', label: '委员' } }
}
const buttonOf = (root, text) => Array.from(root.querySelectorAll('button')).find((b) => b.textContent.includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
  globalThis.__routeId = '7'
  globalThis.__query = {}
})

describe('US-277/278 决议失败后原单终局', () => {
  const detail = (status, extra = {}) => ({
    id: 7, title: '加装电梯', content: '正文', status, approval_mode: 'DESIGNATED',
    initiator: { id: 1, display_name: '张三' }, attachments: [], vote_counts: null, ...extra
  })

  it('AC-277-02：未通过决议不显示“修改后重新提交”，提示结束并给出“新建决议”与留痕', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions/7': detail('REJECTED', { origin_id: 3, reopened_by_id: 9 })
    }))
    const { wrapper, router } = await mountPage(ResolutionDetail)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('该决议已结束（审批人拒绝）')
    expect(text).toContain('重新发起自 R-0003')
    expect(text).toContain('已由 R-0009 重新发起')
    expect(wrapper.findAll('button').some((b) => b.text().includes('修改后重新提交'))).toBe(false)
    await wrapper.findAll('button').find((b) => b.text().includes('新建决议')).trigger('click')
    await flush()
    expect(router.currentRoute.value.path).toBe('/resolutions/mine')
    expect(router.currentRoute.value.query.origin).toBe('7')
  })

  it('AC-278-02：指定负责人拒绝与投票失败同样终局；半数同意显示“表决未过半”', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions/7': detail('REJECTED', { approval_mode: 'HALF_MAJORITY' })
    }))
    const { wrapper } = await mountPage(ResolutionDetail)
    await flush()
    expect(wrapper.text()).toContain('该决议已结束（表决未过半）')
  })

  it('AC-279-03：撤回仍保留原单“修改后重新提交”', async () => {
    http.get.mockImplementation(routeTable({ '/me': ME, '/resolutions/7': detail('WITHDRAWN') }))
    const { wrapper } = await mountPage(ResolutionDetail)
    await flush()
    expect(wrapper.text()).toContain('修改后重新提交')
    expect(wrapper.findAll('button').some((b) => b.text().includes('新建决议'))).toBe(false)
  })

  it('AC-277-05：从失败决议新建时带 origin 参数预填并发起新决议', async () => {
    globalThis.__query = { origin: '5' }
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions': { count: 1, results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' },
      '/approval/flows': { results: [{ id: 2, name: '指定审批', mode: 'DESIGNATED' }] },
      '/resolutions/5': { id: 5, title: '旧决议', content: '旧正文', status: 'REJECTED',
        approval_mode: 'DESIGNATED', initiator: { id: 1 }, attachments: [] }
    }))
    http.post.mockResolvedValue({ id: 8 })
    await mountPage(Resolutions, { props: { section: 'mine' } })
    await flush()
    expect(document.body.textContent).toContain('重新发起自 R-0005')
    buttonOf(document.body, '提交').click()
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resolutions', expect.objectContaining({ origin_id: 5 }))
  })
})

describe('US-280 收入表失败后只读留痕', () => {
  const sheet = (id, status, extra = {}) => ({ id, title: `表${id}`, status, total_amount: '10.00',
    period_start: '2026-01-01', period_end: '2026-01-31', can_void: false, ...extra })

  it('AC-280-02：未通过只显示“重新发起”，撤回才显示“重新提交”', async () => {
    http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 3, results: [
        sheet(1, 'DRAFT'), sheet(2, 'REJECTED', { reopened_by_id: 9 }), sheet(3, 'WITHDRAWN')] },
      '/approval/flows': { results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Income)
    await flush()
    const labels = wrapper.findAll('button').map((b) => b.text().trim())
    expect(labels.filter((t) => t === '提交')).toHaveLength(1)
    expect(labels.filter((t) => t === '重新提交')).toHaveLength(1)
    expect(labels.filter((t) => t === '重新发起')).toHaveLength(1)
    expect(wrapper.text()).toContain('该收入表已结束（审批未通过）')
    expect(wrapper.text()).toContain('已由 #9 重新发起')
  })

  it('AC-280-04：重新发起复制原表明细并带 origin_id 创建新表', async () => {
    http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 1, results: [sheet(2, 'REJECTED')] },
      '/approval/flows': { results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' },
      '/admin/income/sheets/2': { ...sheet(2, 'REJECTED'), attachments: [],
        records: [{ line_no: 1, occurred_on: '2026-06-01', amount: '300.50', category: '物业费',
          source_note: '6月物业费', remark: '' }] }
    }))
    http.post.mockResolvedValue({ id: 6 })
    const { wrapper } = await mountPage(Income)
    await flush()
    await wrapper.findAll('button').find((b) => b.text().trim() === '重新发起').trigger('click')
    await flush()
    expect(document.body.textContent).toContain('重新发起自 #2')
    buttonOf(document.body, '保存为草稿').click()
    await flush()
    expect(http.post).toHaveBeenCalledWith('/admin/income/sheets',
      expect.objectContaining({ origin_id: 2 }))
  })
})

describe('US-279 报销/备用金失败后只能新建', () => {
  it('AC-279-02：未通过申请显示结束提示、重新发起与关联留痕', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/claims': { count: 2, results: [
        { id: 4, type: 'REIMBURSEMENT', amount: '300.50', reason: '打印费', status: 'REJECTED',
          origin_id: 2, reopened_by_id: 8, settlement_id: null },
        { id: 5, type: 'ADVANCE', amount: '500.00', reason: '出差', status: 'WITHDRAWN',
          settlement_id: null }] },
      '/approval/flows': { results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Claims)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('该申请已结束（审批未通过）')
    expect(text).toContain('重新发起自 #2')
    expect(text).toContain('已由 #8 重新发起')
    expect(wrapper.findAll('button').some((b) => b.text().trim() === '重新发起')).toBe(true)
    // 撤回仍允许原单重提（沿用既有入口，不在失败单上出现）
    expect(wrapper.findAll('button').filter((b) => b.text().trim() === '重新提交')).toHaveLength(0)
  })
})
