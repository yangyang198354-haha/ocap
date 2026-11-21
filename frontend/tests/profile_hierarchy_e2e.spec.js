// ocap_profile_hierarchy GROUP_D：critical path 替代用例（多步组件旅程）。
import { describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage } from './helpers.js'
import UserProfile from '@/portal/UserProfile.vue'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

describe('critical path（替代）：他人主页 → 本人主页（US-273/274/275/276）', () => {
  it('TC-E2E-1502：两段主页均保持昵称 → 实名+徽章 → 身份，且本人显示编辑入口', async () => {
    http.get.mockResolvedValueOnce({
      id: 9, nickname: '昵称丙', avatar_url: null,
      identity: { code: 'HEAD', label: '产权业主' }, labels: ['产权业主'],
      real_name: '杨扬', signature: '', is_self: false
    })
    const first = await mountPage(UserProfile, { path: '/users/9/profile' })
    await flush()
    const text1 = first.wrapper.text()
    expect(text1.indexOf('昵称丙')).toBeLessThan(text1.indexOf('杨扬'))
    expect(text1.indexOf('杨扬')).toBeLessThan(text1.indexOf('产权业主'))
    expect(first.wrapper.find('.real-name .verified-badge').text()).toContain('已实名认证')

    http.get.mockResolvedValueOnce({
      id: 2, nickname: '胖子熊', avatar_url: null,
      identity: { code: 'HEAD', label: '产权业主' }, labels: ['产权业主'],
      real_name: '杨扬', signature: '签名档', is_self: true
    })
    const second = await mountPage(UserProfile, { path: '/users/2/profile' })
    await flush()
    const text2 = second.wrapper.text()
    expect(text2.indexOf('胖子熊')).toBeLessThan(text2.indexOf('杨扬'))
    expect(text2.indexOf('杨扬')).toBeLessThan(text2.indexOf('产权业主'))
    expect(second.wrapper.find('.real-name .verified-badge').exists()).toBe(true)
    expect(second.wrapper.text()).toContain('编辑资料')
  })
})
