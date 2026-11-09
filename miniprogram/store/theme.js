// MOD-028 / IFC-151：小程序风格 store，规则与 Web 端相同（ADR-027）。
import { defineStore } from 'pinia'
import { api } from '@/utils/api'
import { DEFAULT_THEME, THEMES } from '@/theme/generated/registry'

export const DEVICE_KEY = 'ocap_theme'
const KEY_RE = /^[a-z][a-z0-9_-]{1,31}$/
const sorted = [...THEMES].sort((a, b) => a.order - b.order)
const find = (key) => sorted.find((t) => t.key === key)
const resolveKey = (key) => (typeof key === 'string' && KEY_RE.test(key) && find(key) ? key : DEFAULT_THEME)

function readDevice() {
  try { return uni.getStorageSync(DEVICE_KEY) } catch (e) { return '' }
}
function writeDevice(key) {
  try { uni.setStorageSync(DEVICE_KEY, key) } catch (e) { /* 存储不可用时忽略 */ }
}

export const useThemeStore = defineStore('theme', {
  // 同步读取设备记忆，首帧即为正确风格（IFC-149）
  state: () => ({ current: resolveKey(readDevice()), reconciled: false }),
  getters: {
    list: () => sorted,
    cssVarsText: (s) => Object.entries(find(s.current).tokens).map(([k, v]) => `${k}:${v}`).join(';')
  },
  actions: {
    initFromDevice() {
      this.current = resolveKey(readDevice())
      this.applyNative(this.current)
    },
    async reconcileAfterLogin() {
      try {
        const data = await api.theme()
        const key = resolveKey(data?.theme)
        this.current = key
        writeDevice(key)
        this.reconciled = true
        this.applyNative(key)
      } catch (e) {
        /* 读取失败：保持当前，不清空设备记忆 */
      }
    },
    async select(key) {
      if (!find(key)) throw new Error('风格不存在')
      const prev = this.current
      this.current = key
      writeDevice(key)
      this.applyNative(key)
      try {
        await api.setTheme(key)
      } catch (e) {
        this.current = prev
        writeDevice(prev)
        this.applyNative(prev)
        throw e
      }
    },
    // 同步原生 tabBar / 导航栏 / 窗口背景；非 tabBar 页调用 setTabBarStyle 会失败，吞掉错误（OQ-T04）
    applyNative(key) {
      const native = find(key)?.native
      if (!native) return
      const quiet = (fn, opts) => {
        try { fn?.({ ...opts, fail() {} }) } catch (e) { /* 平台不支持时忽略 */ }
      }
      quiet(uni.setTabBarStyle, native.tabBar)
      quiet(uni.setNavigationBarColor, native.navBar)
      quiet(uni.setBackgroundColor, { backgroundColor: native.windowBackground })
    }
  }
})
