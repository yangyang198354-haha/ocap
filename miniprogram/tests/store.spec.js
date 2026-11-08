// TC-MP-012~：store/auth 与 /me 的 identities 对象（US-041；CR-012）
import { describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/store/auth'
import { respondWith } from './helpers.js'

describe('store/auth', () => {
  it('TC-MP-012 fetchMe 取 GET /me，保存 profile 与 identities（对象）', async () => {
    setActivePinia(createPinia())
    const me = { profile: { nickname: '张三' }, identities: { labels: ['户主'], committee: null } }
    respondWith({ 'GET /me': me })
    uni.setStorageSync('ocap_token', 't')
    const auth = useAuthStore()
    expect(await auth.fetchMe()).toEqual(me)
    expect(auth.me.identities.labels).toEqual(['户主'])
  })

  it('TC-MP-013 无令牌不请求；setAuth / clear 同步存储', async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    expect(await auth.fetchMe()).toBeNull()
    expect(uni.request).not.toHaveBeenCalled()
    auth.setAuth('T2', { profile: {} })
    expect(uni.getStorageSync('ocap_token')).toBe('T2')
    auth.clear()
    expect(auth.token).toBe('')
    expect(uni.getStorageSync('ocap_token')).toBe('')
  })
})
