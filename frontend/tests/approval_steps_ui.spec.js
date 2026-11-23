// GROUP_D：多步审批前端界面（ocap_approval_flow）。只 mock '@/shared/api'，其余真实组件。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = vi.hoisted(() => ({
  admin: {
    flows: vi.fn(),
    createFlow: vi.fn(),
    updateFlow: vi.fn(),
    deleteFlow: vi.fn(),
    users: vi.fn()
  },
  approvalApi: {
    tasks: vi.fn(),
    decide: vi.fn(),
    instance: vi.fn()
  }
}))
vi.mock('@/shared/api', () => mocked)

import { mountPage } from './helpers.js'
import AdminFlows from '@/admin/AdminFlows.vue'
import StepsEditor from '@/admin/parts/StepsEditor.vue'
import ApprovalTimeline from '@/portal/ApprovalTimeline.vue'
import Tasks from '@/portal/Tasks.vue'

const { admin, approvalApi } = mocked
const flush = async () => {
  await flushPromises()
  await new Promise((r) => setTimeout(r, 0))
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  document.body.innerHTML = ''
})

describe('StepsEditor（US-311 / AC-316-01、AC-325-01）', () => {
  it('TC-UNIT-1301 / AC-316-01：按顺序展示步骤名称与策略', async () => {
    const { wrapper } = await mountPage(StepsEditor, {
      props: {
        steps: [
          { name: '财务初审', strategy: 'ANY', approvers: [] },
          { name: '主任终审', strategy: 'ALL', approvers: [] }
        ]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('第 1 步')
    expect(text).toContain('第 2 步')
    const values = wrapper.findAll('input').map((i) => i.element.value)
    expect(values).toContain('财务初审')
    expect(values).toContain('主任终审')
  })

  it('TC-UNIT-1302 / AC-325-01：下移发出 move 事件', async () => {
    const { wrapper } = await mountPage(StepsEditor, {
      props: { steps: [{ name: 'A', strategy: 'ANY', approvers: [] }, { name: 'B', strategy: 'ANY', approvers: [] }] }
    })
    const down = wrapper.findAll('button').find((b) => b.text().includes('下移'))
    await down.trigger('click')
    expect(wrapper.emitted('move')[0]).toEqual([0, 1])
  })
})

describe('AdminFlows 步骤配置（US-311 / AC-316-01、AC-318-01）', () => {
  it('TC-UNIT-1303 / AC-316-01：展示步骤数并提交嵌套 steps', async () => {
    admin.flows.mockResolvedValue({
      count: 1,
      results: [{
        id: 9, name: '两步流程', scope: 'RESOLUTION', mode: 'DESIGNATED', is_active: true, step_count: 2,
        steps: [
          { order: 1, name: '初审', strategy: 'ANY', approvers: [{ id: 2, display_name: '业主乙' }] },
          { order: 2, name: '终审', strategy: 'ALL', approvers: [{ id: 3, display_name: '业主丙' }] }
        ]
      }]
    })
    admin.createFlow.mockResolvedValue({ id: 10 })
    const { wrapper } = await mountPage(AdminFlows)
    await flush()
    expect(wrapper.text()).toContain('两步流程')

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('新建流程'))
    await createButton.trigger('click')
    await flush()
    const addButton = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('添加步骤'))
    expect(addButton).toBeTruthy()
    addButton.click()
    await flush()

    const setValue = async (el, value) => {
      el.value = value
      el.dispatchEvent(new Event('input', { bubbles: true }))
    }
    const nameInput = document.querySelector('.el-dialog input[placeholder="流程名称"]')
    const stepInputs = [...document.querySelectorAll('.el-dialog input[placeholder^="步骤名称"]')]
    await setValue(nameInput, '新流程')
    await setValue(stepInputs[0], '初审')
    await setValue(stepInputs[1], '终审')
    const save = [...document.querySelectorAll('.el-dialog button')].find((b) => b.textContent.trim() === '保存')
    save.click()
    await flush()
    expect(admin.createFlow).toHaveBeenCalledTimes(1)
    const payload = admin.createFlow.mock.calls[0][0]
    expect(payload.name).toBe('新流程')
    expect(payload.steps).toHaveLength(2)
    expect(payload.steps.map((s) => s.name)).toEqual(['初审', '终审'])
    expect(payload.steps[0].approver_ids).toEqual([])
  })

  it('详情弹窗展示步骤序号（回归：不能丢 order）', async () => {
    admin.flows.mockResolvedValue({
      count: 1,
      results: [{
        id: 9, name: '两步流程', scope: 'RESOLUTION', mode: 'DESIGNATED', is_active: true, step_count: 2,
        steps: [
          { order: 1, name: '初审', strategy: 'ANY', approvers: [{ id: 2, display_name: '业主乙' }] },
          { order: 2, name: '终审', strategy: 'ALL', approvers: [{ id: 3, display_name: '业主丙' }] }
        ]
      }]
    })
    const { wrapper } = await mountPage(AdminFlows)
    await flush()
    const detailButton = wrapper.findAll('button').find((b) => b.text().includes('查看详情'))
    await detailButton.trigger('click')
    await flush()
    const text = document.body.textContent
    expect(text).toContain('第 1 步')
    expect(text).toContain('第 2 步')
  })
})

describe('ApprovalTimeline（US-317 / AC-328-01、AC-328-03）', () => {
  it('TC-INT-1304 / AC-328-01：展示步骤、审批人与备注', async () => {
    approvalApi.instance.mockResolvedValue({
      id: 5, subject_title: '加装电梯', status: 'PENDING', current_step_order: 2,
      submitted_at: '2026-11-22T10:00:00+08:00',
      submitter: { id: 1, display_name: '业主甲', avatar_url: null },
      steps: [
        {
          order: 1, name: '财务初审', strategy: 'ANY', status: 'APPROVED',
          reached_at: '2026-11-22T10:00:00+08:00',
          approvers: [{ id: 2, display_name: '业主乙', avatar_url: null }],
          actions: [{ actor_id: 2, actor_label: '业主乙', action: 'APPROVE', comment: '同意', acted_at: '2026-11-22T10:05:00+08:00' }]
        },
        { order: 2, name: '主任终审', strategy: 'ALL', status: 'ACTIVE', reached_at: null, approvers: [{ id: 3, display_name: '业主丙', avatar_url: null }], actions: [] }
      ]
    })
    const { wrapper } = await mountPage(ApprovalTimeline, { props: { instanceId: 5 } })
    await flush()
    await flush()
    const text = wrapper.text()
    expect(text).toContain('提交人：业主甲')
    expect(text).toContain('业主乙')
    expect(text).toContain('业主丙')
    expect(text).toContain('财务初审')
    expect(text).toContain('第 1 步')
    expect(text).toContain('已通过')
    expect(text).toContain('备注：同意')
    expect(text).toContain('主任终审')
    expect(text).toContain('未开始')
  })
})

describe('Tasks（US-313 / AC-322-01、AC-332-02）', () => {
  it('TC-INT-1305 / AC-322-01：待办显示当前步骤并可带备注提交', async () => {
    approvalApi.tasks.mockResolvedValue({
      count: 1, page: 1, page_size: 20,
      results: [{
        instance_id: 7, scope: 'EXPENSE', subject_title: '报销单',
        submitter: { id: 9, display_name: '业主丁', avatar_url: null }, submitter_label: '业主丁',
        submitted_at: '2026-11-22T10:00:00+08:00',
        step_order: 1, step_name: '财务初审', step_strategy: 'ANY'
      }]
    })
    approvalApi.decide.mockResolvedValue({})
    const { wrapper } = await mountPage(Tasks)
    await flush()
    expect(wrapper.text()).toContain('财务初审')
    expect(wrapper.text()).toContain('或签')
    expect(wrapper.text()).toContain('提交人：业主丁')

    const approve = wrapper.findAll('button').find((b) => b.text().includes('同意'))
    await approve.trigger('click')
    await flush()
    const textarea = document.querySelector('.el-dialog textarea')
    textarea.value = '票据齐全'
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    const confirm = [...document.querySelectorAll('.el-dialog button')].find((b) => b.textContent.trim() === '确认')
    confirm.click()
    await flush()
    expect(approvalApi.decide).toHaveBeenCalledWith(7, 'APPROVE', '票据齐全')
  })
})
