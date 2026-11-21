// MOD-082 / IFC-279：列表翻页组合函数；兼容"数组"与"{count, results}"两种返回
import { ref, unref } from 'vue'

export function usePaging(opts) {
  const pageSize = ref(Math.min(Math.max(Number(opts.pageSize) || 20, 1), 100))
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const filters = unref(opts.filters) || {}
      const data = await opts.fetch({ ...filters, page: page.value, page_size: pageSize.value })
      if (Array.isArray(data)) {
        items.value = data
        total.value = data.length
      } else {
        items.value = data?.results || []
        total.value = data?.count ?? items.value.length
      }
    } finally {
      loading.value = false
    }
  }

  const reload = () => load()
  const goto = (n) => {
    page.value = n
    return load()
  }
  const resetAndLoad = () => {
    page.value = 1
    return load()
  }
  // REQ-FUNC-283：切换每页条数后回到第 1 页重新加载
  const setPageSize = (n) => {
    pageSize.value = Math.min(Math.max(Number(n) || 20, 1), 100)
    return resetAndLoad()
  }

  return { items, total, page, pageSize, loading, reload, goto, resetAndLoad, setPageSize }
}
