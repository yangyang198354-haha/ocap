// MOD-025 / IFC-146：Web 风格 store，优先级规则见 ADR-027。
import { defineStore } from 'pinia'
import { meApi } from '@/shared/api'
import { DEFAULT_THEME, THEMES } from './generated/registry'
import { applyTheme, DEVICE_KEY } from './apply'

const KEY_RE = /^[a-z][a-z0-9_-]{1,31}$/
const sorted = [...THEMES].sort((a, b) => a.order - b.order)
const find = (key) => sorted.find((t) => t.key === key)
// 不在注册表（含已下线）→ 回退默认风格（REQ-FUNC-081）
const resolveKey = (key) => (typeof key === 'string' && KEY_RE.test(key) && find(key) ? key : DEFAULT_THEME)

function readDevice() {
  try { return localStorage.getItem(DEVICE_KEY) } catch (e) { return null }
}
function writeDevice(key) {
  try { localStorage.setItem(DEVICE_KEY, key) } catch (e) { /* 存储不可用时忽略 */ }
}

export const useThemeStore = defineStore('theme', {
  state: () => ({ current: DEFAULT_THEME, reconciled: false, ready: false }),
  getters: {
    list: () => sorted
  },
  actions: {
    _apply(key) {
      this.current = key
      applyTheme(key, find(key).scheme)
    },
    initFromDevice() {
      this._apply(resolveKey(readDevice()))
      this.ready = true
    },
    async reconcileAfterLogin() {
      try {
        const data = await meApi.theme()
        const key = resolveKey(data?.theme)
        this._apply(key)
        writeDevice(key)
        this.reconciled = true
      } catch (e) {
        /* 读取失败：保持当前风格，不清空设备记忆（AC-090-03） */
      }
    },
    async select(key) {
      if (!find(key)) throw new Error('风格不存在')
      const prev = this.current
      this._apply(key)
      writeDevice(key)
      try {
        await meApi.setTheme(key)
      } catch (e) {
        this._apply(prev)
        writeDevice(prev)
        throw e
      }
    },
    forAdminRoute() {
      // 管理端固定 B，不读写设备记忆与账号偏好（REQ-FUNC-076）
      this._apply(DEFAULT_THEME)
    },
    resetSession() {
      this.reconciled = false
    }
  }
})
