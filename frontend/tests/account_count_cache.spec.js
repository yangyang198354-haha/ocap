import { beforeEach, expect, it, vi } from 'vitest'
import { readAccountCount, writeAccountCount } from '@/shared/accountCountCache'

beforeEach(() => { localStorage.clear(); vi.restoreAllMocks() })

it('缓存数量五分钟有效，读取不延长 TTL，零账户也是有效结果', () => {
  const now = vi.spyOn(Date, 'now').mockReturnValue(1000000)
  expect(readAccountCount()).toBeNull()
  writeAccountCount(0)
  now.mockReturnValue(1299999)
  expect(readAccountCount()).toBe(0)
  now.mockReturnValue(1300000)
  expect(readAccountCount()).toBeNull()
})

it('损坏、非法数量或不可用的存储降级为默认骨架', () => {
  for (const value of ['{', '{}', JSON.stringify({ count: -1, savedAt: Date.now() }), JSON.stringify({ count: 1.5, savedAt: Date.now() })]) {
    localStorage.setItem('ocap_account_count_v1', value)
    expect(readAccountCount()).toBeNull()
  }
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('full') })
  expect(readAccountCount()).toBeNull()
  expect(() => writeAccountCount(2)).not.toThrow()
})
