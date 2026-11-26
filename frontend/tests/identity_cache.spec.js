import { beforeEach, describe, expect, it, vi } from 'vitest'
import { clearIdentityCache, readIdentityCache, writeIdentityCache } from '@/shared/identityCache'

const ME = { profile: { id: 1, nickname: '胖子熊' }, identities: { is_guest: false, committee: null, units: [] } }

describe('identityCache', () => {
  beforeEach(() => {
    clearIdentityCache()
    vi.restoreAllMocks()
  })

  it('写入后可读出身份与计数', () => {
    writeIdentityCache(ME, { pendingReview: 1, tasks: 2, votes: 0 })
    const cached = readIdentityCache()
    expect(cached.me.profile.nickname).toBe('胖子熊')
    expect(cached.counts).toEqual({ pendingReview: 1, tasks: 2, votes: 0 })
  })

  it('超过 5 分钟 TTL 后不再读取', () => {
    writeIdentityCache(ME, { pendingReview: 0, tasks: 0, votes: 0 })
    const now = Date.now()
    vi.spyOn(Date, 'now').mockReturnValue(now + 5 * 60 * 1000 + 1)
    expect(readIdentityCache()).toBeNull()
  })

  it('缺少 identities 的登录简版对象不写入', () => {
    writeIdentityCache({ profile: { id: 1 } }, { pendingReview: 0, tasks: 0, votes: 0 })
    expect(readIdentityCache()).toBeNull()
  })

  it('仅刷新身份时保留上次计数字段', () => {
    writeIdentityCache(ME, { pendingReview: 3, tasks: 1, votes: 2 })
    writeIdentityCache({ ...ME, profile: { ...ME.profile, nickname: '新昵称' } })
    const cached = readIdentityCache()
    expect(cached.me.profile.nickname).toBe('新昵称')
    expect(cached.counts.pendingReview).toBe(3)
  })

  it('clear 后读取为空', () => {
    writeIdentityCache(ME, { pendingReview: 1, tasks: 0, votes: 0 })
    clearIdentityCache()
    expect(readIdentityCache()).toBeNull()
  })
})
