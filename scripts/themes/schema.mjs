// MOD-024 / IFC-144：风格定义校验与 WCAG 2.1 对比度计算（仅 Node 内置能力，无第三方依赖）。
export const KEY_RE = /^[a-z][a-z0-9_-]{1,31}$/
const HEX_RE = /^#[0-9a-fA-F]{6}$/

// 全部必填；值类型：hex = '#RRGGBB'；str = 非空字符串；opaque 颜色必须是 hex
export const TOKEN_SPEC = {
  bg: 'hex', surface: 'str', overlay: 'hex', text: 'hex', muted: 'hex', line: 'str',
  accent: 'hex', accent2: 'hex', accentText: 'hex', onAccent: 'hex', accentBg: 'str',
  success: 'hex', warning: 'hex', danger: 'hex', successBg: 'hex', warningBg: 'hex', dangerBg: 'hex',
  hero: 'str', onHero: 'hex',
  radiusSm: 'str', radiusMd: 'str', radiusLg: 'str', radiusBtn: 'str',
  shadow: 'str', font: 'str', mono: 'str',
  glass: 'str', glassLowEnd: 'hex', blur: 'str'
}

const isStr = (v) => typeof v === 'string' && v.trim() !== ''

/** 返回错误字符串数组（空 = 合规）；每条形如 `themes/<file>:<字段路径>: <原因>`（AC-080-03） */
export function validateTheme(def, file) {
  const errors = []
  const err = (path, reason) => errors.push(`themes/${file}:${path}: ${reason}`)
  if (!def || typeof def !== 'object' || Array.isArray(def)) {
    err('$', '定义必须是 JSON 对象')
    return errors
  }
  if (def.schemaVersion !== 1) err('schemaVersion', '必须为 1')
  if (!isStr(def.key) || !KEY_RE.test(def.key)) err('key', `格式须匹配 ${KEY_RE}`)
  else if (`${def.key}.theme.json` !== file) err('key', `与文件名 ${file} 不一致`)
  if (!isStr(def.name) || def.name.length > 12) err('name', '显示名须为 1~12 字符')
  if (!Number.isInteger(def.order)) err('order', '必须为整数')
  if (def.scheme !== 'dark' && def.scheme !== 'light') err('scheme', "必须为 'dark' 或 'light'")
  if (!Array.isArray(def.swatch) || def.swatch.length !== 3 || !def.swatch.every((c) => HEX_RE.test(c ?? ''))) {
    err('swatch', '必须是 3 个 #RRGGBB 颜色')
  }
  const tokens = def.tokens
  if (!tokens || typeof tokens !== 'object') {
    err('tokens', '缺少 tokens')
  } else {
    for (const [name, kind] of Object.entries(TOKEN_SPEC)) {
      if (!(name in tokens)) err(`tokens.${name}`, '缺少必填项')
      else if (kind === 'hex' && !HEX_RE.test(tokens[name] ?? '')) err(`tokens.${name}`, '必须是 #RRGGBB')
      else if (kind === 'str' && !isStr(tokens[name])) err(`tokens.${name}`, '必须是非空字符串')
    }
    if (tokens.decor !== '0' && tokens.decor !== '1') err('tokens.decor', "必须为 '0' 或 '1'")
  }
  const nat = def.native
  const hexIn = (obj, k, path) => { if (!HEX_RE.test(obj?.[k] ?? '')) err(`${path}.${k}`, '必须是 #RRGGBB') }
  if (!nat || typeof nat !== 'object') {
    err('native', '缺少 native')
  } else {
    for (const k of ['color', 'selectedColor', 'backgroundColor']) hexIn(nat.tabBar, k, 'native.tabBar')
    if (nat.tabBar?.borderStyle !== 'black' && nat.tabBar?.borderStyle !== 'white') {
      err('native.tabBar.borderStyle', "必须为 'black' 或 'white'")
    }
    hexIn(nat.navBar, 'backgroundColor', 'native.navBar')
    if (nat.navBar?.frontColor !== '#ffffff' && nat.navBar?.frontColor !== '#000000') {
      err('native.navBar.frontColor', "必须为 '#ffffff' 或 '#000000'")
    }
    hexIn(nat, 'windowBackground', 'native')
  }
  if (!Array.isArray(def.contrast) || def.contrast.length === 0) {
    err('contrast', '至少声明 1 个对比度组合')
  } else if (tokens && typeof tokens === 'object') {
    def.contrast.forEach((c, i) => {
      const path = `contrast[${i}]`
      const fg = tokens[c?.fg] ?? c?.fg
      if (!HEX_RE.test(fg ?? '')) return err(`${path}.fg`, '必须是 token 名（取值为 #RRGGBB）或 #RRGGBB')
      if (!HEX_RE.test(c?.bg ?? '')) return err(`${path}.bg`, '必须是等效不透明背景 #RRGGBB')
      if (typeof c.min !== 'number' || c.min < 4.5) return err(`${path}.min`, '必须是数字且不低于 4.5')
      if (!isStr(c.label)) return err(`${path}.label`, '缺少 label')
      const ratio = contrastRatio(fg, c.bg)
      if (ratio + 1e-9 < c.min) err(path, `${c.label}：对比度 ${ratio.toFixed(2)} 低于 ${c.min}`)
    })
  }
  return errors
}

export function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

export function rgbToHex([r, g, b]) {
  return '#' + [r, g, b].map((v) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, '0')).join('').toUpperCase()
}

/** 按 weight 把 a 向 b 混合：weight=0 → a，weight=1 → b */
export function mix(a, b, weight) {
  const [ra, rb] = [hexToRgb(a), hexToRgb(b)]
  return rgbToHex(ra.map((v, i) => v * (1 - weight) + rb[i] * weight))
}

function luminance(hex) {
  const [r, g, b] = hexToRgb(hex).map((v) => {
    const s = v / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** WCAG 2.1 对比度 (L1+0.05)/(L2+0.05) */
export function contrastRatio(fg, bg) {
  const [l1, l2] = [luminance(fg), luminance(bg)].sort((x, y) => y - x)
  return (l1 + 0.05) / (l2 + 0.05)
}
