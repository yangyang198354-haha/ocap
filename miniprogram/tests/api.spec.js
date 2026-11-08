// TC-MP-001~：utils/api.js、utils/http.js 的路径与参数（真实 api.js/http.js，仅桩 uni.request / uni.uploadFile）
import { describe, expect, it } from 'vitest'
import { api, getToken, setToken } from '@/utils/api'
import { respondWith, requests } from './helpers.js'

const lastRequest = () => requests().at(-1)

describe('utils/http + api', () => {
  it('TC-MP-001 请求拼接 /api/v1 前缀，带 Bearer 令牌与 JSON 头', async () => {
    respondWith({ 'GET /me': { profile: {}, identities: {} } })
    setToken('abc')
    await api.me()
    const req = uni.request.mock.calls[0][0]
    expect(req.url).toBe('/api/v1/me')
    expect(req.method).toBe('GET')
    expect(req.header.Authorization).toBe('Bearer abc')
    expect(req.header['content-type']).toBe('application/json')
  })

  it('TC-MP-002 无令牌时不带 Authorization；setToken("") 清除存储', async () => {
    respondWith({ 'GET /me': {} })
    await api.me()
    expect(uni.request.mock.calls[0][0].header.Authorization).toBeUndefined()
    setToken('x')
    expect(getToken()).toBe('x')
    setToken('')
    expect(getToken()).toBe('')
  })

  it('TC-MP-003 报销 / 预借 / 核销走 /claims/reimbursements|advances|settlements（CR-013）', async () => {
    respondWith({
      'POST /claims/reimbursements': {}, 'POST /claims/advances': {}, 'POST /claims/settlements': {}
    })
    const body = { amount: '1.00' }
    await api.createReimbursement(body)
    await api.createAdvance(body)
    await api.createSettlement(body)
    expect(requests().map((r) => [r.method, r.path, r.data])).toEqual([
      ['POST', '/claims/reimbursements', body],
      ['POST', '/claims/advances', body],
      ['POST', '/claims/settlements', body]
    ])
  })

  it('TC-MP-004 报销列表 GET /claims，查询参数经 data 传递；撤回 POST /claims/{id}/withdraw', async () => {
    respondWith({ 'GET /claims': { results: [] }, 'POST /claims/7/withdraw': {} })
    await api.claims({ scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 })
    expect(lastRequest()).toMatchObject({ method: 'GET', path: '/claims',
      data: { scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 } })
    await api.withdrawClaim(7)
    expect(lastRequest()).toMatchObject({ method: 'POST', path: '/claims/7/withdraw', data: {} })
  })

  it('TC-MP-005 投票作答 POST /polls/{id}/responses，体为 { answers }（CR-014）', async () => {
    respondWith({ 'POST /polls/5/responses': {}, 'GET /polls/5/result': {} })
    const answers = [{ question_id: 1, value: '甲' }, { question_id: 3, value: ['a'] }]
    await api.respond(5, answers)
    expect(lastRequest()).toMatchObject({ method: 'POST', path: '/polls/5/responses', data: { answers } })
    await api.pollResult(5)
    expect(lastRequest().path).toBe('/polls/5/result')
  })

  it('TC-MP-006 绑定 / 换绑手机号字段名与验证码用途', async () => {
    respondWith({ 'POST /me/phone/bind': {}, 'POST /me/phone/change': {}, 'POST /me/codes': {} })
    await api.bindPhone('13800000001', '123456')
    expect(lastRequest().data).toEqual({ phone: '13800000001', code: '123456' })
    await api.changePhone('13800000001', '13800000002', '111111', '222222')
    expect(lastRequest()).toMatchObject({ path: '/me/phone/change', data: {
      old_phone: '13800000001', new_phone: '13800000002', old_code: '111111', new_code: '222222' } })
    await api.sendMeCode('BIND_PHONE', '13800000001')
    expect(lastRequest().data).toEqual({ purpose: 'BIND_PHONE', target: '13800000001' })
    await api.sendMeCode('CANCEL')
    expect(lastRequest().data).toEqual({ purpose: 'CANCEL' })
  })

  it('TC-MP-007 登录：验证码 / 密码 / 微信一键登录的路径与字段', async () => {
    respondWith({ 'POST /auth/login/code': {}, 'POST /auth/login/password': {}, 'POST /auth/wechat/miniapp': {} })
    await api.loginByCode('13800000001', '123456')
    expect(lastRequest()).toMatchObject({ path: '/auth/login/code', data: { phone: '13800000001', code: '123456' } })
    await api.loginByPassword('acc', 'pw')
    expect(lastRequest()).toMatchObject({ path: '/auth/login/password', data: { identifier: 'acc', password: 'pw' } })
    await api.loginByWechat('wxcode')
    expect(lastRequest()).toMatchObject({ path: '/auth/wechat/miniapp', data: { code: 'wxcode' } })
  })

  it('TC-MP-008 申诉 POST /appeals 带 proof_ids；认证 POST /certifications { unit_id }', async () => {
    respondWith({ 'POST /appeals': {}, 'POST /certifications': {} })
    await api.createAppeal({ unit_id: 1, proof_ids: ['u'] })
    expect(lastRequest().data).toEqual({ unit_id: 1, proof_ids: ['u'] })
    await api.certify(9)
    expect(lastRequest()).toMatchObject({ path: '/certifications', data: { unit_id: 9 } })
  })

  it('TC-MP-009 上传附件：uni.uploadFile 到 /api/v1/attachments，name=file，formData.purpose', async () => {
    uni.uploadFile.mockImplementation(({ success }) => success({ statusCode: 201, data: '{"id":"att-1"}' }))
    setToken('tk')
    const body = await api.upload('/tmp/a.png', 'INVOICE')
    expect(body).toEqual({ id: 'att-1' })
    expect(uni.uploadFile.mock.calls[0][0]).toMatchObject({
      url: '/api/v1/attachments', filePath: '/tmp/a.png', name: 'file',
      formData: { purpose: 'INVOICE' }, header: { Authorization: 'Bearer tk' } })
  })

  it('TC-MP-010 失败响应：抛出带 code/message 的错误；401 清令牌并跳转登录页', async () => {
    uni.request.mockImplementation(({ success }) =>
      success({ statusCode: 401, data: { code: 'UNAUTHORIZED', message: '请先登录' } }))
    setToken('old')
    await expect(api.me()).rejects.toMatchObject({ code: 'UNAUTHORIZED', message: '请先登录' })
    expect(getToken()).toBe('')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/login/index' })
  })

  it('TC-MP-011 api.js 每个请求类函数发出 1 次请求，路径合法', async () => {
    uni.request.mockImplementation(({ success }) => success({ statusCode: 200, data: {} }))
    const skip = new Set(['upload', 'setToken', 'getToken'])
    const paths = []
    for (const [name, fn] of Object.entries(api)) {
      if (skip.has(name)) continue
      uni.request.mockClear()
      await fn(...Array(fn.length).fill(1))
      expect(uni.request, name).toHaveBeenCalledTimes(1)
      const { url } = uni.request.mock.calls[0][0]
      expect(url, name).toMatch(/^\/api\/v1\/[a-z]/)
      expect(url, name).not.toMatch(/undefined|\[object|\$\{/)
      paths.push(url)
    }
    expect(paths.length).toBeGreaterThanOrEqual(25)
  })
})
