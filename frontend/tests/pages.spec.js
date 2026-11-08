// TC-WEB-017~：关键页面挂载渲染与提交（真实页面 + 真实 api.js + 真实 store，仅 mock HTTP 层）
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Home from '@/portal/Home.vue'
import Claims from '@/portal/Claims.vue'
import PollDetail from '@/portal/PollDetail.vue'
import Me from '@/portal/Me.vue'
import { useAuthStore } from '@/stores/auth'

const { http } = mocked

const ME = (labels, position = null) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: labels.includes('游客'),
    units: [],
    committee: position ? { position, term_end: '2027-01-01' } : null,
    labels
  }
})

const FLOWS = { results: [{ id: 7, name: '报销流程', mode: 'DESIGNATED' }] }

const button = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('首页身份显示（CR-012）', () => {
  it('TC-WEB-017 委员：显示 identities.labels、昵称、手机号，并出现“收入表”入口', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['户主', '业委会委员'], 'MEMBER'),
      '/resolutions': { results: [{ id: 1, title: '加装电梯决议', status: 'APPROVED' }] }
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('你好，张三')
    expect(text).toContain('当前身份：户主、业委会委员')
    expect(text).toContain('手机号：138****0000')
    expect(text).toContain('加装电梯决议')
    expect(text).toContain('收入表')
    expect(http.get).toHaveBeenCalledWith('/resolutions', { params: { scope: 'public', page_size: 5 } })
  })

  it('TC-WEB-018 游客：显示“游客”，无“收入表”入口', async () => {
    http.get.mockImplementation(routeTable({ '/me': ME(['游客']), '/resolutions': { results: [] } }))
    const { wrapper } = await mountPage(Home)
    expect(wrapper.text()).toContain('当前身份：游客')
    expect(wrapper.text()).not.toContain('收入表')
    expect(wrapper.text()).toContain('暂无公开决议')
  })
})

describe('报销与核销表单（CR-013）', () => {
  const claimsRoutes = (me) => routeTable({
    '/me': me,
    '/claims': (arg) => ({ results: arg?.params?.type === 'ADVANCE'
      ? [{ id: 11, type: 'ADVANCE', amount: '1000.00', reason: '活动备用金', status: 'APPROVED', settlement_id: null }]
      : arg?.params?.type === 'REIMBURSEMENT'
        ? [{ id: 12, type: 'REIMBURSEMENT', amount: '800.00', reason: '购物', status: 'APPROVED', settlement_id: null }]
        : [] }),
    '/approval/flows': FLOWS
  })

  it('TC-WEB-019 挂载后按 scope=mine 拉取列表、按 EXPENSE 拉取审批流程；委员可见“备用金核销”', async () => {
    http.get.mockImplementation(claimsRoutes(ME(['户主', '业委会委员'], 'MEMBER')))
    const { wrapper } = await mountPage(Claims)
    expect(http.get).toHaveBeenCalledWith('/claims', { params: { scope: 'mine' } })
    expect(http.get).toHaveBeenCalledWith('/approval/flows', { params: { scope: 'EXPENSE' } })
    expect(wrapper.text()).toContain('报销 / 备用金')
    expect(button(wrapper, '备用金核销')).toBeTruthy()
  })

  it('TC-WEB-020 非委员看不到“备用金核销”按钮', async () => {
    http.get.mockImplementation(claimsRoutes(ME(['游客'])))
    const { wrapper } = await mountPage(Claims)
    expect(button(wrapper, '备用金核销')).toBeUndefined()
  })

  it('TC-WEB-021 报销提交：先上传发票(purpose=INVOICE)，再 POST /claims/reimbursements 带全部必填字段', async () => {
    http.get.mockImplementation(claimsRoutes(ME(['户主', '业委会委员'], 'MEMBER')))
    http.post.mockImplementation(async (url) => (url === '/attachments' ? { id: 'att-1' } : { id: 99 }))
    const { wrapper } = await mountPage(Claims)
    await wrapper.vm.uploadInvoice({ file: new File(['x'], 'inv.pdf') })
    const upload = http.post.mock.calls.find((c) => c[0] === '/attachments')
    expect(upload[1].get('purpose')).toBe('INVOICE')
    Object.assign(wrapper.vm.form, {
      type: 'REIMBURSEMENT', amount: '300.50', reason: '购买灯泡', occurred_on: '2026-11-01', approval_flow_id: 7
    })
    await wrapper.vm.create()
    await flushPromises()
    expect(http.post).toHaveBeenLastCalledWith('/claims/reimbursements', {
      amount: '300.50', reason: '购买灯泡', occurred_on: '2026-11-01',
      invoice_ids: ['att-1'], approval_flow_id: 7
    })
  })

  it('TC-WEB-022 备用金预借：POST /claims/advances 带 expected_usage / expected_settle_on', async () => {
    http.get.mockImplementation(claimsRoutes(ME(['户主', '业委会委员'], 'MEMBER')))
    http.post.mockResolvedValue({ id: 5 })
    const { wrapper } = await mountPage(Claims)
    Object.assign(wrapper.vm.form, {
      type: 'ADVANCE', amount: '1000.00', reason: '活动', expected_usage: '小区活动',
      expected_settle_on: '2026-12-01', approval_flow_id: 7
    })
    await wrapper.vm.create()
    expect(http.post).toHaveBeenLastCalledWith('/claims/advances', {
      amount: '1000.00', reason: '活动', expected_usage: '小区活动',
      expected_settle_on: '2026-12-01', approval_flow_id: 7
    })
  })

  it('TC-WEB-023 核销：载入已通过未核销的预借与报销单，差额提示“多退/少补”，提交 POST /claims/settlements', async () => {
    http.get.mockImplementation(claimsRoutes(ME(['户主', '业委会委员'], 'MEMBER')))
    http.post.mockResolvedValue({ id: 30 })
    const { wrapper } = await mountPage(Claims)
    await wrapper.vm.openSettle()
    expect(http.get).toHaveBeenCalledWith('/claims', {
      params: { scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 } })
    expect(http.get).toHaveBeenCalledWith('/claims', {
      params: { scope: 'mine', type: 'REIMBURSEMENT', status: 'APPROVED', page_size: 100 } })
    Object.assign(wrapper.vm.settle, {
      advance_id: 11, reimbursement_ids: [12], reason: '活动核销', approval_flow_id: 7
    })
    expect(wrapper.vm.diffText).toContain('多退 ¥200.00')
    await wrapper.vm.submitSettle()
    expect(http.post).toHaveBeenLastCalledWith('/claims/settlements', {
      advance_id: 11, reimbursement_ids: [12], reason: '活动核销', approval_flow_id: 7
    })
  })

  it('TC-WEB-024 差额文案：报销 1200 > 预借 1000 → 少补 ¥200.00；相等 → 刚好核销', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['户主', '业委会委员'], 'MEMBER'),
      '/claims': (arg) => ({ results: arg?.params?.type === 'ADVANCE'
        ? [{ id: 11, amount: '1000.00', reason: 'a', settlement_id: null }]
        : arg?.params?.type === 'REIMBURSEMENT'
          ? [{ id: 12, amount: '1200.00', reason: 'b', settlement_id: null },
             { id: 13, amount: '1000.00', reason: 'c', settlement_id: null }]
          : [] }),
      '/approval/flows': FLOWS
    }))
    const { wrapper } = await mountPage(Claims)
    await wrapper.vm.openSettle()
    wrapper.vm.settle.advance_id = 11
    wrapper.vm.settle.reimbursement_ids = [12]
    expect(wrapper.vm.diffText).toContain('少补 ¥200.00')
    wrapper.vm.settle.reimbursement_ids = [13]
    expect(wrapper.vm.diffText).toContain('刚好核销')
  })
})

describe('投票提交（CR-014）', () => {
  const POLL = {
    id: 5, title: '加装电梯调查', description: 'd', kind: 'SURVEY', status: 'OPEN',
    deadline: '2026-12-01T00:00:00Z', can_respond: true,
    questions: [
      { id: 1, title: '单选题', qtype: 'SINGLE', required: true, options: ['甲', '乙'] },
      { id: 2, title: '表态题', qtype: 'AGREE_OPPOSE_ABSTAIN', required: true, options: [] },
      { id: 3, title: '多选题', qtype: 'MULTI', required: false, options: ['a', 'b', 'c'] },
      { id: 4, title: '打分题', qtype: 'SCORE', required: false, options: [] }
    ]
  }

  it('TC-WEB-025 按题型渲染并“一键提交”：POST /polls/5/responses，体为 {answers:[{question_id,value}]}', async () => {
    http.get.mockImplementation(routeTable({ '/polls/5': POLL }))
    http.post.mockResolvedValue({})
    const { wrapper } = await mountPage(PollDetail, { path: '/polls/5' })
    const text = wrapper.text()
    for (const t of ['加装电梯调查', '单选题', '表态题', '多选题', '打分题', '调查']) expect(text).toContain(t)
    wrapper.vm.answers[1] = '甲'
    wrapper.vm.answers[2] = 'AGREE'
    wrapper.vm.answers[3] = ['a', 'c']
    wrapper.vm.answers[4] = 5
    await flushPromises()
    await button(wrapper, '一键提交').trigger('click')
    await flushPromises()
    expect(http.post).toHaveBeenCalledWith('/polls/5/responses', {
      answers: [
        { question_id: 1, value: '甲' },
        { question_id: 2, value: 'AGREE' },
        { question_id: 3, value: ['a', 'c'] },
        { question_id: 4, value: '5' }
      ]
    })
  })

  it('TC-WEB-026 未填写的选答题不提交；已作答（my_response）时不显示提交按钮并回填答案', async () => {
    http.get.mockImplementation(routeTable({
      '/polls/5': { ...POLL, my_response: [
        { question_id: 1, value: '乙' }, { question_id: 3, value: 'a,c' }, { question_id: 4, value: '4' }] }
    }))
    const { wrapper } = await mountPage(PollDetail, { path: '/polls/5' })
    expect(button(wrapper, '一键提交')).toBeUndefined()
    expect(wrapper.text()).toContain('你已提交')
    expect(wrapper.vm.answers[1]).toBe('乙')
    expect(wrapper.vm.answers[3]).toEqual(['a', 'c'])
    expect(wrapper.vm.answers[4]).toBe(4)
  })

  it('TC-WEB-027 截止后“查看结果”：GET /polls/5/result，展示参与人数与选项占比', async () => {
    http.get.mockImplementation(routeTable({
      '/polls/5': { ...POLL, status: 'CLOSED', can_respond: false },
      '/polls/5/result': { results: { responses: 1, participants: 3, questions: [
        { id: 1, title: '单选题', options: [{ value: '甲', count: 1, percentage: 100.0 }, { value: '乙', count: 0, percentage: 0.0 }] }] } }
    }))
    const { wrapper } = await mountPage(PollDetail, { path: '/polls/5' })
    await button(wrapper, '查看结果').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('结果（参与 1 / 3）')
    expect(wrapper.text()).toContain('甲：1（100%）')
  })
})

describe('绑定 / 换绑手机号（CR-019）', () => {
  it('TC-WEB-028 已有手机号 → 显示“更换手机号”；换绑 POST /me/phone/change，合并时换用新令牌并重取 /me', async () => {
    http.get.mockImplementation(routeTable({
      '/me/profile': { nickname: '张三', gender: 0, phone: '138****0000', email: null },
      '/me': ME(['户主'])
    }))
    http.post.mockResolvedValue({ merged: true, token: 'MERGED-TOKEN', user: { id: 2 } })
    const { wrapper } = await mountPage(Me)
    const titles = wrapper.findAll('h3').map((h) => h.text())
    expect(titles).toContain('更换手机号')
    expect(titles).not.toContain('绑定手机号')
    Object.assign(wrapper.vm.change, {
      oldPhone: '13800000000', newPhone: '13900000000', oldCode: '111111', newCode: '222222'
    })
    await wrapper.vm.changePhone()
    await flushPromises()
    expect(http.post).toHaveBeenCalledWith('/me/phone/change', {
      old_phone: '13800000000', new_phone: '13900000000', old_code: '111111', new_code: '222222'
    })
    expect(useAuthStore().token).toBe('MERGED-TOKEN')
    expect(localStorage.getItem('ocap_token')).toBe('MERGED-TOKEN')
    expect(http.get).toHaveBeenCalledWith('/me', { params: undefined })
  })

  it('TC-WEB-029 无手机号（仅微信登录）→ 显示“绑定手机号”；发码 POST /me/codes，绑定 POST /me/phone/bind；未合并不换令牌', async () => {
    http.get.mockImplementation(routeTable({
      '/me/profile': { nickname: '微信用户', gender: 0, phone: null, email: null },
      '/me': ME(['游客'])
    }))
    http.post.mockResolvedValue({ merged: false, phone: '139****0000' })
    const { wrapper } = await mountPage(Me)
    const titles = wrapper.findAll('h3').map((h) => h.text())
    expect(titles).toContain('绑定手机号')
    expect(titles).not.toContain('更换手机号')
    Object.assign(wrapper.vm.bind, { phone: '13900000000', code: '123456' })
    await wrapper.vm.sendBindCode()
    expect(http.post).toHaveBeenCalledWith('/me/codes', { purpose: 'BIND_PHONE', target: '13900000000' })
    await wrapper.vm.bindPhone()
    await flushPromises()
    expect(http.post).toHaveBeenLastCalledWith('/me/phone/bind', { phone: '13900000000', code: '123456' })
    expect(useAuthStore().token).toBe('tok')
  })

  it('TC-WEB-030 改密字段 PUT /me/password {password,password_confirm}；注销带 phone 与 code', async () => {
    http.get.mockImplementation(routeTable({
      '/me/profile': { nickname: 'x', gender: 0, phone: '138****0000', email: null }
    }))
    http.put.mockResolvedValue({})
    http.post.mockResolvedValue({})
    const { wrapper } = await mountPage(Me)
    Object.assign(wrapper.vm.pwd, { current: '', password: 'Ocap2026pass', confirm: 'Ocap2026pass' })
    await wrapper.vm.savePassword()
    expect(http.put).toHaveBeenCalledWith('/me/password', { password: 'Ocap2026pass', password_confirm: 'Ocap2026pass' })
    Object.assign(wrapper.vm.cancel, { phone: '13800000000', code: '654321' })
    await wrapper.vm.cancelAccount()
    expect(http.post).toHaveBeenCalledWith('/me/cancel', { phone: '13800000000', code: '654321' })
  })
})
