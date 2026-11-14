// MOD-084：版式模板编辑项的默认值与范围（沿用后端 TOKEN_RULES，B/content/styles.py；颜色字面量不得出现在 .vue 中，ADR-029）
export const DEFAULT_TOKENS = {
  font_family_key: 'sans',
  font_size: 16,
  line_height: 1.8,
  paragraph_spacing: 14,
  page_chars: 2000,
  text_color: '#222222',
  heading_color: '#000000',
  link_color: '#0f4c81',
  quote_border_color: '#9ca3af',
  accent_color: '#0f4c81'
}

export const NUMERIC_FIELDS = [
  { key: 'font_size', label: '字号', min: 12, max: 24, step: 1 },
  { key: 'line_height', label: '行高', min: 1.2, max: 2.4, step: 0.1 },
  { key: 'paragraph_spacing', label: '段间距', min: 0, max: 32, step: 1 },
  { key: 'page_chars', label: '每页字数', min: 200, max: 20000, step: 100 }
]

export const COLOR_FIELDS = [
  { key: 'text_color', label: '正文色' },
  { key: 'heading_color', label: '标题色' },
  { key: 'link_color', label: '链接色' },
  { key: 'quote_border_color', label: '引用边框色' },
  { key: 'accent_color', label: '强调色' }
]

export const FONT_OPTIONS = [
  { value: 'sans', label: '无衬线' },
  { value: 'serif', label: '衬线' }
]

export function mergeTokens(tokens) {
  return { ...DEFAULT_TOKENS, ...(tokens || {}) }
}
