// MOD-128 / IFC-327：风格 key → 配图组件；未知或缺失回退 bento（与 DEFAULT_THEME 一致）。
import NeonArt from './NeonArt.vue'
import BentoArt from './BentoArt.vue'
import TerminalArt from './TerminalArt.vue'

const ARTS = { neon: NeonArt, bento: BentoArt, terminal: TerminalArt }

export function artFor(themeKey) {
  // DEF-001：只认自有键，原型链键名（__proto__、constructor 等）一律回退
  return (typeof themeKey === 'string' && Object.hasOwn(ARTS, themeKey) && ARTS[themeKey]) || BentoArt
}
