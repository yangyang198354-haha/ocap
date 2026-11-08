// vitest 全局 uni 桩：仅模拟页面脚本与 utils 用到的 API，不模拟 uni 运行时与微信真机行为。
import { beforeEach, vi } from 'vitest'
import { resetLifecycle } from './stubs/uni-app.js'

const storage = new Map()

globalThis.uni = {
  getStorageSync: (key) => storage.get(key) || '',
  setStorageSync: (key, value) => storage.set(key, value),
  removeStorageSync: (key) => storage.delete(key),
  request: vi.fn(),
  uploadFile: vi.fn(),
  chooseImage: vi.fn(),
  reLaunch: vi.fn(),
  navigateTo: vi.fn(),
  switchTab: vi.fn(),
  navigateBack: vi.fn(),
  login: vi.fn(),
  showToast: vi.fn()
}

beforeEach(() => {
  storage.clear()
  resetLifecycle()
  for (const fn of Object.values(globalThis.uni)) {
    if (typeof fn?.mockReset === 'function') fn.mockReset()
  }
})
