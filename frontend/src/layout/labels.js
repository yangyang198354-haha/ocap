// MOD-120 / IFC-330：显示名截断，按 Unicode 码点计数（昵称/账号名过长时加省略号）。
export function truncateLabel(text, max = 12) {
  if (typeof text !== 'string' || !text) return ''
  const chars = [...text]
  return chars.length > max ? `${chars.slice(0, max).join('')}…` : text
}
