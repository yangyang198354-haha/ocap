// MOD-025 / IFC-147：把风格应用到 <html>；detectLowEnd 为启发式（ADR-032）。
export const DEVICE_KEY = 'ocap_theme'

export function applyTheme(key, scheme) {
  const el = document.documentElement
  el.setAttribute('data-theme', key)
  // 深色风格启用 Element Plus 官方 dark 变量（其余映射由 themes.css 覆盖）
  el.classList.toggle('dark', scheme === 'dark')
}

export function detectLowEnd() {
  const nav = typeof navigator === 'undefined' ? {} : navigator
  const low = (nav.deviceMemory !== undefined && nav.deviceMemory <= 4) ||
    (nav.hardwareConcurrency !== undefined && nav.hardwareConcurrency <= 4)
  if (typeof document !== 'undefined') {
    if (low) document.documentElement.setAttribute('data-perf', 'low')
    else document.documentElement.removeAttribute('data-perf')
  }
  return low
}
