<template>
  <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path :d="PATHS[name] || PATHS.doc" />
  </svg>
</template>

<script setup>
// 语义图标（描边，颜色取 currentColor）；页面只写图标名，不写风格相关代码
defineProps({ name: { type: String, default: 'doc' } })

const PATHS = {
  home: 'M3 11l9-8 9 8M5 10v10h14V10',
  doc: 'M6 3h9l4 4v14H6zM14 3v5h5M9 13h6M9 17h6',
  vote: 'M4 20V10M10 20V4M16 20v-8M22 20H2',
  wallet: 'M4 7h16v12H4zM4 7l2-3h12l2 3M12 11v4M10 13h4',
  user: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0',
  key: 'M8 15a4 4 0 100-8 4 4 0 000 8zM11 12l9-9M17 6l3 3M15 8l2 2',
  chart: 'M3 3v18h18M7 14l4-4 3 3 6-6',
  check: 'M5 12l5 5L20 7',
  task: 'M9 11l3 3 8-8M20 12v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1h9',
  receipt: 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6',
  coin: 'M12 21a9 9 0 100-18 9 9 0 000 18zM9 8l3 4 3-4M8.5 13h7M12 12v6',
  income: 'M3 17l6-6 4 4 8-8M15 7h6v6',
  upload: 'M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3',
  clip: 'M21 11l-8.5 8.5a5 5 0 01-7-7L14 4a3.5 3.5 0 015 5l-8.5 8.5a2 2 0 01-3-3L15 7',
  close: 'M6 6l12 12M18 6L6 18'
}
defineOptions({ name: 'UiIcon' })
</script>
