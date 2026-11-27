// ocap_approval_history GROUP_D PHASE_09：审批与同住人历史完整用户旅程。
// critical path 口径：替代——画像无浏览器 E2E 框架；挂载真实页面、api.js 与 Pinia，仅 HTTP 层使用有状态替身。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage } from './helpers.js'
import Tasks from '@/portal/Tasks.vue'
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
const dialogButton = (text) => [...document.querySelectorAll('.el-dialog button')]
  .find((node) => node.textContent.trim() === text)

beforeEach(() => {
  vi.clearAllMocks()
  for (const method of Object.values(http)) method.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'test-token')
  document.body.innerHTML = ''
})

describe('审批历史 critical path', () => {
  it('TC-E2E-2301 / US-370、US-371 / AC-370-01、02，AC-371-02：待办同意并留意见 → 待办移除 → 已处理在途记录 → 完整只读时间线', async () => {
    let acted = false
    const todoRow = {
      instance_id: 7, scope: 'RESOLUTION', subject_type: 'resolution', subject_id: 7,
      subject_title: '更换电梯', submitter: { id: 9, display_name: '提交人', avatar_url: null },
      submitter_label: '提交人', submitted_at: '2026-11-27T08:00:00+08:00',
      step_order: 1, step_name: '财务初审', step_strategy: 'ANY'
    }
    const handledRow = {
      ...todoRow, status: 'PENDING', step_order: 2, step_name: '主任终审',
      my_action: 'APPROVE', my_acted_at: '2026-11-27T09:00:00+08:00',
      my_comment: '同意，预算清晰', my_step_order: 1, my_step_name: '财务初审'
    }
    http.get.mockImplementation(async (url, config = {}) => {
      if (url === '/approval/tasks') {
        if (config.params.view === 'handled') {
          return { count: acted ? 1 : 0, page: 1, page_size: 20, results: acted ? [handledRow] : [] }
        }
        return { count: acted ? 0 : 1, page: 1, page_size: 20, results: acted ? [] : [todoRow] }
      }
      if (url === '/approval/instances/7') return {
        id: 7, subject_title: '更换电梯', status: 'PENDING', current_step_order: 2,
        submitted_at: '2026-11-27T08:00:00+08:00', submitter: { display_name: '提交人' },
        steps: [
          { order: 1, name: '财务初审', strategy: 'ANY', status: 'APPROVED', reached_at: '2026-11-27T08:00:00+08:00',
            approvers: [{ id: 2, display_name: '审批一', avatar_url: null }],
            actions: [{ actor_id: 2, actor_label: '审批一', actor_avatar_url: null, action: 'APPROVE',
              comment: '同意，预算清晰', acted_at: '2026-11-27T09:00:00+08:00' }] },
          { order: 2, name: '主任终审', strategy: 'ANY', status: 'ACTIVE', reached_at: '2026-11-27T09:00:00+08:00',
            approvers: [{ id: 3, display_name: '审批二', avatar_url: null }], actions: [] }
        ]
      }
      throw new Error(`未预期 GET ${url}`)
    })
    http.post.mockImplementation(async (url, data) => {
      expect(url).toBe('/approval/instances/7/decision')
      expect(data).toEqual({ action: 'APPROVE', comment: '同意，预算清晰' })
      acted = true
      return handledRow
    })

    const { wrapper } = await mountPage(Tasks)
    await flush()
    expect(wrapper.text()).toContain('更换电梯')
    await button(wrapper, '同意').trigger('click')
    await flush()
    const textarea = document.querySelector('.el-dialog textarea')
    textarea.value = '同意，预算清晰'
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    await flush()
    await dialogButton('确认通过').click()
    await flush()

    expect(http.post).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('暂无待办')
    await tab(wrapper, '已处理').trigger('click')
    await flush()
    expect(wrapper.findAll('.list-item')).toHaveLength(1)
    for (const expected of ['更换电梯', '我的处理：通过', '审批意见：同意，预算清晰', '审批中', '当前第 2 步 · 主任终审'])
      expect(wrapper.text()).toContain(expected)
    expect(button(wrapper, '同意')).toBeUndefined()
    expect(button(wrapper, '拒绝')).toBeUndefined()

    await button(wrapper, '审批过程').trigger('click')
    await flush()
    const timeline = document.body.textContent
    for (const expected of ['提交人：提交人', '财务初审', '主任终审', '审批一', '审批二', '通过', '备注：同意，预算清晰', '审批中'])
      expect(timeline).toContain(expected)
    expect(http.post).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})

describe('同住人通过与申请人记录 critical path', () => {
  it('TC-E2E-2302 / US-372、US-373 / AC-372-01、02，AC-373-01、02：产权人通过申请 → 已通过记录 → 申请人只看本人通过结果', async () => {
    let currentUser = 'reviewer'
    const ownPending = {
      id: 8, unit: { unit_id: 1, specific_part: 'A房' }, status: 'PENDING', applicant_name: '张同住',
      created_at: '2026-11-27T08:00:00+08:00', decided_at: null, decision_note: null,
      applicant: { id: 2, nickname: '小王', account_no: '8002' }
    }
    const ownApproved = { ...ownPending, status: 'APPROVED', decided_at: '2026-11-27T09:00:00+08:00', decision_note: '已核实' }
    const otherApproved = {
      id: 9, unit: { unit_id: 1, specific_part: 'A房' }, status: 'APPROVED', applicant_name: '李其他',
      created_at: '2026-11-26T08:00:00+08:00', decided_at: '2026-11-26T09:00:00+08:00', decision_note: '既往通过',
      applicant: { id: 3, nickname: '其他申请人', account_no: '8003' }
    }
    const rejected = { ...ownPending, id: 10, status: 'REJECTED', applicant_name: '王拒绝',
      applicant: { id: 4, nickname: '被拒申请人', account_no: '8004' } }
    const otherUnitApproved = { ...otherApproved, id: 11, unit: { unit_id: 2, specific_part: 'B房' }, applicant_name: '他房业主' }
    let applications = [ownPending, otherApproved, rejected, otherUnitApproved]

    http.get.mockImplementation(async (url) => {
      if (url === '/resident-applications/to-review') {
        return currentUser === 'reviewer' ? applications.filter((row) => row.unit.unit_id === 1 && row.status === 'PENDING') : []
      }
      if (url === '/resident-applications/approved') {
        return currentUser === 'reviewer'
          ? applications.filter((row) => row.unit.unit_id === 1 && row.status === 'APPROVED')
          : []
      }
      if (url === '/resident-applications/mine') {
        const applicantId = currentUser === 'applicant' ? 2 : 1
        return applications.filter((row) => row.applicant.id === applicantId)
      }
      if (url === '/appeals/mine') return []
      if (url === '/me/housing') return {
        summary: { code: currentUser === 'reviewer' ? 'HEAD' : 'RESIDENT', label: currentUser === 'reviewer' ? '户主' : '同住人' },
        units: currentUser === 'reviewer' ? [{ unit_id: 1, role: 'HEAD' }] : [],
        pending_review_count: currentUser === 'reviewer' ? applications.filter((row) => row.status === 'PENDING').length : 0
      }
      throw new Error(`未预期 GET ${url}`)
    })
    http.post.mockImplementation(async (url, data) => {
      expect(url).toBe('/resident-applications/8/decision')
      expect(data).toEqual({ decision: 'APPROVE' })
      applications = applications.map((row) => row.id === 8 ? ownApproved : row)
      return ownApproved
    })

    const reviewer = await mountPage(UnitsReview)
    await flush()
    expect(reviewer.wrapper.text()).toContain('小王')
    expect(reviewer.wrapper.text()).toContain('其他申请人')
    expect(reviewer.wrapper.text()).not.toContain('王拒绝')
    expect(reviewer.wrapper.text()).not.toContain('B房')
    await button(reviewer.wrapper, '通过').trigger('click')
    await flush()
    expect(reviewer.wrapper.find('#review').text()).toContain('暂无待审批的同住人申请')
    const approvedCard = reviewer.wrapper.findAll('.card')[1]
    for (const expected of ['A房', '小王', '申请人实名：张同住', '处理备注：已核实', '处理 2026', '通过'])
      expect(approvedCard.text()).toContain(expected)
    expect(approvedCard.text()).not.toContain('王拒绝')
    expect(approvedCard.text()).not.toContain('B房')
    expect(approvedCard.findAll('button')).toHaveLength(0)
    reviewer.wrapper.unmount()
    document.body.innerHTML = ''

    currentUser = 'applicant'
    const applicant = await mountPage(UnitsApplicationRecords)
    await flush()
    const ownText = applicant.wrapper.text()
    for (const expected of ['A房', '实名：张同住', '处理结果：已通过', '处理备注：已核实', '处理 2026'])
      expect(ownText).toContain(expected)
    expect(ownText).not.toContain('其他申请人')
    expect(ownText).not.toContain('李其他')
    expect(applicant.wrapper.findAll('.list-item-top')).toHaveLength(1)
    applicant.wrapper.unmount()
  })
})
