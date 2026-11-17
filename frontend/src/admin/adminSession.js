// MOD-125 / IFC-326：管理员账号名的本机缓存（管理端没有"当前管理员"接口，C-64、ADR-117）。
import { getToken } from '@/shared/http'

export const ADMIN_NAME_KEY = 'ocap_admin_name'

// 仅接受 trim 后 1~64 字符的字符串；存储不可用时静默
export function saveAdminName(name) {
  if (typeof name !== 'string') return
  const value = name.trim()
  if (!value || [...value].length > 64) return
  try { localStorage.setItem(ADMIN_NAME_KEY, value) } catch (e) { /* 存储不可用时忽略 */ }
}

// 管理端令牌为空（如 401 被清除）时不显示陈旧账号名
export function readAdminName() {
  if (!getToken(true)) return ''
  try { return localStorage.getItem(ADMIN_NAME_KEY) || '' } catch (e) { return '' }
}

export function clearAdminName() {
  try { localStorage.removeItem(ADMIN_NAME_KEY) } catch (e) { /* 存储不可用时忽略 */ }
}
