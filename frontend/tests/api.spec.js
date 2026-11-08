// TC-WEB-006~：shared/api.js 的路径、方法与参数（mock HTTP 层 `@/shared/http`，api.js 为真实实现）
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import * as api from '@/shared/api'

const { http, adminHttp } = mocked

beforeEach(() => {
  vi.clearAllMocks()
  for (const client of [http, adminHttp]) {
    for (const fn of Object.values(client)) fn.mockResolvedValue({})
  }
})

describe('api.js 路径与参数（critical path）', () => {
  it('TC-WEB-006 报销 / 预借 / 核销走 /claims/reimbursements|advances|settlements（CR-013）', async () => {
    const body = { amount: '1.00' }
    await api.claimApi.createReimbursement(body)
    await api.claimApi.createAdvance(body)
    await api.claimApi.createSettlement(body)
    expect(http.post.mock.calls).toEqual([
      ['/claims/reimbursements', body],
      ['/claims/advances', body],
      ['/claims/settlements', body]
    ])
  })

  it('TC-WEB-007 报销列表 GET /claims 带 scope/type/status 查询参数；撤回 POST /claims/{id}/withdraw', async () => {
    await api.claimApi.list({ scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 })
    expect(http.get).toHaveBeenCalledWith('/claims', {
      params: { scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 }
    })
    await api.claimApi.withdraw(9)
    expect(http.post).toHaveBeenCalledWith('/claims/9/withdraw', {})
  })

  it('TC-WEB-008 投票作答 POST /polls/{id}/responses，体为 { answers: [{question_id, value}] }（CR-014）', async () => {
    const answers = [{ question_id: 1, value: '甲' }, { question_id: 2, value: ['a', 'b'] }]
    await api.pollApi.respond(5, answers)
    expect(http.post).toHaveBeenCalledWith('/polls/5/responses', { answers })
    await api.pollApi.result(5)
    expect(http.get).toHaveBeenCalledWith('/polls/5/result', { params: undefined })
  })

  it('TC-WEB-009 创建投票 POST /polls；决议表决 POST /resolutions/{id}/votes { choice }', async () => {
    const body = { kind: 'SURVEY', survey_scope: 'OWNERS_ONLY', title: 't', deadline: 'x', questions: [] }
    await api.pollApi.create(body)
    expect(http.post).toHaveBeenCalledWith('/polls', body)
    await api.resolutionApi.vote(3, 'AGREE')
    expect(http.post).toHaveBeenCalledWith('/resolutions/3/votes', { choice: 'AGREE' })
  })

  it('TC-WEB-010 绑定 / 换绑手机号字段名（US-012、US-014）', async () => {
    await api.meApi.bindPhone('13800000001', '123456')
    expect(http.post).toHaveBeenLastCalledWith('/me/phone/bind', { phone: '13800000001', code: '123456' })
    await api.meApi.changePhone('13800000001', '13800000002', '111111', '222222')
    expect(http.post).toHaveBeenLastCalledWith('/me/phone/change', {
      old_phone: '13800000001', new_phone: '13800000002', old_code: '111111', new_code: '222222'
    })
    await api.meApi.cancelAccount('13800000001', '333333')
    expect(http.post).toHaveBeenLastCalledWith('/me/cancel', { phone: '13800000001', code: '333333' })
  })

  it('TC-WEB-011 改密为 PUT /me/password；验证码 POST /me/codes 带 purpose 与可选 target', async () => {
    const data = { password: 'Aa123456', password_confirm: 'Aa123456' }
    await api.meApi.setPassword(data)
    expect(http.put).toHaveBeenCalledWith('/me/password', data)
    await api.meApi.sendCode('CANCEL')
    expect(http.post).toHaveBeenLastCalledWith('/me/codes', { purpose: 'CANCEL' })
    await api.meApi.sendCode('BIND_PHONE', '13800000001')
    expect(http.post).toHaveBeenLastCalledWith('/me/codes', { purpose: 'BIND_PHONE', target: '13800000001' })
  })

  it('TC-WEB-012 收入表：逐条录入 POST /admin/income/sheets；普通列表 GET /income/sheets；提交带 approval_flow_id（CR-016）', async () => {
    const body = { records: [{ occurred_on: '2026-06-01', amount: '1.00', category: 'c', source_note: 's', remark: '' }], voucher_ids: [] }
    await api.incomeApi.create(body)
    expect(http.post).toHaveBeenCalledWith('/admin/income/sheets', body)
    await api.incomeApi.submit(4, 7)
    expect(http.post).toHaveBeenLastCalledWith('/admin/income/sheets/4/submit', { approval_flow_id: 7 })
    await api.incomeApi.list({ status: 'EFFECTIVE' })
    expect(http.get).toHaveBeenLastCalledWith('/income/sheets', { params: { status: 'EFFECTIVE' } })
  })

  it('TC-WEB-013 管理端撤销认证 POST /admin/memberships/revoke { user_id, unit_id }，走管理员客户端（CR-015）', async () => {
    await api.admin.revokeMembership(11, 22)
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/memberships/revoke', { user_id: 11, unit_id: 22 })
    await api.admin.updateFlow(3, { is_active: false })
    expect(adminHttp.put).toHaveBeenCalledWith('/admin/approval/flows/3', { is_active: false })
    await api.admin.updateSeat(5, { position: 'CHAIR' })
    expect(adminHttp.patch).toHaveBeenCalledWith('/admin/committee/seats/5', { position: 'CHAIR' })
  })

  it('TC-WEB-014 附件上传 POST /attachments，multipart 含 file 与 purpose', async () => {
    const file = new File(['x'], 'inv.pdf', { type: 'application/pdf' })
    await api.attachmentApi.upload(file, 'INVOICE')
    const [path, body] = http.post.mock.calls[0]
    expect(path).toBe('/attachments')
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('purpose')).toBe('INVOICE')
    expect(body.get('file').name).toBe('inv.pdf')
  })

  it('TC-WEB-015 申诉 POST /appeals 体含 proof_ids；登录 POST /auth/login/password 体字段', async () => {
    await api.unitApi.createAppeal({ unit_id: 1, proof_ids: ['u'] })
    expect(http.post).toHaveBeenLastCalledWith('/appeals', { unit_id: 1, proof_ids: ['u'] })
    await api.authApi.loginByPassword('acc', 'pw', true)
    expect(http.post).toHaveBeenLastCalledWith('/auth/login/password', { identifier: 'acc', password: 'pw', remember_me: true })
  })
})

describe('api.js 全量调用健全性', () => {
  const groups = Object.entries(api).filter(([, v]) => v && typeof v === 'object')

  it('TC-WEB-016 每个 api 函数恰好发出 1 次 HTTP 调用，路径以 / 开头且不含 undefined / [object', async () => {
    const urls = []
    for (const [groupName, group] of groups) {
      for (const [name, fn] of Object.entries(group)) {
        vi.clearAllMocks()
        const args = Array(fn.length).fill(1)
        if (['upload', 'importFile', 'importRegistry'].includes(name)) args[0] = new File(['x'], 'a.csv')
        await fn(...args)
        const calls = [http, adminHttp].flatMap((c) => Object.values(c).flatMap((m) => m.mock.calls))
        expect(calls.length, `${groupName}.${name}`).toBe(1)
        const url = calls[0][0]
        expect(url, `${groupName}.${name}`).toMatch(/^\/[a-z]/)
        expect(url, `${groupName}.${name}`).not.toMatch(/undefined|\[object|\$\{/)
        urls.push(url)
      }
    }
    expect(urls.length).toBeGreaterThanOrEqual(80)
  })
})
