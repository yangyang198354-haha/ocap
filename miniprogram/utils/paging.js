// MOD-085 / IFC-284：“加载更多”分页；兼容“数组”与“{count, results}”两种返回
import { computed, ref } from 'vue'

export function usePaging(opts) {
  const pageSize = Math.min(Math.max(Number(opts.pageSize) || 20, 1), 100)
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  let page = 0

  const hasMore = computed(() => items.value.length < total.value)

  async function fetchPage(next) {
    loading.value = true
    try {
      const data = await opts.fetch({ page: next, page_size: pageSize })
      const rows = Array.isArray(data) ? data : data?.results || []
      return { rows, count: Array.isArray(data) ? rows.length : data?.count ?? rows.length, array: Array.isArray(data) }
    } finally {
      loading.value = false
    }
  }

  async function reset() {
    page = 1
    const { rows, count } = await fetchPage(1)
    items.value = rows
    total.value = count
  }

  async function loadMore() {
    if (loading.value) return
    if (page === 0) return reset()
    if (!hasMore.value) return
    const { rows, count, array } = await fetchPage(page + 1)
    if (array) {
      // 旧接口整体返回：不再追加，避免重复
      total.value = items.value.length
      return
    }
    page += 1
    const seen = new Set(items.value.map((x) => x.id))
    items.value = [...items.value, ...rows.filter((x) => !seen.has(x.id))]
    total.value = count
  }

  return { items, total, hasMore, loading, loadMore, reset }
}
