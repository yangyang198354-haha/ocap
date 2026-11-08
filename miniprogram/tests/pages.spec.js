// TC-MP-014~：关键页面脚本与模板在 jsdom 中挂载（真实页面 + 真实 api.js/http.js/store；桩 uni 全局对象与 uni-app 生命周期钩子）。
// 说明：uni 运行时与微信真机行为不在此覆盖，见 e2e_test_report 人工验证清单。
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, respondWith, requests, byText } from './helpers.js'
import Index from '../pages/index/index.vue'
import Claims from '../pages/claims/index.vue'
import PollDetail from '../pages/polls/detail.vue'
import Phone from '../pages/phone/index.vue'
import Login from '../pages/login/index.vue'
import { useAuthStore } from '@/store/auth'

const ME = (labels, phone = '138****0000') => ({
  profile: { id: 1, nickname: '张三', phone },
  identities: { is_guest: labels.includes('游客'), units: [], committee: null, labels }
})

describe('首页身份显示（CR-012）', () => {
  it('TC-MP-014 显示昵称与 identities.labels；加载待办与公开决议', async () => {
    respondWith({
      'GET /me': ME(['户主', '业委会委员']),
      'GET /approval/tasks': { results: [{ instance_id: 3, scope: 'EXPENSE', subject_title: '报销#1' }] },
      'GET /resolutions': { results: [{ id: 1, title: '加装电梯决议', status: 'APPROVED' }] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('你好，张三')
    expect(text).toContain('身份：户主、业委会委员')
    expect(text).toContain('报销#1')
    expect(text).toContain('加装电梯决议')
    expect(requests().find((r) => r.path === '/resolutions').data).toEqual({ scope: 'public' })
  })

  it('TC-MP-015 游客：身份显示“游客”；待办接口 403 时按空处理，不抛错', async () => {
    uni.request.mockImplementation(({ url, success }) => {
      const path = url.replace('/api/v1', '')
      if (path === '/me') return success({ statusCode: 200, data: ME(['游客']) })
      if (path === '/approval/tasks') return success({ statusCode: 403, data: { code: 'FORBIDDEN', message: 'x' } })
      return success({ statusCode: 200, data: { results: [] } })
    })
    const { wrapper } = await mountPage(Index)
    expect(wrapper.text()).toContain('身份：游客')
    expect(wrapper.text()).toContain('暂无审批待办')
  })

  it('TC-MP-016 审批待办“同意”：POST /approval/instances/{id}/decision { action: APPROVE }', async () => {
    respondWith({
      'GET /me': ME(['户主']),
      'GET /approval/tasks': { results: [{ instance_id: 3, scope: 'EXPENSE', subject_title: '报销#1' }] },
      'GET /resolutions': { results: [] },
      'POST /approval/instances/3/decision': {}
    })
    const { wrapper } = await mountPage(Index)
    await byText(wrapper, 'button', '同意').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.method === 'POST')
    expect(post).toMatchObject({ path: '/approval/instances/3/decision', data: { action: 'APPROVE' } })
  })
})

describe('报销与核销表单（CR-013）', () => {
  const routes = {
    'GET /me': ME(['户主', '业委会委员']),
    'GET /approval/flows': { results: [{ id: 7, name: '报销流程' }] },
    'POST /attachments': {}
  }
  const claimsList = (data) => ({
    results: data?.type === 'ADVANCE'
      ? [{ id: 11, type: 'ADVANCE', amount: '1000.00', reason: '活动备用金', status: 'APPROVED', settlement_id: null }]
      : data?.type === 'REIMBURSEMENT'
        ? [{ id: 12, type: 'REIMBURSEMENT', amount: '1200.00', reason: '购物', status: 'APPROVED', settlement_id: null }]
        : []
  })

  it('TC-MP-017 onShow 拉取 scope=mine 列表与 EXPENSE 审批流程', async () => {
    respondWith({ ...routes, 'GET /claims': claimsList })
    const { wrapper } = await mountPage(Claims)
    const gets = requests().filter((r) => r.method === 'GET')
    expect(gets.find((r) => r.path === '/approval/flows').data).toEqual({ scope: 'EXPENSE' })
    expect(gets.filter((r) => r.path === '/claims').map((r) => r.data)).toEqual([
      { scope: 'mine' },
      { scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 },
      { scope: 'mine', type: 'REIMBURSEMENT', status: 'APPROVED', page_size: 100 }
    ])
    expect(wrapper.text()).toContain('报销 / 备用金')
  })

  it('TC-MP-018 报销提交：选发票(uni.chooseImage+uploadFile) → POST /claims/reimbursements 带全部必填字段', async () => {
    respondWith({ ...routes, 'GET /claims': claimsList, 'POST /claims/reimbursements': { id: 1 } })
    uni.chooseImage.mockImplementation(({ success }) => success({ tempFilePaths: ['/tmp/inv.png'] }))
    uni.uploadFile.mockImplementation(({ success }) => success({ statusCode: 201, data: '{"id":"att-1"}' }))
    const { wrapper } = await mountPage(Claims)
    await byText(wrapper, 'button', '上传发票').trigger('click')
    await flushPromises()
    expect(uni.uploadFile.mock.calls[0][0]).toMatchObject({ formData: { purpose: 'INVOICE' } })
    wrapper.vm.amount = '300.50'
    wrapper.vm.reason = '购买灯泡'
    wrapper.vm.occurredOn = '2026-11-01'
    wrapper.vm.pickFlow({ detail: { value: 0 } })
    await byText(wrapper, 'button', '提交').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.path === '/claims/reimbursements')
    expect(post.data).toEqual({
      amount: '300.50', reason: '购买灯泡', occurred_on: '2026-11-01',
      invoice_ids: ['att-1'], approval_flow_id: 7
    })
  })

  it('TC-MP-019 未选审批流程时不发请求并提示', async () => {
    respondWith({ ...routes, 'GET /claims': claimsList })
    const { wrapper } = await mountPage(Claims)
    wrapper.vm.amount = '1.00'
    await wrapper.vm.create()
    expect(requests().some((r) => r.method === 'POST')).toBe(false)
    expect(uni.showToast).toHaveBeenCalledWith({ title: '请选择审批流程', icon: 'none' })
  })

  it('TC-MP-020 备用金预借：POST /claims/advances 带 expected_usage / expected_settle_on', async () => {
    respondWith({ ...routes, 'GET /claims': claimsList, 'POST /claims/advances': { id: 2 } })
    const { wrapper } = await mountPage(Claims)
    wrapper.vm.pickType({ detail: { value: 1 } })
    wrapper.vm.pickFlow({ detail: { value: 0 } })
    wrapper.vm.amount = '1000.00'
    wrapper.vm.reason = '活动'
    wrapper.vm.expectedUsage = '小区活动'
    wrapper.vm.expectedSettleOn = '2026-12-01'
    await wrapper.vm.create()
    expect(requests().find((r) => r.path === '/claims/advances').data).toEqual({
      amount: '1000.00', reason: '活动', expected_usage: '小区活动',
      expected_settle_on: '2026-12-01', approval_flow_id: 7
    })
  })

  it('TC-MP-021 核销：差额“少补 ¥200.00”，POST /claims/settlements { advance_id, reimbursement_ids, reason, approval_flow_id }', async () => {
    respondWith({ ...routes, 'GET /claims': claimsList, 'POST /claims/settlements': { id: 3 } })
    const { wrapper } = await mountPage(Claims)
    wrapper.vm.pickFlow({ detail: { value: 0 } })
    wrapper.vm.settle.advanceIndex = 0
    wrapper.vm.settle.reimbursementIds = [12]
    wrapper.vm.settle.reason = '活动核销'
    expect(wrapper.vm.diffText).toBe('少补 ¥200.00')
    await wrapper.vm.submitSettle()
    expect(requests().find((r) => r.path === '/claims/settlements').data).toEqual({
      advance_id: 11, reimbursement_ids: [12], reason: '活动核销', approval_flow_id: 7
    })
  })
})

describe('投票提交（CR-014）', () => {
  const POLL = {
    id: 5, title: '加装电梯调查', description: 'd', status: 'OPEN', deadline: '2026-12-01', can_respond: true,
    questions: [
      { id: 1, title: '单选题', qtype: 'SINGLE', required: true, options: ['甲', '乙'] },
      { id: 2, title: '表态题', qtype: 'AGREE_OPPOSE_ABSTAIN', required: true, options: [] },
      { id: 3, title: '多选题', qtype: 'MULTI', required: false, options: ['a', 'b'] },
      { id: 4, title: '打分题', qtype: 'SCORE', required: false, options: [] }
    ]
  }

  it('TC-MP-022 onLoad 取 id 拉详情；作答后 POST /polls/5/responses，体为 {answers:[{question_id,value}]}', async () => {
    respondWith({ 'GET /polls/5': POLL, 'POST /polls/5/responses': {} })
    const { wrapper } = await mountPage(PollDetail, { query: { id: '5' } })
    expect(wrapper.text()).toContain('加装电梯调查')
    expect(wrapper.text()).toContain('单选题（必答）')
    wrapper.vm.choose(1, '甲')
    wrapper.vm.choose(2, 'AGREE')
    wrapper.vm.choose(3, ['a', 'b'])
    wrapper.vm.choose(4, '5')
    await flushPromises()
    await byText(wrapper, 'button', '提交').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.method === 'POST')
    expect(post.path).toBe('/polls/5/responses')
    expect(post.data).toEqual({ answers: [
      { question_id: 1, value: '甲' }, { question_id: 2, value: 'AGREE' },
      { question_id: 3, value: ['a', 'b'] }, { question_id: 4, value: '5' }
    ] })
  })

  it('TC-MP-023 已作答隐藏提交按钮；截止后“查看结果”展示选项占比', async () => {
    respondWith({
      'GET /polls/5': { ...POLL, status: 'CLOSED', can_respond: false, my_response: [{ question_id: 1, value: '甲' }] },
      'GET /polls/5/result': { results: { responses: 1, participants: 3, questions: [
        { id: 1, title: '单选题', options: [{ value: '甲', count: 1, percentage: 100.0 }] }] } }
    })
    const { wrapper } = await mountPage(PollDetail, { query: { id: '5' } })
    expect(wrapper.text()).toContain('你已提交')
    expect(byText(wrapper, 'button', '提交')?.text()).not.toBe('提交')
    await byText(wrapper, 'button', '查看结果').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('甲：1（100%）')
  })
})

describe('绑定 / 换绑手机号（CR-019）', () => {
  it('TC-MP-024 无手机号：显示绑定表单；发码用途 BIND_PHONE；绑定未合并不换令牌', async () => {
    respondWith({
      'GET /me': ME(['游客'], null),
      'POST /me/codes': {}, 'POST /me/phone/bind': { merged: false, phone: '139****0000' }
    })
    const { wrapper } = await mountPage(Phone)
    expect(wrapper.text()).toContain('绑定手机号')
    expect(wrapper.text()).not.toContain('更换手机号')
    wrapper.vm.phone = '13900000000'
    wrapper.vm.code = '123456'
    await wrapper.vm.sendCode('BIND_PHONE', wrapper.vm.phone)
    await wrapper.vm.bind()
    const posts = requests().filter((r) => r.method === 'POST')
    expect(posts[0]).toMatchObject({ path: '/me/codes', data: { purpose: 'BIND_PHONE', target: '13900000000' } })
    expect(posts[1]).toMatchObject({ path: '/me/phone/bind', data: { phone: '13900000000', code: '123456' } })
    expect(uni.getStorageSync('ocap_token')).toBe('tok')
  })

  it('TC-MP-025 已有手机号：显示更换表单；POST /me/phone/change；合并后换用返回的新令牌', async () => {
    respondWith({
      'GET /me': ME(['户主']),
      'POST /me/phone/change': { merged: true, token: 'MERGED', user: { id: 2 } }
    })
    const { wrapper } = await mountPage(Phone)
    expect(wrapper.text()).toContain('更换手机号')
    Object.assign(wrapper.vm, { oldPhone: '13800000000', newPhone: '13900000000', oldCode: '111111', newCode: '222222' })
    await wrapper.vm.change()
    await flushPromises()
    expect(requests().find((r) => r.path === '/me/phone/change').data).toEqual({
      old_phone: '13800000000', new_phone: '13900000000', old_code: '111111', new_code: '222222' })
    expect(uni.getStorageSync('ocap_token')).toBe('MERGED')
    expect(useAuthStore().token).toBe('MERGED')
  })
})

describe('登录（CR-020）', () => {
  it('TC-MP-026 密码登录：POST /auth/login/password；is_new 为 false 进首页', async () => {
    respondWith({
      'POST /auth/login/password': { token: 'T', user: { id: 1 }, is_new: false },
      'GET /me': ME(['户主'])
    })
    const { wrapper } = await mountPage(Login, { token: '' })
    wrapper.vm.mode = 'password'
    await flushPromises()
    wrapper.vm.identifier = 'acc'
    wrapper.vm.password = 'pw'
    await wrapper.vm.loginPassword()
    expect(requests()[0]).toMatchObject({ path: '/auth/login/password', data: { identifier: 'acc', password: 'pw' } })
    expect(uni.getStorageSync('ocap_token')).toBe('T')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/index/index' })
  })

  it('TC-MP-027 验证码登录：登录响应 is_new=true 进入头像昵称设置页', async () => {
    respondWith({
      'POST /auth/login/code': { token: 'T2', user: { id: 2 }, is_new: true },
      'GET /me': ME(['游客'])
    })
    const { wrapper } = await mountPage(Login, { token: '' })
    wrapper.vm.phone = '13800000001'
    wrapper.vm.code = '123456'
    await wrapper.vm.loginCode()
    expect(requests()[0]).toMatchObject({ path: '/auth/login/code', data: { phone: '13800000001', code: '123456' } })
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/profile-setup/index' })
  })
})
