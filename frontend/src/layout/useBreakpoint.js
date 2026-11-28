// MOD-120 / IFC-320：宽窄屏判断。形态切换以 CSS 媒体查询为主，JS 只用于 /me 重定向与抽屉关闭（ADR-120）。
import { onBeforeUnmount, onMounted, readonly, ref } from 'vue'

export const WIDE_QUERY = '(min-width: 768px)'

// matchMedia 不可用（jsdom）时按窄屏处理
export function isWideNow() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return Boolean(window.matchMedia(WIDE_QUERY).matches)
}

export function useIsWide(media = WIDE_QUERY) {
  const wide = ref(typeof window !== 'undefined' && typeof window.matchMedia === 'function' &&
    window.matchMedia(media).matches)
  let query = null
  const onChange = (event) => {
    wide.value = Boolean(event.matches)
  }
  onMounted(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
    query = window.matchMedia(media)
    wide.value = Boolean(query.matches)
    if (typeof query.addEventListener === 'function') query.addEventListener('change', onChange)
    else if (typeof query.addListener === 'function') query.addListener(onChange)
  })
  onBeforeUnmount(() => {
    if (!query) return
    if (typeof query.removeEventListener === 'function') query.removeEventListener('change', onChange)
    else if (typeof query.removeListener === 'function') query.removeListener(onChange)
  })
  return readonly(wide)
}
