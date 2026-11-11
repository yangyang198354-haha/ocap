// GROUP_D：注册用户目录展示（TC-UNIT-410 ~ 411，US-132 ~ 136）
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import AdminUsers from '@/admin/AdminUsers.vue'
import { formatDateTime } from '@/shared/format'

const { adminHttp } = mocked

beforeAll(() => {
  if (!global.ResizeObserver) {
    global.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
})

beforeEach(() => vi.clearAllMocks())
afterEach(() => { document.body.innerHTML = '' })

describe('注册用户目录展示', () => {
  it('TC-UNIT-410：formatDateTime 输出 YYYY-MM-DD HH:mm，空值为空字符串', () => {
    expect(formatDateTime(null)).toBe('')
    expect(formatDateTime('')).toBe('')
    expect(formatDateTime('2026-11-10T09:05:00+08:00')).toBe('2026-11-10 09:05')
  })

  it('TC-UNIT-411：身份/认证/实名/上次登录四列与空值文案', async () => {
    adminHttp.get.mockImplementation(async (url) => {
      if (url === '/admin/admins') return []
      if (url === '/admin/users') {
        return {
          results: [
            {
              id: 1, account_no: '1000000001', phone: '138****0001', nickname: '甲',
              status: 'ACTIVE', identity_label: '户主', certified_units: 2,
              real_names: ['张三', '李四'], last_login_at: '2026-11-10T09:05:00+08:00'
            },
            {
              id: 2, account_no: '1000000002', phone: null, nickname: '乙',
              status: 'ACTIVE', identity_label: '游客', certified_units: 0,
              real_names: [], last_login_at: null
            }
          ]
        }
      }
      throw new Error(`未预期的 GET ${url}`)
    })

    const wrapper = mount(AdminUsers, { global: { plugins: [ElementPlus] }, attachTo: document.body })
    await flushPromises()
    const text = wrapper.text().replace(/\s+/g, ' ')

    expect(text).toContain('身份')
    expect(text).toContain('户主')
    expect(text).toContain('已认证（2 套）')
    expect(text).toContain('张三、李四')
    expect(text).toContain('2026-11-10 09:05')
    expect(text).toContain('游客')
    expect(text).toContain('未认证')
    expect(text).toContain('—')
    expect(text).toContain('从未登录')
    wrapper.unmount()
  })
})
