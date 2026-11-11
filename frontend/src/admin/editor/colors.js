// MOD-059 / IFC-241：颜色归一化，规则与服务端 normalize_color（IFC-169）完全一致，共享同一组测试向量
const HEX_RE = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/
const RGB_RE = /^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*(\d(?:\.\d+)?|\.\d+)\s*)?\)$/

// 取色器预设色板（颜色字面量不得出现在 .vue 文件中，ADR-029）
export const COLOR_PALETTE = ['#000000', '#333333', '#666666', '#999999', '#d0021b', '#f5a623',
  '#f8e71c', '#7ed321', '#1a73e8', '#4a90e2', '#9013fe', '#ffffff']

function hex2(value) {
  return value.toString(16).padStart(2, '0')
}

/** #rgb/#rrggbb/#rrggbbaa 原样返回；rgb()/rgba()（逗号形式）转 #rrggbb[aa]；其余返回 null。 */
export function toHexColor(input) {
  if (typeof input !== 'string') return null
  if (HEX_RE.test(input)) return input
  const match = RGB_RE.exec(input)
  if (!match) return null
  const channels = [match[1], match[2], match[3]].map(Number)
  if (channels.some((c) => c > 255)) return null
  let out = `#${channels.map(hex2).join('')}`
  if (match[4] !== undefined) {
    const alpha = Number(match[4])
    if (alpha > 1) return null
    // 四舍五入取半向上，与后端 floor(a*255+0.5) 一致
    if (alpha < 1) out += hex2(Math.floor(alpha * 255 + 0.5))
  }
  return out
}
