// MOD-069 / IFC-253：管理端风格 store，与用户端 store 状态、设备键、接口完全分离。
import { defineStore } from 'pinia'
import { admin as adminApi } from '@/shared/api'
import { findTheme, readDevice, resolveKey, sortedThemes, writeDevice } from './core'
import { applyTheme } from './apply'

export const ADMIN_DEVICE_KEY = 'ocap_admin_theme'

export const useAdminThemeStore = defineStore('adminTheme', {
  state: () => ({ current: resolveKey(null), reconciled: false, ready: false }),
  getters: {
    list: () => sortedThemes
  },
  actions: {
    _apply(key) {
      const theme = findTheme(key)
      if (!theme) return
      this.current = key
      applyTheme(key, theme.scheme, 'admin')
    },
    initFromDevice() {
      this._apply(resolveKey(readDevice(ADMIN_DEVICE_KEY)))
      this.ready = true
    },
    enter() {
      if (!this.ready) this.initFromDevice()
      else this._apply(this.current)
    },
    async reconcile() {
      try {
        const data = await adminApi.theme()
        const key = resolveKey(data?.theme)
        this._apply(key)
        writeDevice(ADMIN_DEVICE_KEY, key)
        this.reconciled = true
      } catch (e) {
        /* 读取失败：保持当前风格，不清空设备记忆（AC-140-03） */
      }
    },
    async select(key) {
      if (!findTheme(key)) throw new Error('风格不存在')
      const prev = this.current
      this._apply(key)
      writeDevice(ADMIN_DEVICE_KEY, key)
      try {
        await adminApi.setTheme(key)
      } catch (e) {
        this._apply(prev)
        writeDevice(ADMIN_DEVICE_KEY, prev)
        throw e
      }
    },
    resetSession() {
      this.reconciled = false
    }
  }
})
