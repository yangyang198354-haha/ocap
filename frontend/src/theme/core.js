// MOD-069 / IFC-252：用户端与管理端风格 store 共用的注册表与设备记忆工具。
import { DEFAULT_THEME, THEMES } from './generated/registry'

export const KEY_RE = /^[a-z][a-z0-9_-]{1,31}$/
export const sortedThemes = [...THEMES].sort((a, b) => a.order - b.order)

export function findTheme(key) {
  return sortedThemes.find((theme) => theme.key === key)
}

// 不在注册表（含已下线）→ 回退默认风格（REQ-FUNC-081 / REQ-FUNC-131）
export function resolveKey(key) {
  return typeof key === 'string' && KEY_RE.test(key) && findTheme(key) ? key : DEFAULT_THEME
}

export function readDevice(deviceKey) {
  try { return localStorage.getItem(deviceKey) } catch (e) { return null }
}

export function writeDevice(deviceKey, key) {
  try { localStorage.setItem(deviceKey, key) } catch (e) { /* 存储不可用时忽略 */ }
}
