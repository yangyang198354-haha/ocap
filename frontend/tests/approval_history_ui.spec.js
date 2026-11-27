// ocap_approval_history GROUP_D：真实页面 + api.js + Pinia，只有 HTTP 层为替身。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage } from './helpers.js'
import Tasks from '@/portal/Tasks.vue'
import PagerBar from '@/shared/PagerBar.vue'
import UnitsReview from '@/portal/units/UnitsReview.vue'
import UnitsApplicationRecords from '@/portal/units/UnitsApplicationRecords.vue'

const { http } = mocked
const flush = async () => {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
}
const tab = (wrapper, text) => wrapper.findAll('.el-tabs__item').find((node) => node.text() === text)
const button = (wrapper, text) => wrapper.findAll('button').find((node) => node.text().trim() === text)
const taskRow = (id, overrides = {}) => ({
  instance_id: id, scope: 'RESOLUTION', subject_type: 'resolution', subject_id: id,
  subject_title: `决议${id}`, submitter: { id: 9, display_name: '提交人', avatar_url: null },
  submitter_label: '提交人', submitted_at: '2026-11-27T08:00:00+08:00', status: 'PENDING',
  step_order: 2, step_name: '主任终审', step_strategy: 'ANY', my_action: 'APPROVE',
  my_acted_at: '2026-11-27T09:00:00+08:00', my_comment: '同意', my_step_order: 1,
  my_step_name: '财务初审', ...overrides
})

beforeEach(() => {
  vi.clearAllMocks()
  for (const method of Object.values(http)) method.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'test-token')
  document.body.innerHTML = ''
})

describe('Tasks 审批历史', () => {
  it('TC-INT-2308 / AC-370-02、AC-371-02：已处理显示在途摘要，时间线完整且没有再次审批入口', async () => {
    http.get.mockImplementation(async (url, config = {}) => {
      if (url === '/approval/tasks') {
        return config.params.view === 'handled'
          ? { count: 1, page: 1, page_size: 20, results: [taskRow(7)] }
          : { count: 0, page: 1, page_size: 20, results: [] }
      }
      if (url === '/approval/instances/7') return {
        id: 7, subject_title: '决议7', status: 'PENDING', current_step_order: 2,
        submitted_at: '2026-11-27T08:00:00+08:00', submitter: { display_name: '提交人' },
        steps: [
          { order: 1, name: '财务初审', strategy: 'ANY', status: 'APPROVED', reached_at: '2026-11-27T08:00:00+08:00',
            approvers: [{ id: 2, display_name: '审批一', avatar_url: null }],
            actions: [{ actor_id: 2, actor_label: '审批一', actor_avatar_url: null, action: 'APPROVE', comment: '同意', acted_at: '2026-11-27T09:00:00+08:00' }] },
          { order: 2, name: '主任终审', strategy: 'ANY', status: 'ACTIVE', reached_at: '2026-11-27T09:00:00+08:00',
            approvers: [{ id: 3, display_name: '审批二', avatar_url: null }], actions: [] }
        ]
      }
      throw new Error(`未预期 GET ${url}`)
    })
    const { wrapper } = await mountPage(Tasks)
    await flush()
    await tab(wrapper, '已处理').trigger('click')
    await flush()

    expect(http.get).toHaveBeenCalledWith('/approval/tasks', {
      params: { view: 'handled', page: 1, page_size: 20 }
    })
    const text = wrapper.text()
    for (const expected of ['决议7', '我的处理：通过', '审批意见：同意', '审批中', '当前第 2 步 · 主任终审'])
      expect(text).toContain(expected)
    expect(button(wrapper, '同意')).toBeUndefined()
    expect(button(wrapper, '拒绝')).toBeUndefined()

    await button(wrapper, '审批过程').trigger('click')
    await flush()
    const detail = document.body.textContent
    for (const expected of ['财务初审', '主任终审', '审批一', '备注：同意', '审批中'])
      expect(detail).toContain(expected)
    expect(http.post).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('TC-INT-2309 / AC-370-04、AC-371-01、04：空态不影响待办；筛选与翻页重置并传递正确参数', async () => {
    http.get.mockImplementation(async (url, config = {}) => {
      if (url !== '/approval/tasks') throw new Error(`未预期 GET ${url}`)
      return config.params.view === 'handled'
        ? { count: 0, page: 1, page_size: 20, results: [] }
        : { count: 1, page: 1, page_size: 20, results: [taskRow(1, { status: undefined })] }
    })
    const empty = await mountPage(Tasks)
    await flush()
    await tab(empty.wrapper, '已处理').trigger('click')
    await flush()
    expect(empty.wrapper.text()).toContain('暂无已处理记录')
    await tab(empty.wrapper, '待办').trigger('click')
    await flush()
    expect(empty.wrapper.text()).toContain('决议1')
    empty.wrapper.unmount()
    document.body.innerHTML = ''

    http.get.mockImplementation(async (url, config = {}) => {
      if (url !== '/approval/tasks') throw new Error(`未预期 GET ${url}`)
      const params = config.params
      if (params.view === 'todo') return { count: 0, page: 1, page_size: 20, results: [] }
      if (params.scope === 'RESOLUTION') return { count: 2, page: 1, page_size: 20, results: [taskRow(101), taskRow(102)] }
      const start = (params.page - 1) * 20
      const count = params.page === 1 ? 20 : 5
      return { count: 25, page: params.page, page_size: 20,
        results: Array.from({ length: count }, (_, index) => taskRow(start + index + 1)) }
    })
    const { wrapper } = await mountPage(Tasks)
    await flush()
    await tab(wrapper, '已处理').trigger('click')
    await flush()
    expect(wrapper.findAll('.list-item')).toHaveLength(20)
    expect(wrapper.find('.pager-total').text()).toBe('共 25 条')

    await wrapper.findComponent(PagerBar).vm.$emit('change', 2)
    await flush()
    expect(wrapper.findAll('.list-item')).toHaveLength(5)
    expect(http.get).toHaveBeenLastCalledWith('/approval/tasks', {
      params: { view: 'handled', page: 2, page_size: 20 }
    })

    const scopeSelect = wrapper.findComponent({ name: 'ElSelect' })
    scopeSelect.vm.$emit('update:modelValue', 'RESOLUTION')
    await flush()
    scopeSelect.vm.$emit('change', 'RESOLUTION')
    await flush()
    expect(wrapper.findAll('.list-item')).toHaveLength(2)
    expect(wrapper.find('.pager-total').text()).toBe('共 2 条')
    expect(http.get).toHaveBeenLastCalledWith('/approval/tasks', {
      params: { scope: 'RESOLUTION', view: 'handled', page: 1, page_size: 20 }
    })
    wrapper.unmount()
  })
})

describe('同住人通过与申请人记录', () => {
  it('TC-INT-2310 / AC-372-01、02：通过后待审移除并刷新已通过记录；初始空态正确', async () => {
    const pendingRow = { id: 8, unit: { unit_id: 1, specific_part: 'A房' }, status: 'PENDING',
      applicant_name: '张同住', created_at: '2026-11-27T08:00:00+08:00',
      applicant: { id: 2, nickname: '小王', account_no: '8002' } }
    const approvedRow = { ...pendingRow, status: 'APPROVED', decided_at: '2026-11-27T09:00:00+08:00',
      decision_note: '已核实' }
    let pending = [pendingRow]
    let approved = []
    http.get.mockImplementation(async (url) => {
      if (url === '/resident-applications/to-review') return pending
      if (url === '/resident-applications/approved') return approved
      if (url === '/resident-applications/mine' || url === '/appeals/mine') return []
      if (url === '/me/housing') return { summary: { code: 'HEAD', label: '户主' }, units: [], pending_review_count: pending.length }
      throw new Error(`未预期 GET ${url}`)
    })
    http.post.mockImplementation(async (url, data) => {
      expect(url).toBe('/resident-applications/8/decision')
      expect(data).toEqual({ decision: 'APPROVE' })
      pending = []
      approved = [approvedRow]
      return approvedRow
    })
    const { wrapper } = await mountPage(UnitsReview)
    await flush()
    expect(wrapper.text()).toContain('暂无已通过的同住人申请')
    expect(wrapper.text()).toContain('小王')

    await button(wrapper, '通过').trigger('click')
    await flush()
    const cards = wrapper.findAll('.card')
    expect(cards[0].text()).toContain('暂无待审批的同住人申请')
    expect(cards[1].text()).toContain('A房')
    expect(cards[1].text()).toContain('申请人实名：张同住')
    expect(cards[1].text()).toContain('处理备注：已核实')
    expect(cards[1].text()).toContain('通过')
    expect(cards[1].findAll('button')).toHaveLength(0)
    expect(http.get.mock.calls.filter((call) => call[0] === '/resident-applications/approved')).toHaveLength(2)
    wrapper.unmount()
  })

  it('TC-INT-2311 / AC-373-01：申请人记录继续显示通过状态、处理时间和备注', async () => {
    http.get.mockImplementation(async (url) => {
      if (url === '/resident-applications/mine') return [{
        id: 9, unit: { unit_id: 1, specific_part: 'A房' }, status: 'APPROVED', applicant_name: '张同住',
        created_at: '2026-11-27T08:00:00+08:00', decided_at: '2026-11-27T09:00:00+08:00', decision_note: '已核实'
      }]
      if (url === '/resident-applications/to-review' || url === '/appeals/mine') return []
      throw new Error(`未预期 GET ${url}`)
    })
    const { wrapper } = await mountPage(UnitsApplicationRecords)
    await flush()
    const text = wrapper.text()
    for (const expected of ['A房', '处理结果：已通过', '处理备注：已核实', '处理 2026'])
      expect(text).toContain(expected)
    expect(text).not.toContain('其他申请人')
    wrapper.unmount()
  })
})
