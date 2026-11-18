// MOD-147 / IFC-364：专有部分下拉检索排序——前缀匹配在前（原序），其余包含匹配在后（原序），不匹配不显示；
// query 为空返回原序全部；大小写不敏感，匹配文本取 option.value，并同时匹配 label 中"（"之前的名称部分
// （户号级 label 形如"552（住宅 89 ㎡）"，括号内的类型与面积不参与匹配，避免面积数字造成误命中）
export function rankOptions(options, query) {
  const list = Array.isArray(options) ? options : []
  const q = String(query ?? '').trim().toLowerCase()
  if (!q) return list
  const prefix = []
  const contains = []
  for (const option of list) {
    const value = String(option?.value ?? '').toLowerCase()
    const name = String(option?.label ?? '').split('（')[0].toLowerCase()
    if (value.startsWith(q)) prefix.push(option)
    else if (value.includes(q) || name.includes(q)) contains.push(option)
  }
  return [...prefix, ...contains]
}
