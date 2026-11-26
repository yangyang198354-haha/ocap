// 身份渲染缓存：刷新/直链时先用上次身份与任务计数渲染最终布局，再后台用 /me + 计数校准
// 仅用于布局与展示，任何权限仍以后端 401/403 为准
const KEY = 'ocap_identity_cache_v1'
const TTL = 5 * 60 * 1000

function readRaw() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    return null
  }
}

export function readIdentityCache() {
  const cached = readRaw()
  if (!cached?.me?.identities) return null
  if (Date.now() - Number(cached.savedAt || 0) > TTL) return null
  return cached
}

export function writeIdentityCache(me, counts) {
  if (!me?.identities) return
  try {
    const prev = readRaw()
    localStorage.setItem(KEY, JSON.stringify({
      savedAt: Date.now(),
      me,
      counts: counts || prev?.counts || null
    }))
  } catch (e) {
    /* 隐私模式或配额不足时静默降级为每次加载骨架 */
  }
}

export function clearIdentityCache() {
  try {
    localStorage.removeItem(KEY)
  } catch (e) {
    /* ignore */
  }
}
