// TC-WEB-031~033：Web 登录页（US-006）挂载与提交（真实 Login.vue + 真实 api.js + 真实 store，仅 mock HTTP 层）
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { ElMessage } from 'element-plus'
import { mountPage } from './helpers.js'
import Login from '@/portal/Login.vue'
import { useAuthStore } from '@/stores/auth'

const { http } = mocked

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  document.body.innerHTML = ''
  // 未配置微信开放平台：登录页挂载时取参数失败，入口隐藏
  http.get.mockRejectedValue(new Error('WECHAT_UNAVAILABLE'))
})

describe('Web 手机号登录（US-006）', () => {
  it('TC-WEB-031 验证码登录：发码 POST /auth/codes {purpose:LOGIN}；POST /auth/login/code {phone,code,remember_me}；保存令牌（AC-006-01）', async () => {
    http.post.mockImplementation(async (url) => {
      if (url === '/auth/codes') return {}
      if (url === '/auth/login/code') return { token: 'WEB-TOKEN', user: { id: 9 }, is_new: false }
      throw new Error(`未预期的请求 ${url}`)
    })
    const { wrapper } = await mountPage(Login)
    wrapper.vm.form.phone = '13800000001'
    await wrapper.vm.sendCode()
    expect(http.post).toHaveBeenCalledWith('/auth/codes', {
      target: '13800000001', purpose: 'LOGIN', target_type: 'PHONE'
    })
    wrapper.vm.form.code = '123456'
    wrapper.vm.form.remember = true
    await wrapper.vm.loginCode()
    await flushPromises()
    expect(http.post).toHaveBeenCalledWith('/auth/login/code', {
      phone: '13800000001', code: '123456', remember_me: true
    })
    expect(useAuthStore().token).toBe('WEB-TOKEN')
    expect(localStorage.getItem('ocap_token')).toBe('WEB-TOKEN')
  })

  it('TC-WEB-032 密码登录：POST /auth/login/password {identifier,password,remember_me}；成功保存令牌（AC-006-02）', async () => {
    http.post.mockResolvedValue({ token: 'PWD-TOKEN', user: { id: 3 }, is_new: false })
    const { wrapper } = await mountPage(Login)
    wrapper.vm.form.identifier = '13800000002'
    wrapper.vm.form.password = 'Ocap2026pass'
    await wrapper.vm.loginPassword()
    await flushPromises()
    expect(http.post).toHaveBeenCalledWith('/auth/login/password', {
      identifier: '13800000002', password: 'Ocap2026pass', remember_me: false
    })
    expect(useAuthStore().token).toBe('PWD-TOKEN')
  })

  it('TC-WEB-033 登录失败：界面提示后端返回的统一文案；锁定时附“N 秒后重试”；不保存令牌（AC-006-03/04）', async () => {
    const spy = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const uniform = '账号或密码错误；若从未设置过密码，请使用验证码登录'
    http.post.mockRejectedValueOnce({ code: 'LOGIN_FAILED', message: uniform })
    const { wrapper } = await mountPage(Login)
    wrapper.vm.form.identifier = '13800000003'
    wrapper.vm.form.password = 'whatever'
    await wrapper.vm.loginPassword()
    await flushPromises()
    expect(spy).toHaveBeenLastCalledWith(uniform)
    http.post.mockRejectedValueOnce({ code: 'LOGIN_LOCKED', message: '登录失败次数过多，请稍后再试', details: { retry_after: 900 } })
    await wrapper.vm.loginPassword()
    await flushPromises()
    expect(spy).toHaveBeenLastCalledWith('登录失败次数过多，请稍后再试（900 秒后重试）')
    expect(useAuthStore().token).toBeFalsy()
    expect(localStorage.getItem('ocap_token')).toBeNull()
    spy.mockRestore()
  })
})
