export function money(value) {
  if (value === null || value === undefined || value === '') return ''
  return String(value)
}

// 两位小数展示；无法转数字时原样返回
export function moneyText(value) {
  if (value === null || value === undefined || value === '') return ''
  const n = Number(value)
  return Number.isNaN(n) ? String(value) : n.toFixed(2)
}

export function datetime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 19)
}

export function formatDateTime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16)
}

export function identityLabel(item) {
  return item?.identity || item?.identity_label || ''
}

export function errorText(err) {
  if (!err) return ''
  return err.details?.retry_after ? `${err.message}（${err.details.retry_after} 秒后重试）` : err.message
}
