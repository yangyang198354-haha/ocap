// TC-WEB-001~005：stores/auth 对 /me 的 identities 对象的读取（US-041、US-036；CR-012）
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { useAuthStore } from '@/stores/auth'

const ME_CHAIR = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: false,
    units: [{ unit_id: 3, specific_part: '1-1-101', role: 'HEAD' }],
    committee: { position: 'CHAIR', term_end: '2027-01-01' },
    labels: ['户主', '业委会主任']
  }
}

describe('stores/auth', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('TC-WEB-001 fetchMe 请求 GET /me，identities 取 labels 数组', async () => {
    localStorage.setItem('ocap_token', 'tok')
    mocked.http.get.mockResolvedValue(ME_CHAIR)
    const auth = useAuthStore()
    await auth.fetchMe()
    expect(mocked.http.get).toHaveBeenCalledWith('/me', { params: undefined })
    expect(auth.identities).toEqual(['户主', '业委会主任'])
    expect(auth.identities.join('、')).toBe('户主、业委会主任')
    expect(auth.position).toBe('CHAIR')
  })

  it.each([
    ['CHAIR', true, true],
    ['VICE_CHAIR', true, true],
    ['MEMBER', true, false],
    ['REPRESENTATIVE', false, false]
  ])('TC-WEB-002 职位 %s：isCommittee=%s isChairOrVice=%s', (position, committee, chair) => {
    const auth = useAuthStore()
    auth.me = { ...ME_CHAIR, identities: { ...ME_CHAIR.identities, committee: { position } } }
    expect(auth.isCommittee).toBe(committee)
    expect(auth.isChairOrVice).toBe(chair)
  })

  it('TC-WEB-003 游客（committee 为 null）：无委员身份，标签为空数组时不抛错', () => {
    const auth = useAuthStore()
    auth.me = { profile: {}, identities: { is_guest: true, units: [], committee: null, labels: ['游客'] } }
    expect(auth.isCommittee).toBe(false)
    expect(auth.identities).toEqual(['游客'])
    auth.me = null
    expect(auth.identities).toEqual([])
    expect(auth.position).toBe('')
  })

  it('TC-WEB-004 旧结构（identities 为中文标签数组）不再被当作对象读取，也不会在渲染时抛 TypeError', () => {
    const auth = useAuthStore()
    auth.me = { profile: {}, identities: ['户主'] }
    expect(auth.identities).toEqual([])
    expect(() => auth.identities.join('、')).not.toThrow()
    expect(auth.isCommittee).toBe(false)
  })

  it('TC-WEB-005 setAuth 持久化令牌；logout 调 POST /auth/logout 并清理', async () => {
    mocked.http.post.mockResolvedValue({})
    const auth = useAuthStore()
    auth.setAuth('NEW', null)
    expect(localStorage.getItem('ocap_token')).toBe('NEW')
    expect(auth.isLogin).toBe(true)
    await auth.logout()
    expect(mocked.http.post).toHaveBeenCalledWith('/auth/logout', {})
    expect(auth.token).toBe('')
    expect(localStorage.getItem('ocap_token')).toBeNull()
  })
})
