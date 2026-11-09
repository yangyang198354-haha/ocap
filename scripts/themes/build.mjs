// MOD-024 / IFC-145：读取 themes/*.theme.json，校验并生成 Web 与小程序产物。
// 用法：node scripts/themes/build.mjs [--strict] [--check] [--themes-dir=DIR] [--root=DIR]
// 仅使用 node:fs / node:path / node:url，无第三方依赖。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { KEY_RE, mix, validateTheme } from './schema.mjs'

export const DEFAULT_THEME = 'bento'
const GENERATED_NOTE = '由 scripts/themes/build.mjs 生成，请勿手改；修改 themes/ 后重新运行。'

const VAR_NAMES = {
  bg: '--bg', surface: '--surface', overlay: '--overlay', text: '--text', muted: '--muted', line: '--line',
  accent: '--accent', accent2: '--accent-2', accentText: '--accent-text', onAccent: '--on-accent',
  accentBg: '--accent-bg', success: '--success', warning: '--warning', danger: '--danger',
  successBg: '--success-bg', warningBg: '--warning-bg', dangerBg: '--danger-bg',
  hero: '--hero', onHero: '--on-hero', radiusSm: '--radius-sm', radiusMd: '--radius-md', radiusLg: '--radius-lg',
  radiusBtn: '--radius-btn', shadow: '--shadow', font: '--font', mono: '--mono',
  glass: '--glass', glassLowEnd: '--glass-low-end', blur: '--blur', decor: '--decor'
}

/** 业务语义变量（Web 与小程序同名） */
export function businessVars(def) {
  const out = {}
  for (const [name, cssVar] of Object.entries(VAR_NAMES)) out[cssVar] = def.tokens[name]
  return out
}

function elScale(name, color, base, dark) {
  const out = { [`--el-color-${name}`]: color }
  for (const n of [3, 5, 7, 8, 9]) out[`--el-color-${name}-light-${n}`] = mix(color, base, n / 10)
  out[`--el-color-${name}-dark-2`] = mix(color, dark ? '#FFFFFF' : '#000000', 0.2)
  return out
}

/** Element Plus 变量映射（ADR-026）；梯度由混色计算，不依赖 color-mix */
export function elementVars(def) {
  const t = def.tokens
  const dark = def.scheme === 'dark'
  const base = dark ? t.bg : '#FFFFFF'
  const fill = (w) => mix(t.overlay, t.text, w)
  const rgbaOf = (hex, a) => {
    const n = parseInt(hex.slice(1), 16)
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`
  }
  return {
    ...elScale('primary', t.accent, base, dark),
    ...elScale('success', t.success, base, dark),
    ...elScale('warning', t.warning, base, dark),
    ...elScale('danger', t.danger, base, dark),
    ...elScale('error', t.danger, base, dark),
    ...elScale('info', t.muted, base, dark),
    '--el-bg-color': t.overlay,
    '--el-bg-color-page': t.bg,
    '--el-bg-color-overlay': t.overlay,
    '--el-text-color-primary': t.text,
    '--el-text-color-regular': t.text,
    '--el-text-color-secondary': t.muted,
    '--el-text-color-placeholder': t.muted,
    '--el-text-color-disabled': mix(t.muted, t.bg, 0.5),
    '--el-border-color': t.line,
    '--el-border-color-light': t.line,
    '--el-border-color-lighter': t.line,
    '--el-border-color-extra-light': t.line,
    '--el-border-color-dark': mix(t.bg, t.text, 0.25),
    '--el-border-color-darker': mix(t.bg, t.text, 0.4),
    '--el-border-color-hover': mix(t.bg, t.text, 0.3),
    '--el-fill-color': fill(0.08),
    '--el-fill-color-light': fill(0.05),
    '--el-fill-color-lighter': fill(0.03),
    '--el-fill-color-extra-light': fill(0.02),
    '--el-fill-color-dark': fill(0.12),
    '--el-fill-color-darker': fill(0.16),
    '--el-fill-color-blank': t.surface,
    '--el-mask-color': rgbaOf(t.bg, 0.8),
    '--el-mask-color-extra-light': rgbaOf(t.bg, 0.3),
    '--el-border-radius-base': t.radiusSm,
    '--el-border-radius-small': t.radiusSm,
    '--el-font-family': t.font,
    '--el-box-shadow': t.shadow,
    '--el-box-shadow-light': t.shadow,
    '--el-box-shadow-dark': t.shadow
  }
}

const decl = (vars, indent = '  ') => Object.entries(vars).map(([k, v]) => `${indent}${k}: ${v};`).join('\n')

function primaryButtonRule(def, selector) {
  const t = def.tokens
  const grad = t.accentBg.startsWith('linear-gradient')
  const bg = grad ? 'transparent' : t.accentBg
  const lines = [
    `--el-button-text-color: ${t.onAccent}`, `--el-button-hover-text-color: ${t.onAccent}`,
    `--el-button-active-text-color: ${t.onAccent}`,
    `--el-button-bg-color: ${bg}`, `--el-button-hover-bg-color: ${bg}`, `--el-button-active-bg-color: ${bg}`,
    `--el-button-border-color: ${bg}`, `--el-button-hover-border-color: ${bg}`, `--el-button-active-border-color: ${bg}`,
    `border-radius: var(--radius-btn)`
  ]
  if (grad) lines.push(`background-image: ${t.accentBg}`)
  return `${selector} .el-button--primary {\n${lines.map((l) => `  ${l};`).join('\n')}\n}\n` +
    `${selector} .el-button--primary:hover { filter: brightness(1.08); }`
}

export function loadThemeFiles(dir) {
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith('.theme.json')).sort() : []
  return files.map((file) => {
    const text = fs.readFileSync(path.join(dir, file), 'utf8')
    let def = null
    let errors = []
    try {
      def = JSON.parse(text)
      errors = validateTheme(def, file)
    } catch (e) {
      errors = [`themes/${file}:$: JSON 解析失败：${e.message}`]
    }
    const base = file.replace(/\.theme\.json$/, '')
    const read = (ext) => {
      const p = path.join(dir, `${base}.${ext}`)
      return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''
    }
    return { file, def, errors, webCss: read('web.css'), mpCss: read('mp.css') }
  })
}

/** 校验可选样式片段：每个顶层选择器必须以 prefixes 之一开头（@keyframes 内部不检查） */
export function checkScopedCss(css, prefixes, label) {
  const errors = []
  const src = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const walk = (text, inMedia) => {
    let i = 0
    while (i < text.length) {
      const open = text.indexOf('{', i)
      if (open < 0) break
      const prelude = text.slice(i, open).trim()
      let depth = 1
      let j = open + 1
      while (j < text.length && depth > 0) {
        if (text[j] === '{') depth++
        else if (text[j] === '}') depth--
        j++
      }
      const body = text.slice(open + 1, j - 1)
      if (prelude.startsWith('@media')) walk(body, true)
      else if (!prelude.startsWith('@')) {
        for (const sel of prelude.split(',').map((s) => s.trim()).filter(Boolean)) {
          if (!prefixes.some((p) => sel.startsWith(p))) errors.push(`${label}: 选择器 "${sel}" 未以 ${prefixes.join(' 或 ')} 开头`)
        }
      }
      i = j
    }
  }
  walk(src, false)
  return errors
}

const REDUCED_MOTION = `@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
  .theme-decor { display: none !important; }
}`

/** 由合规风格列表生成全部产物，返回 { 相对路径: 内容 } */
export function generate(entries) {
  const valid = entries.filter((e) => e.errors.length === 0).sort((a, b) => a.def.order - b.def.order || a.def.key.localeCompare(b.def.key))
  const bento = valid.find((e) => e.def.key === DEFAULT_THEME)
  if (!bento) throw new Error(`默认风格 ${DEFAULT_THEME} 缺失或不合规`)

  const css = [`/* ${GENERATED_NOTE} */`]
  css.push(`:root {\n  color-scheme: light;\n${decl({ ...businessVars(bento.def), ...elementVars(bento.def) })}\n}`)
  for (const { def, webCss } of valid) {
    const sel = `html[data-theme="${def.key}"]`
    css.push(`${sel} {\n  color-scheme: ${def.scheme};\n${decl({ ...businessVars(def), ...elementVars(def) })}\n}`)
    css.push(primaryButtonRule(def, sel))
    if (webCss.trim()) css.push(`/* themes/${def.key}.web.css */\n${webCss.trim()}`)
  }
  css.push('/* 低端设备降级（ADR-032）：玻璃模糊换为不透明纯色 */')
  css.push('html[data-perf="low"] {\n  --blur: none;\n  --surface: var(--glass-low-end);\n  --glass: var(--glass-low-end);\n}')
  css.push(REDUCED_MOTION)

  const meta = (def) => ({ key: def.key, name: def.name, order: def.order, scheme: def.scheme, swatch: def.swatch })
  const webRegistry = `// ${GENERATED_NOTE}\nexport const THEMES = ${JSON.stringify(valid.map((e) => meta(e.def)), null, 2)}\nexport const DEFAULT_THEME = '${DEFAULT_THEME}'\n`
  const mpThemes = valid.map((e) => ({ ...meta(e.def), tokens: businessVars(e.def), native: e.def.native }))
  const mpRegistry = `// ${GENERATED_NOTE}\nexport const THEMES = ${JSON.stringify(mpThemes, null, 2)}\nexport const DEFAULT_THEME = '${DEFAULT_THEME}'\n`
  const scss = [`/* ${GENERATED_NOTE} */`, `page {\n${decl(businessVars(bento.def))}\n}`]
  for (const { def, mpCss } of valid) if (mpCss.trim()) scss.push(`/* themes/${def.key}.mp.css */\n${mpCss.trim()}`)

  return {
    'frontend/src/theme/generated/themes.css': css.join('\n\n') + '\n',
    'frontend/src/theme/generated/registry.js': webRegistry,
    'miniprogram/theme/generated/registry.js': mpRegistry,
    'miniprogram/theme/generated/themes.scss': scss.join('\n\n') + '\n'
  }
}

/** 校验 + 生成；返回 { outputs, errors(含定位信息的字符串), fatal } */
export function run(themesDir) {
  const entries = loadThemeFiles(themesDir)
  const errors = []
  const seen = new Map()
  for (const e of entries) {
    errors.push(...e.errors)
    if (e.errors.length === 0) {
      if (seen.has(e.def.key)) e.errors.push(`themes/${e.file}:key: 与 ${seen.get(e.def.key)} 重复`)
      else seen.set(e.def.key, e.file)
      errors.push(...e.errors.filter((m) => m.includes(':key: 与')))
      const k = e.def.key
      if (KEY_RE.test(k)) {
        const w = checkScopedCss(e.webCss, [`[data-theme="${k}"]`, `html[data-theme="${k}"]`], `themes/${k}.web.css`)
        const m = checkScopedCss(e.mpCss, [`.theme-${k}`], `themes/${k}.mp.css`)
        if (w.length || m.length) { e.errors.push(...w, ...m); errors.push(...w, ...m) }
      }
    }
  }
  let outputs = null
  let fatal = null
  try { outputs = generate(entries) } catch (err) { fatal = err.message }
  return { outputs, errors, fatal }
}

function main(argv) {
  const flag = (n) => argv.includes(n)
  const opt = (n) => argv.find((a) => a.startsWith(`--${n}=`))?.slice(n.length + 3)
  const root = opt('root') ? path.resolve(opt('root')) : path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
  const themesDir = opt('themes-dir') ? path.resolve(opt('themes-dir')) : path.join(root, 'themes')
  const { outputs, errors, fatal } = run(themesDir)
  for (const e of errors) console.error(e)
  if (fatal) { console.error(fatal); return 1 }
  let drift = 0
  for (const [rel, content] of Object.entries(outputs)) {
    const target = path.join(root, rel)
    const current = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : null
    if (flag('--check')) {
      if (current !== content) { console.error(`生成物与风格定义不一致：${rel}`); drift++ }
    } else if (current !== content) {
      fs.mkdirSync(path.dirname(target), { recursive: true })
      fs.writeFileSync(target, content)
      console.log(`wrote ${rel}`)
    }
  }
  if (flag('--check')) return drift ? 1 : (flag('--strict') && errors.length ? 1 : 0)
  return flag('--strict') && errors.length ? 1 : 0
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = main(process.argv.slice(2))
}
