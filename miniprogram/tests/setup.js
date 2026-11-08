// vitest 全局 uni mock（沿用 Freeark 小程序测试脚手架思路）
const storage = new Map()

globalThis.uni = {
  getStorageSync: (key) => storage.get(key) || '',
  setStorageSync: (key, value) => storage.set(key, value),
  removeStorageSync: (key) => storage.delete(key),
  request: () => {},
  reLaunch: () => {},
  navigateTo: () => {},
  login: () => {},
  showToast: () => {}
}
