// MOD-025 / IFC-146：Web 风格 store，优先级规则见 ADR-027。
import { defineStore } from 'pinia'
import { meApi } from '@/shared/api'
import { DEFAULT_THEME } from './generated/registry'
import { applyTheme, DEVICE_KEY } from './apply'
import { findTheme, readDevice, resolveKey, sortedThemes, writeDevice as writeDeviceKey } from './core'

const sorted = sortedThemes
const find = findTheme
const readDeviceKey = () => readDevice(DEVICE_KEY)
const writeDevice = (key) => writeDeviceKey(DEVICE_KEY, key)

export const useThemeStore = defineStore('theme', {
  state: () => ({ current: DEFAULT_THEME, reconciled: false, ready: false }),
  getters: {
    list: () => sorted
  },
  actions: {
    _apply(key) {
      this.current = key
      applyTheme(key, find(key).scheme, 'portal')
    },
    initFromDevice() {
      this._apply(resolveKey(readDeviceKey()))
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
    resetSession() {
      this.reconciled = false
    }
  }
})
