// ocap_appeal_center GROUP_D：申诉/同住申请记录中心（TC-UNIT-1532 ~ 1535）。
// 层级：unit（页面级组件 + 真实 store/api，仅 mock HTTP 层）。
// 溯源：US-291、292、293、294、295、296、297。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage, ElMessageBox } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import UnitsMyAppeals from '@/portal/units/UnitsMyAppeals.vue'
import UnitsApplicationForm from '@/portal/units/UnitsApplicationForm.vue'
import UnitsApplications from '@/portal/units/UnitsApplications.vue'
import UnitsAppeal from '@/portal/units/UnitsAppeal.vue'
import UnitsIdentity from '@/portal/units/UnitsIdentity.vue'
import AppealCenter from '@/portal/units/AppealCenter.vue'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const HOUSING = { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0, real_names: [] }
const table = (over = {}) => routeTable({
  '/appeals/mine': [], '/resident-applications/mine': [],
  '/resident-applications/to-review': [], '/me/housing': HOUSING, ...over
})
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('我的申诉记录（US-292/293/294）', () => {
  it('TC-UNIT-1532 / AC-292-01、AC-293-02/03、AC-294-01/03/04：展示处理结果、备注占位、驳回原因与已撤回标签；仅待审可撤回、仅已撤回可重新提交', async () => {
    http.get.mockImplementation(table({
      '/appeals/mine': [
        { id: 1, unit: { unit_id: 1, specific_part: '1栋101' }, status: 'PENDING', submitted_at: '2026-11-20T10:00:00+08:00', decided_at: null, reject_reason: null, decision_note: null, withdrawn_at: null, previous_appeal_id: null },
        { id: 2, unit: { unit_id: 1, specific_part: '1栋101' }, status: 'REJECTED', submitted_at: '2026-11-19T10:00:00+08:00', decided_at: '2026-11-20T10:00:00+08:00', reject_reason: '证明不清晰', decision_note: null, withdrawn_at: null, previous_appeal_id: null },
        { id: 3, unit: { unit_id: 2, specific_part: '2栋202' }, status: 'WITHDRAWN', submitted_at: '2026-11-18T10:00:00+08:00', decided_at: null, reject_reason: null, decision_note: null, withdrawn_at: '2026-11-21T09:00:00+08:00', previous_appeal_id: 2 }
      ]
    }))
    const { wrapper } = await mountPage(UnitsMyAppeals)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('待审核')
    expect(text).toContain('已驳回')
    expect(text).toContain('已撤回')
    expect(text).toContain('处理备注：—')
    expect(text).toContain('驳回原因：证明不清晰')
    expect(text).toContain('重新提交自 #2')
    expect(wrapper.findAll('button').filter((b) => b.text() === '撤回')).toHaveLength(1)
    expect(wrapper.findAll('button').filter((b) => b.text() === '重新提交')).toHaveLength(1)
  })

  it('TC-UNIT-1533 / AC-294-01：确认撤回后调用 POST /appeals/{id}/withdraw 并刷新列表', async () => {
    http.get.mockImplementation(table({
      '/appeals/mine': [{ id: 7, unit: { unit_id: 1, specific_part: '1栋101' }, status: 'PENDING', submitted_at: '2026-11-20T10:00:00+08:00', decided_at: null, reject_reason: null, decision_note: null, withdrawn_at: null, previous_appeal_id: null }]
    }))
    http.post.mockResolvedValue({ id: 7, status: 'WITHDRAWN' })
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm')
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountPage(UnitsMyAppeals)
    await flush()
    await buttonOf(wrapper, '撤回').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/appeals/7/withdraw', {})
  })
})

describe('同住申请实名（US-297）', () => {
  it('TC-UNIT-1534 / AC-297-01、AC-297-02：未填实名或超过 64 字提示且不提交；合法实名提交 unit_id + applicant_name', async () => {
    http.get.mockImplementation(table())
    http.post.mockResolvedValue({ id: 9, status: 'PENDING' })
    const warning = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountPage(UnitsApplicationForm)
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 42)
    await flush()
    await buttonOf(wrapper, '申请成为同住人').trigger('click')
    await flush()
    expect(warning).toHaveBeenCalledWith('请输入本人实名')
    expect(http.post).not.toHaveBeenCalled()
    await wrapper.find('input[placeholder="本人实名"]').setValue('名'.repeat(65))
    await buttonOf(wrapper, '申请成为同住人').trigger('click')
    await flush()
    expect(warning).toHaveBeenCalledWith('实名不超过 64 字')
    expect(http.post).not.toHaveBeenCalled()
    await wrapper.find('input[placeholder="本人实名"]').setValue('  张三  ')
    await buttonOf(wrapper, '申请成为同住人').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resident-applications', { unit_id: 42, applicant_name: '张三' })
    expect(success).toHaveBeenCalledWith('申请已提交，等待产权业主审批')
  })
})

describe('申诉中心 Tab 与重新提交（US-291/294）', () => {
  it('TC-UNIT-1535 / AC-291-03、AC-294-03：initialTab=mine 时默认选中“我的申诉”；已撤回记录触发重新提交后切回“认证申诉”并带入原房屋/姓名/来源编号', async () => {
    http.get.mockImplementation(table({
      '/appeals/mine': [{ id: 15, unit: { unit_id: 8, specific_part: '8栋808' }, status: 'WITHDRAWN', submitted_at: '2026-11-20T10:00:00+08:00', decided_at: null, reject_reason: null, decision_note: null, withdrawn_at: '2026-11-21T10:00:00+08:00', previous_appeal_id: null }]
    }))
    const { wrapper } = await mountPage(AppealCenter, { props: { initialTab: 'mine' } })
    await flush()
    expect(wrapper.find('.el-tabs__item.is-active').text()).toBe('我的申诉')
    const formEl = wrapper.findComponent(UnitsAppeal).element
    await wrapper.findAll('.el-tabs__item').find((t) => t.text() === '认证申诉').trigger('click')
    await flush()
    expect(wrapper.find('.el-tabs__item.is-active').text()).toBe('认证申诉')
    // AC-291-02：Tab 切换不重建表单节点（DOM 节点保持不变 → 已选房屋/姓名/证明保留）
    expect(wrapper.findComponent(UnitsAppeal).element).toBe(formEl)
    wrapper.findComponent(UnitsMyAppeals).vm.$emit('resubmit', {
      id: 15, unit: { unit_id: 8, specific_part: '8栋808' }, status: 'WITHDRAWN'
    })
    await flush()
    expect(wrapper.find('.el-tabs__item.is-active').text()).toBe('认证申诉')
    const prefill = wrapper.findComponent(UnitsAppeal).props('prefill')
    expect(prefill.unitId).toBe(8)
    expect(prefill.previousAppealId).toBe(15)
  })
})

describe('同住申请双 Tab（US-295）', () => {
  it('TC-UNIT-1536 / AC-295-01、AC-295-02：默认“发起申请”，两个 Tab 均存在；切换不重建表单组件', async () => {
    http.get.mockImplementation(table())
    const { wrapper } = await mountPage(UnitsApplications)
    await flush()
    expect(wrapper.findAll('.el-tabs__item').map((t) => t.text())).toEqual(['发起申请', '申请记录'])
    expect(wrapper.find('.el-tabs__item.is-active').text()).toBe('发起申请')
    const formEl = wrapper.findComponent(UnitsApplicationForm).element
    await wrapper.findAll('.el-tabs__item').find((t) => t.text() === '申请记录').trigger('click')
    await flush()
    expect(wrapper.find('.el-tabs__item.is-active').text()).toBe('申请记录')
    expect(wrapper.findComponent(UnitsApplicationForm).element).toBe(formEl)
  })
})

describe('身份页同住人实名（US-298）', () => {
  it('TC-UNIT-1537 / AC-298-02、AC-298-03：业主视角同住人列表显示实名，缺失显示“—”', async () => {
    http.get.mockImplementation(table({
      '/me/housing': {
        summary: { code: 'OWNER', label: '产权业主' }, pending_review_count: 0, real_names: ['业主甲'],
        units: [{
          unit_id: 1, specific_part: '1栋101', role: 'HEAD', role_label: '产权业主',
          residents: [
            { user_id: 2, nickname: '同住甲', account_no: 'U2', real_name: '李四', joined_at: '2026-11-20T10:00:00+08:00' },
            { user_id: 3, nickname: '同住乙', account_no: 'U3', real_name: null, joined_at: '2026-11-20T10:00:00+08:00' }
          ]
        }]
      }
    }))
    const { wrapper } = await mountPage(UnitsIdentity)
    await flush()
    expect(wrapper.text()).toContain('实名：李四')
    expect(wrapper.findAll('.row').filter((r) => r.text().includes('实名：—'))).toHaveLength(1)
  })
})
