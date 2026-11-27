// Only cache layout hints; balances and entries always come from the API.
const KEY = 'ocap_account_count_v1'
const TTL = 5 * 60 * 1000

export function readAccountCount() {
  try {
    const cached = JSON.parse(localStorage.getItem(KEY))
    const age = Date.now() - cached?.savedAt
    if (Number.isInteger(cached?.count) && cached.count >= 0 && cached.count <= 100 && age >= 0 && age < TTL) return cached.count
  } catch { /* Storage may be unavailable or malformed. */ }
  return null
}

export function writeAccountCount(count) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ count, savedAt: Date.now() }))
  } catch { /* Loading works without storage. */ }
}
