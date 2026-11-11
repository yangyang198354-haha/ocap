// MOD-069/IFC-253：管理端风格 store（US-139~US-141、US-143）。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { ADMIN_DEVICE_KEY, useAdminThemeStore } from '@/theme/adminStore'
import { useThemeStore } from '@/theme/store'

const { adminHttp } = mocked
const html = () => document.documentElement

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  html().removeAttribute('data-theme')
  html().removeAttribute('data-surface')
  html().classList.remove('dark')
  setActivePinia(createPinia())
})

describe('TC-UNIT-501 管理端设备记忆与默认值（AC-140-01、AC-141-05）', () => {
  it('无记忆 → bento，data-surface=admin', () => {
    const store = useAdminThemeStore()
    store.initFromDevice()
    expect(store.current).toBe('bento')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(html().getAttribute('data-surface')).toBe('admin')
  })

  it('读取 ocap_admin_theme，不受 ocap_theme 影响', () => {
    localStorage.setItem('ocap_theme', 'terminal')
    localStorage.setItem(ADMIN_DEVICE_KEY, 'neon')
    const store = useAdminThemeStore()
    store.initFromDevice()
    expect(store.current).toBe('neon')
    expect(html().getAttribute('data-theme')).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
  })

  it('已下线/非法 key → bento', () => {
    localStorage.setItem(ADMIN_DEVICE_KEY, 'retired-d')
    const store = useAdminThemeStore()
    store.initFromDevice()
    expect(store.current).toBe('bento')
  })
})

describe('TC-UNIT-502 账号偏好对账（AC-140-02/03、AC-141-01/04）', () => {
  it('账号值权威：设备 neon、账号 terminal → terminal 并写设备记忆', async () => {
    localStorage.setItem(ADMIN_DEVICE_KEY, 'neon')
    adminHttp.get.mockResolvedValueOnce({ theme: 'terminal' })
    const store = useAdminThemeStore()
    store.initFromDevice()
    await store.reconcile()
    expect(store.current).toBe('terminal')
    expect(store.reconciled).toBe(true)
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('terminal')
  })

  it('账号值为 null → bento 并覆盖设备记忆', async () => {
    localStorage.setItem(ADMIN_DEVICE_KEY, 'terminal')
    adminHttp.get.mockResolvedValueOnce({ theme: null })
    const store = useAdminThemeStore()
    store.initFromDevice()
    await store.reconcile()
    expect(store.current).toBe('bento')
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('bento')
  })

  it('账号值是已下线 key → bento，页面可用', async () => {
    adminHttp.get.mockResolvedValueOnce({ theme: 'retired-d' })
    const store = useAdminThemeStore()
    store.initFromDevice()
    await store.reconcile()
    expect(store.current).toBe('bento')
  })

  it('读取失败 → 保持当前与设备记忆，不清空', async () => {
    localStorage.setItem(ADMIN_DEVICE_KEY, 'terminal')
    adminHttp.get.mockRejectedValueOnce(new Error('timeout'))
    const store = useAdminThemeStore()
    store.initFromDevice()
    await store.reconcile()
    expect(store.current).toBe('terminal')
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('terminal')
    expect(store.reconciled).toBe(false)
  })
})

describe('TC-UNIT-503 顶栏选择（AC-139-02/04、AC-141-03）', () => {
  it('乐观应用 + PUT /admin/me/theme，并写设备记忆', async () => {
    adminHttp.put.mockResolvedValueOnce({ theme: 'terminal' })
    const store = useAdminThemeStore()
    store.initFromDevice()
    const pending = store.select('terminal')
    expect(html().getAttribute('data-theme')).toBe('terminal')
    await pending
    expect(adminHttp.put).toHaveBeenCalledWith('/admin/me/theme', { theme: 'terminal' })
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('terminal')
  })

  it('保存失败回滚并抛出', async () => {
    adminHttp.put.mockRejectedValueOnce(new Error('offline'))
    const store = useAdminThemeStore()
    store.initFromDevice()
    await expect(store.select('neon')).rejects.toThrow()
    expect(store.current).toBe('bento')
    expect(html().getAttribute('data-theme')).toBe('bento')
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('bento')
  })

  it('未知风格被拒绝且不发请求', async () => {
    const store = useAdminThemeStore()
    await expect(store.select('retired-d')).rejects.toThrow()
    expect(adminHttp.put).not.toHaveBeenCalled()
  })

  it('登出只重置对账状态，保留设备记忆（AC-141-05）', () => {
    localStorage.setItem(ADMIN_DEVICE_KEY, 'terminal')
    const store = useAdminThemeStore()
    store.initFromDevice()
    store.reconciled = true
    store.resetSession()
    expect(store.reconciled).toBe(false)
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('terminal')
  })
})

describe('TC-UNIT-504 与用户端 store 互相独立（AC-143-01/02/03）', () => {
  it('管理端选择不改写用户端记忆或用户端 store', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    const userStore = useThemeStore()
    userStore.initFromDevice()
    adminHttp.put.mockResolvedValueOnce({ theme: 'neon' })
    const adminStore = useAdminThemeStore()
    adminStore.initFromDevice()
    await adminStore.select('neon')
    expect(userStore.current).toBe('terminal')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    expect(localStorage.getItem(ADMIN_DEVICE_KEY)).toBe('neon')
  })
})
