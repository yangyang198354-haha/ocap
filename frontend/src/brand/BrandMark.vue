<!-- MOD-119 / IFC-328：品牌标识（圆角方块 + 枫叶 + @ 形电路环），纯 SVG，颜色只用语义变量与 currentColor -->
<template>
  <svg class="brand-mark" :width="size" :height="size" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
    <rect class="brand-mark-frame" x="1.5" y="1.5" width="29" height="29" rx="8" />
    <circle class="brand-mark-ring" cx="16" cy="16" r="11.5" />
    <path
      class="brand-mark-leaf"
      d="M16 5.5 L18.1 10.6 L22.8 9.4 L20.9 14 L25.5 16.2 L20.6 17.9 L21.1 22.4 L16.9 20.4 L16 26.5 L15.1 20.4 L10.9 22.4 L11.4 17.9 L6.5 16.2 L11.1 14 L9.2 9.4 L13.9 10.6 Z"
    />
  </svg>
</template>

<script setup>
defineProps({ size: { type: Number, default: 32 } })
</script>

<style scoped>
.brand-mark { flex: none; color: var(--accent-text); }
.brand-mark-frame { fill: none; stroke: var(--accent); stroke-width: 2; }
.brand-mark-ring { fill: none; stroke: var(--accent-2); stroke-width: 1; stroke-dasharray: 3 2.5; }
.brand-mark-leaf { fill: currentColor; }
</style>
