// ocap_brand_layout GROUP_D（MOD-131）：管理员账号名本机缓存 adminSession（IFC-326，ADR-117）。
// 层级：unit（localStorage + 令牌读取，HTTP 层 mock）。TC-UNIT-831 起。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { ADMIN_NAME_KEY, clearAdminName, readAdminName, saveAdminName } from '@/admin/adminSession'

beforeEach(() => localStorage.clear())
afterEach(() => vi.restoreAllMocks())

describe('adminSession', () => {
  it('TC-UNIT-831 / AC-226-01：存储键为 ocap_admin_name；保存后在持有管理端令牌时可读（刷新后仍显示）', () => {
    expect(ADMIN_NAME_KEY).toBe('ocap_admin_name')
    localStorage.setItem('ocap_admin_token', 'atok')
    saveAdminName('admin01')
    expect(localStorage.getItem('ocap_admin_name')).toBe('admin01')
    expect(readAdminName()).toBe('admin01')
  })

  it('TC-UNIT-832 / AC-226-05：没有管理端令牌（如 401 清除）时不显示陈旧账号名；用户端令牌不算', () => {
    saveAdminName('admin01')
    expect(readAdminName()).toBe('')
    localStorage.setItem('ocap_token', 'user-tok')
    expect(readAdminName()).toBe('')
  })

  it('TC-UNIT-833 / AC-226-05：无记录时读到空串（调用方回退"管理员"）', () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    expect(readAdminName()).toBe('')
  })

  it('TC-UNIT-834 / AC-226-04：clearAdminName 清除；再次读取为空', () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    saveAdminName('admin01')
    clearAdminName()
    expect(localStorage.getItem(ADMIN_NAME_KEY)).toBeNull()
    expect(readAdminName()).toBe('')
  })

  it('TC-UNIT-835 / IFC-326 输入校验：非字符串、空串、纯空白被忽略，不覆盖已有值', () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    saveAdminName('keep')
    for (const bad of [undefined, null, 123, {}, [], '', '   ', '\n\t']) saveAdminName(bad)
    expect(readAdminName()).toBe('keep')
  })

  it('TC-UNIT-836 / IFC-326 输入校验：首尾空白被去掉；恰 64 个字符可存，65 个被忽略（按码点计）', () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    saveAdminName('  admin01  ')
    expect(readAdminName()).toBe('admin01')
    saveAdminName('a'.repeat(64))
    expect(readAdminName()).toBe('a'.repeat(64))
    saveAdminName('b'.repeat(65))
    expect(readAdminName()).toBe('a'.repeat(64))
    saveAdminName('😀'.repeat(64))
    expect(readAdminName()).toBe('😀'.repeat(64))
    saveAdminName('😀'.repeat(65))
    expect(readAdminName()).toBe('😀'.repeat(64))
  })

  it('TC-UNIT-837 / IFC-326：存储不可用（setItem/getItem/removeItem 抛错）时静默，不抛异常', () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    const proto = Object.getPrototypeOf(localStorage)
    vi.spyOn(proto, 'setItem').mockImplementation(() => { throw new Error('quota') })
    expect(() => saveAdminName('admin01')).not.toThrow()
    vi.restoreAllMocks()
    localStorage.setItem('ocap_admin_token', 'atok')
    vi.spyOn(proto, 'getItem').mockImplementation((key) => {
      if (key === 'ocap_admin_token') return 'atok'
      throw new Error('denied')
    })
    expect(readAdminName()).toBe('')
    vi.restoreAllMocks()
    vi.spyOn(proto, 'removeItem').mockImplementation(() => { throw new Error('denied') })
    expect(() => clearAdminName()).not.toThrow()
  })
})
